<template>
  <div class="chat-page">
    <!-- Empty state -->
    <div v-if="!currentId" class="chat-welcome">
      <div class="welcome-icon">🤖</div>
      <h1>智能客服助手</h1>
      <p>企业级 AI 知识库问答 — 上传产品资料，AI 精准回答</p>
      <div class="quick-cards">
        <div class="quick-card" @click="quickStart('介绍一下知识库中有哪些产品文档？')">📦 查看产品</div>
        <div class="quick-card" @click="quickStart('帮我推荐一款性价比高的产品')">💡 智能推荐</div>
        <div class="quick-card" @click="quickStart('如何对比不同产品的参数？')">📊 产品对比</div>
      </div>
    </div>

    <!-- Active chat -->
    <template v-else>
      <div class="chat-topbar">
        <h3>{{ chatStore.currentSession?.title || '新对话' }}</h3>
        <div style="display:flex;align-items:center;gap:8px">
          <n-select v-model:value="selectedModel" :options="modelOptions" size="tiny" placeholder="🤖 默认模型" style="width:160px" @update:value="onModelChange"/>
          <n-button text size="small" @click="exportChat">📥 导出</n-button>
        </div>
      </div>

      <div class="msg-scroll" ref="msgContainer">
        <div class="msg-inner">
          <div v-for="msg in chatStore.messages" :key="msg.id" class="msg-row" :class="{ me: msg.role === 'user' }">
            <div class="msg-avatar-area">
              <span v-if="msg.role === 'user'" class="u-avatar">{{ authStore.avatar }}</span>
              <span v-else class="ai-avatar">AI</span>
            </div>
            <div class="msg-body">
              <div class="msg-meta">
                <span class="msg-role">{{ msg.role === 'user' ? '我' : 'AI 助手' }}</span>
                <span class="msg-time">{{ fmtTime(msg.created_at) }}</span>
              </div>
              <div
                class="msg-text"
                :class="{ 'msg-me': msg.role === 'user' }"
                v-html="msg.role === 'assistant' ? renderMd(msg.content) : escapeHtml(msg.content)"
              />
              <div v-if="msg.citations?.length" class="msg-cite">
                <n-collapse>
                  <n-collapse-item :title="`📚 ${msg.citations.length} 条参考来源`">
                    <div v-for="c in msg.citations" :key="c.index" class="cite-line">
                      <span class="cite-tag">[{{ c.index }}]</span>
                      <strong>{{ c.doc_name }}</strong>
                      <p>{{ c.content_snippet }}</p>
                    </div>
                  </n-collapse-item>
                </n-collapse>
              </div>
              <div class="msg-acts">
                <n-button text size="tiny" @click="copyMsg(msg.content)">📋 复制</n-button>
                <template v-if="msg.role === 'user'">
                  <n-button text size="tiny" @click="startEdit(msg)" v-if="editingId !== msg.id">✏️ 编辑</n-button>
                  <n-popconfirm @positive-click="deleteMsg(msg.id)">
                    <template #trigger><n-button text size="tiny">🗑 删除</n-button></template>
                    删除？
                  </n-popconfirm>
                </template>
              </div>
              <!-- Inline editor -->
              <div v-if="editingId === msg.id" class="edit-area">
                <n-input v-model:value="editText" type="textarea" :autosize="{minRows:1,maxRows:4}" @keydown.enter.exact.prevent="submitEdit(msg)" />
                <n-space style="margin-top:8px;">
                  <n-button size="small" type="primary" @click="submitEdit(msg)">重新发送</n-button>
                  <n-button size="small" @click="editingId=null">取消</n-button>
                </n-space>
              </div>
            </div>
          </div>
          <div v-if="chatStore.isLoading" class="msg-row">
            <div class="msg-avatar-area"><span class="ai-avatar">AI</span></div>
            <div class="msg-body"><div class="typing"><span /><span /><span /></div></div>
          </div>
        </div>
      </div>

      <div class="chat-input-bar">
        <div class="input-row">
          <n-input
            ref="inputRef"
            v-model:value="inputText"
            type="textarea"
            placeholder="输入问题，Enter 发送…"
            :autosize="{ minRows: 1, maxRows: 4 }"
            :disabled="chatStore.isLoading"
            @keydown.enter.exact.prevent="handleSend"
            size="large"
            round
            style="flex:1;"
          />
          <n-button type="primary" circle size="large" :disabled="!inputText.trim() || chatStore.isLoading" @click="handleSend" style="margin-left:8px;">↑</n-button>
          <n-button circle size="large" :disabled="!currentId" @click="escalateToHuman" style="margin-left:4px;" title="转人工客服">🎧</n-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useChatStore } from '../stores/chat'
