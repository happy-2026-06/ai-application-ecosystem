import apiClient from './client'

export interface Session {
  id: string
  title: string | null
  session_type: string
  status: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  citations: Citation[] | null
  token_count: number | null
  feedback: string | null
  created_at: string
}

export interface Citation {
  index: number
  doc_name: string
  doc_id: string | null
  content_snippet: string
  score: number | null
}

export interface SSEEvent {
  type: 'thinking' | 'retrieving' | 'token' | 'sources' | 'done' | 'error'
  content?: string
  data?: any
}

export const chatApi = {
  // Sessions
  listSessions(page = 1, pageSize = 20) {
    return apiClient.get<Session[]>('/chat/sessions', {
      params: { page, page_size: pageSize },
    })
  },
  createSession(title?: string) {
    return apiClient.post<Session>('/chat/sessions', { title })
  },
  getSession(sessionId: string) {
    return apiClient.get<Session>(`/chat/sessions/${sessionId}`)
  },
  deleteSession(sessionId: string) {
    return apiClient.delete(`/chat/sessions/${sessionId}`)
  },
  renameSession(sessionId: string, title: string) {
    return apiClient.patch(`/chat/sessions/${sessionId}`, { title })
  },

  // Messages
  getMessages(sessionId: string, page = 1, pageSize = 50) {
    return apiClient.get<Message[]>(`/chat/sessions/${sessionId}/messages`, {
      params: { page, page_size: pageSize },
    })
  },

  // Streaming chat via SSE
  askQuestion(sessionId: string, question: string, token: string): Promise<Response> {
    return fetch(`/api/chat/ask?session_id=${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ question }),
    })
  },

  // Feedback
  submitFeedback(messageId: string, rating: 'positive' | 'negative', comment?: string) {
    return apiClient.post('/chat/feedback', {
      message_id: messageId,
      rating,
      comment,
    })
  },
}
