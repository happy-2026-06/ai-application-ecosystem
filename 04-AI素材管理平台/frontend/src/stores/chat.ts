import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi, type Session, type Message, type Citation, type SSEEvent } from '../api/chat'
import { useAuthStore } from './auth'

function generateId(): string {
  return crypto.randomUUID?.() || `temp-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

const SSE_READ_TIMEOUT_MS = 120_000   // 2 min max for the whole stream
const MAX_RETRIES = 2                  // max reconnect attempts

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<Session[]>([])
  const currentSession = ref<Session | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const streamingContent = ref('')
  const currentCitations = ref<Citation[]>([])
  let activeAbortController: AbortController | null = null

  // ── Session management ──────────────────────────────────────────

  async function loadSessions() {
    try {
      const res = await chatApi.listSessions()
      sessions.value = res.data
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  }

  async function createSession(): Promise<Session | null> {
    try {
      const res = await chatApi.createSession()
      sessions.value.unshift(res.data)
      return res.data
    } catch (err) {
      console.error('Failed to create session:', err)
      return null
    }
  }

  async function deleteSession(sessionId: string) {
    try {
      await chatApi.deleteSession(sessionId)
      sessions.value = sessions.value.filter((s) => s.id !== sessionId)
      if (currentSession.value?.id === sessionId) {
        currentSession.value = null
        messages.value = []
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  async function renameSession(sessionId: string, title: string) {
    try {
      await chatApi.renameSession(sessionId, title)
      const session = sessions.value.find((s) => s.id === sessionId)
      if (session) session.title = title
      if (currentSession.value?.id === sessionId) {
        currentSession.value.title = title
      }
    } catch (err) {
      console.error('Failed to rename session:', err)
    }
  }

  // ── Messages ────────────────────────────────────────────────────

  async function loadMessages(sessionId: string) {
    try {
      const res = await chatApi.getMessages(sessionId)
      messages.value = res.data
    } catch (err) {
      console.error('Failed to load messages:', err)
    }
  }

  // ── Streaming chat with timeout + reconnect ─────────────────────

  function cancelActiveStream() {
    if (activeAbortController) {
      activeAbortController.abort()
      activeAbortController = null
    }
  }

  /**
   * Read the SSE stream line by line with a global timeout.
   * Returns a cleaned-up body text on success, or throws on timeout / abort.
   */
  async function readSSEStream(
    response: Response,
    assistantMsg: Message,
    signal: AbortSignal,
  ): Promise<void> {
    const reader = response.body?.getReader()
    if (!reader) throw new Error('Response body is not readable')

    const decoder = new TextDecoder()
    let buffer = ''
    let lastDataTime = Date.now()

    // Race the read loop against the global timeout
    const timeoutPromise = sleep(SSE_READ_TIMEOUT_MS).then(() => {
      throw new Error('SSE_READ_TIMEOUT')
    })

    const readPromise = (async () => {
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          if (signal.aborted) { reader.cancel(); break }

          lastDataTime = Date.now()
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const data = line.slice(6)
            if (data === '[DONE]') continue

            try {
              const event: SSEEvent = JSON.parse(data)
              handleSSEEvent(event, assistantMsg)
            } catch {
              // Malformed SSE chunk — skip
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
    })()

    await Promise.race([readPromise, timeoutPromise])
  }

  async function sendMessage(sessionId: string, question: string, retryCount = 0) {
    const authStore = useAuthStore()

    // Cancel any in-progress stream before starting a new one
    cancelActiveStream()

    // Add user message immediately
    const userMsg: Message = {
      id: generateId(),
      session_id: sessionId,
      role: 'user',
      content: question,
      citations: null,
      token_count: null,
      feedback: null,
      created_at: new Date().toISOString(),
    }
    messages.value.push(userMsg)

    // Add placeholder assistant message
    const assistantMsg: Message = {
      id: generateId(),
      session_id: sessionId,
      role: 'assistant',
      content: '',
      citations: null,
      token_count: null,
      feedback: null,
      created_at: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)

    isLoading.value = true
    streamingContent.value = ''
    currentCitations.value = []

    activeAbortController = new AbortController()

    try {
      const response = await chatApi.askQuestion(sessionId, question, authStore.token)
      if (!response.ok) {
        if (response.status === 401 && retryCount < MAX_RETRIES) {
          // Token may have expired — refresh and retry once
          console.warn('[sendMessage] 401 received, retrying after token refresh…')
          await authStore.updateProfile('')  // trigger token refresh path
          return sendMessage(sessionId, question, retryCount + 1)
        }
        throw new Error(`HTTP ${response.status}`)
      }

      await readSSEStream(response, assistantMsg, activeAbortController.signal)
    } catch (error) {
      const err = error as Error
      if (err.name === 'AbortError') {
        // User intentionally cancelled — keep partial content
        if (!assistantMsg.content) {
          assistantMsg.content = '（已取消）'
        }
      } else if (err.message === 'SSE_READ_TIMEOUT') {
        console.error('[sendMessage] SSE stream timed out')
        if (!assistantMsg.content) {
          assistantMsg.content = '抱歉，响应超时，请重试。'
        }
      } else if (retryCount < MAX_RETRIES) {
        // Network error — retry with exponential backoff
        console.warn(`[sendMessage] Retry ${retryCount + 1}/${MAX_RETRIES} after error:`, err.message)
        // Remove placeholder, will re-add
        messages.value = messages.value.filter(m => m.id !== assistantMsg.id)
        await sleep(1000 * (retryCount + 1))  // 1s, 2s backoff
        return sendMessage(sessionId, question, retryCount + 1)
      } else {
        console.error('[sendMessage] All retries exhausted:', err.message)
        if (!assistantMsg.content) {
          assistantMsg.content = '抱歉，请求失败，请检查网络后重试。'
        }
      }
    } finally {
      isLoading.value = false
      activeAbortController = null
      await loadSessions()
    }
  }

  function handleSSEEvent(event: SSEEvent, msg: Message) {
    switch (event.type) {
      case 'token':
        streamingContent.value += event.content || ''
        msg.content = streamingContent.value
        break
      case 'sources':
        currentCitations.value = event.data || []
        msg.citations = currentCitations.value
        break
      case 'done':
        msg.id = event.data?.message_id || msg.id
        msg.content = event.data?.full_answer || msg.content
        msg.citations = event.data?.sources || msg.citations
        break
      case 'error':
        msg.content = event.content || '处理出错'
        console.error('[SSE] Server error:', event.content)
        break
    }
  }

  return {
    sessions, currentSession, messages,
    isLoading, streamingContent, currentCitations,
    loadSessions, createSession, deleteSession, renameSession,
    loadMessages, sendMessage, cancelActiveStream,
  }
})