import { useMessage } from 'naive-ui'
import apiClient from '../api/client'
import MarkdownIt from 'markdown-it'

const route = useRoute(); const router = useRouter()
const authStore = useAuthStore(); const chatStore = useChatStore(); const message = useMessage()

const inputText = ref('')
const inputRef = ref<any>(null)
const msgContainer = ref<HTMLElement | null>(null)

const currentId = computed(() => (route.params.sessionId as string) || chatStore.currentSession?.id || null)

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

// Model selection
const selectedModel = ref('default')
const modelOptions = ref([{label:'🤖 默认DeepSeek',value:'default'}])

async function fetchModels(){
  try{const r=await apiClient.get('/finetune/models/active',{baseURL:'http://localhost:8808/api'});modelOptions.value=[{label:'🤖 默认DeepSeek',value:'default'},...r.data.map((m:any)=>({label:'🧠 '+m.model_name,value:m.proxy_url}))]}catch{}
}

function onModelChange(url:string){
  if(url==='default') localStorage.removeItem('custom_llm_url')
  else localStorage.setItem('custom_llm_url',url)
  // Reload needed for LLM switch — user can refresh
}

onMounted(async () => { fetchModels() });
function renderMd(t: string) { return t ? md.render(t) : '' }
function escapeHtml(t: string) { return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') }

function fmtTime(d: string) {
  if (!d) return ''
  return new Date(d).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function handleSend() {
  const t = inputText.value.trim()
  if (!t || chatStore.isLoading || !currentId.value) return
  inputText.value = ''
  await chatStore.sendMessage(currentId.value, t)
  nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight })
}

async function escalateToHuman() {
  if (!currentId.value) return
  try {
    const { default: apiClient } = await import('../api/client')
    await apiClient.post('/chat/escalate', { session_id: currentId.value })
    message.success('已转接人工客服，工单已生成')
  } catch (e: any) {
    console.error('转接失败:', e?.response?.status, e?.response?.data)
    message.error(e?.response?.data?.detail || '转接失败，请稍后重试')
    return
  }
  chatStore.messages.push({
    id: `escalate-${Date.now()}`,
    session_id: currentId.value,
    role: 'assistant',
    content: '🎧 **已为您转接人工客服**\n\n工单号：' + Date.now().toString(36).toUpperCase() + '\n\n⏰ 人工客服工作时间：每天 9:00-22:00\n📞 客服热线：**400-888-6666**\n\n请耐心等待，客服专员将尽快为您服务。您也可以直接拨打上方电话获得即时帮助。',
    citations: null,
    token_count: null,
    feedback: null,
    created_at: new Date().toISOString(),
  })
}

function copyMsg(t: string) { navigator.clipboard.writeText(t).then(() => message.success('已复制')) }

function deleteMsg(id: string) {
  const i = chatStore.messages.findIndex(m => m.id === id)
  if (i >= 0) chatStore.messages.splice(i, 1)
  message.success('已删除')
}

// Message editing
const editingId = ref<string | null>(null)
const editText = ref('')
function startEdit(msg: any) { editingId.value = msg.id; editText.value = msg.content }
async function submitEdit(msg: any) {
  const t = editText.value.trim()
  if (!t) return
  const idx = chatStore.messages.findIndex(m => m.id === msg.id)
  if (idx >= 0) {
    chatStore.messages.splice(idx, 1)
    inputText.value = t; editingId.value = null
    await nextTick(); handleSend()
  }
}

function exportChat() {
  const t = chatStore.messages.map(m => `[${fmtTime(m.created_at)}] ${m.role === 'user' ? '我' : 'AI'}: ${m.content}`).join('\n\n')
  const b = new Blob([t], { type: 'text/plain' })
  const u = URL.createObjectURL(b)
  const a = document.createElement('a'); a.href = u; a.download = `${chatStore.currentSession?.title || '对话'}.txt`; a.click()
  URL.revokeObjectURL(u)
  message.success('已导出')
}

async function quickStart(q: string) {
  if (!currentId.value) {
    const s = await chatStore.createSession()
    if (s) {
      router.push(`/chat/${s.id}`)
      inputText.value = q
      await nextTick()
      handleSend()
    }
  }
}

watch(() => route.params.sessionId, async id => {
  if (id && typeof id === 'string') {
    chatStore.messages = []
    const s = chatStore.sessions.find(x => x.id === id)
    if (s) { chatStore.currentSession = s; await chatStore.loadMessages(id); nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight }) }
  } else {
    chatStore.currentSession = null
    chatStore.messages = []
  }
}, { immediate: true })

onMounted(async () => {
  if (currentId.value) nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight })
})
</script>

<style scoped>
.chat-page { display: flex; flex-direction: column; height: 100%; background: #F8FAFC; transition: background var(--transition-normal); }

/* ═══ Welcome ═══ */
.chat-welcome {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 60px 40px; text-align: center;
}
.welcome-icon { font-size: 80px; margin-bottom: 24px; animation: float 4s ease-in-out infinite; }
.chat-welcome h1 { font-size: 28px; font-weight: 800; margin: 0 0 10px; color: #0F172A; letter-spacing: -0.3px; }
.chat-welcome p { color: #64748B; margin: 0 0 36px; font-size: 15px; }
.quick-cards { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
.quick-card {
  padding: 16px 28px; background: #fff; border: 1px solid #E2E8F0;
  border-radius: 14px; cursor: pointer; font-size: 14px; font-weight: 500;
  transition: all .25s var(--ease-smooth); color: #334155;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.quick-card:hover {
  background: #EEF2FF; border-color: #BFDBFE; color: #2563EB;
  transform: translateY(-3px); box-shadow: 0 8px 24px rgba(37,99,235,.12);
}

/* ═══ Top bar ═══ */
.chat-topbar {
  padding: 14px 24px; border-bottom: 1px solid #E5E7EB; display: flex;
  justify-content: space-between; align-items: center; background: rgba(255,255,255,.8);
  backdrop-filter: blur(12px); flex-shrink: 0;
}
.chat-topbar h3 { margin: 0; font-size: 15px; font-weight: 600; color: #0F172A; }

/* ═══ Messages ═══ */
.msg-scroll { flex: 1; overflow-y: auto; padding: 28px 24px; background: #F8FAFC; }
.msg-scroll::-webkit-scrollbar { width: 5px; }
.msg-scroll::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 5px; }
.msg-inner { max-width: 820px; margin: 0 auto; }
.msg-row { display: flex; gap: 12px; margin-bottom: 28px; animation: fadeInUp 0.3s var(--ease-smooth) both; }
.msg-row.me { flex-direction: row-reverse; }
.msg-avatar-area { flex-shrink: 0; }
.u-avatar { font-size: 32px; display: block; filter: drop-shadow(0 2px 4px rgba(0,0,0,.1)); }
.ai-avatar {
  display: flex; align-items: center; justify-content: center; width: 36px; height: 36px;
  border-radius: 50%; background: linear-gradient(135deg, #2563EB, #1D4ED8); color: #fff;
  font-size: 13px; font-weight: 700; box-shadow: 0 2px 8px rgba(37,99,235,.25);
}

.msg-body { flex: 1; min-width: 0; }
.msg-meta { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.msg-row.me .msg-meta { flex-direction: row-reverse; }
.msg-role { font-size: 12px; font-weight: 600; color: #64748B; }
.msg-time { font-size: 11px; color: #94A3B8; }
.msg-text {
  padding: 14px 18px; border-radius: 18px; font-size: 15px; line-height: 1.85;
  font-family: -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;
  word-break: break-word; letter-spacing: .01em;
}
.msg-me {
  background: linear-gradient(135deg, #2563EB, #7C3AED); color: #fff;
  border-bottom-right-radius: 6px; box-shadow: 0 2px 8px rgba(37,99,235,.2);
}
.msg-row:not(.me) .msg-text {
  background: #fff; color: #1E293B; border-bottom-left-radius: 6px;
  box-shadow: 0 1px 4px rgba(0,0,0,.04); border: 1px solid #F1F5F9;
}

/* AI markdown */
.msg-row:not(.me) .msg-text :deep(h1),
.msg-row:not(.me) .msg-text :deep(h2),
.msg-row:not(.me) .msg-text :deep(h3) { margin: 14px 0 6px; font-weight: 700; color: #0F172A; }
.msg-row:not(.me) .msg-text :deep(h2) { font-size: 17px; border-bottom: 2px solid #EEF2FF; padding-bottom: 6px; }
.msg-row:not(.me) .msg-text :deep(p) { margin: 0 0 8px; }
.msg-row:not(.me) .msg-text :deep(p:last-child) { margin-bottom: 0; }
.msg-row:not(.me) .msg-text :deep(strong) { font-weight: 700; color: #0F172A; }
.msg-row:not(.me) .msg-text :deep(ul),
.msg-row:not(.me) .msg-text :deep(ol) { margin: 6px 0; padding-left: 20px; }
.msg-row:not(.me) .msg-text :deep(li) { margin: 3px 0; }
.msg-row:not(.me) .msg-text :deep(table) { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 13px; border-radius: 8px; overflow: hidden; }
.msg-row:not(.me) .msg-text :deep(th) { background: #EEF2FF; padding: 10px 14px; text-align: left; font-weight: 600; border: 1px solid #E0E7FF; color: #1E3A5F; }
.msg-row:not(.me) .msg-text :deep(td) { padding: 10px 14px; border: 1px solid #F1F5F9; color: #334155; }
.msg-row:not(.me) .msg-text :deep(tr:nth-child(even)) { background: #F8FAFC; }
.msg-row:not(.me) .msg-text :deep(code) { background: #EEF2FF; padding: 2px 6px; border-radius: 4px; font-size: 13px; font-family: "Cascadia Code","Fira Code",Consolas,monospace; color: #2563EB; }
.msg-row:not(.me) .msg-text :deep(pre) { background: #1E293B; color: #cdd6f4; padding: 14px; border-radius: 10px; overflow-x: auto; margin: 10px 0; border: 1px solid #334155; }
.msg-row:not(.me) .msg-text :deep(pre code) { background: transparent; padding: 0; color: inherit; }
.msg-row:not(.me) .msg-text :deep(blockquote) { border-left: 3px solid #2563EB; padding: 8px 14px; margin: 10px 0; background: #EEF2FF; border-radius: 0 8px 8px 0; color: #475569; }

.msg-cite { margin-top: 6px; }
.cite-line { padding: 6px 0; border-bottom: 1px solid #F1F5F9; font-size: 13px; }
.cite-line p { margin: 2px 0 0; color: #64748B; }
.cite-tag { display: inline-block; background: #DBEAFE; color: #2563EB; padding: 2px 6px; border-radius: 4px; margin-right: 6px; font-size: 11px; font-weight: 600; }
.msg-acts { margin-top: 4px; opacity: 0; transition: opacity .2s; }
.msg-row:hover .msg-acts { opacity: 1; }

.typing { display: flex; gap: 4px; padding: 14px 18px; background: #fff; border-radius: 18px; border-bottom-left-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,.04); border: 1px solid #F1F5F9; }
.typing span { width: 7px; height: 7px; background: #94A3B8; border-radius: 50%; animation: bounce 1.4s infinite both; }
.typing span:nth-child(2) { animation-delay: .2s } .typing span:nth-child(3) { animation-delay: .4s }
@keyframes bounce { 0%,80%,100% { transform: scale(.6) } 40% { transform: scale(1) } }
.edit-area { margin-top: 8px; padding: 12px; background: #F8FAFC; border-radius: 10px; border: 1px solid #E2E8F0; }

/* ═══ Input bar ═══ */
.chat-input-bar { padding: 16px 24px 20px; border-top: 1px solid #E5E7EB; background: rgba(255,255,255,.9); backdrop-filter: blur(12px); flex-shrink: 0; }
.input-row { display: flex; align-items: flex-end; max-width: 820px; margin: 0 auto; }

/* ═══ Dark Mode ═══ */
[data-theme="dark"] .chat-page { background: #0B1120; }
[data-theme="dark"] .chat-topbar { border-bottom-color: #1E293B; background: rgba(11,17,32,.9); backdrop-filter: blur(12px); }
[data-theme="dark"] .chat-topbar h3 { color: #E2E8F0; }
[data-theme="dark"] .chat-welcome h1 { color: #E2E8F0; }
[data-theme="dark"] .chat-welcome p { color: #64748B; }
[data-theme="dark"] .quick-card { background: #1E293B; color: #94A3B8; border-color: #334155; }
[data-theme="dark"] .quick-card:hover { background: #1E3A5F; border-color: #2563EB; color: #60A5FA; box-shadow: 0 8px 24px rgba(37,99,235,.15); }
[data-theme="dark"] .msg-scroll { background: #0B1120; }
[data-theme="dark"] .msg-scroll::-webkit-scrollbar-thumb { background: #334155; }
[data-theme="dark"] .msg-role { color: #94A3B8; }
[data-theme="dark"] .msg-time { color: #64748B; }
[data-theme="dark"] .msg-row:not(.me) .msg-text { background: #1A2332; color: #CBD5E0; box-shadow: none; border-color: #1E293B; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(h1),
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(h2),
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(h3) { color: #E2E8F0; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(h2) { border-bottom-color: #1E3A5F; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(strong) { color: #E2E8F0; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(p) { color: #CBD5E0; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(li) { color: #CBD5E0; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(th) { background: #1E3A5F; border-color: #2A4A7F; color: #93C5FD; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(td) { border-color: #1E293B; color: #CBD5E0; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(tr:nth-child(even)) { background: rgba(30,58,95,.2); }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(code) { background: #1E293B; color: #60A5FA; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(pre) { background: #0F172A; border-color: #1E293B; }
[data-theme="dark"] .msg-row:not(.me) .msg-text :deep(blockquote) { background: #1E293B; border-left-color: #2563EB; color: #94A3B8; }
[data-theme="dark"] .typing { background: #1A2332; border-color: #1E293B; }
[data-theme="dark"] .chat-input-bar { border-top-color: #1E293B; background: rgba(11,17,32,.9); backdrop-filter: blur(12px); }
[data-theme="dark"] .cite-line { border-bottom-color: #1E293B; }
[data-theme="dark"] .cite-line p { color: #64748B; }
[data-theme="dark"] .edit-area { background: #1E293B; border-color: #334155; }
</style>
