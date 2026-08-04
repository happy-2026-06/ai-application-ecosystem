<template>
  <div class="studio-page">
    <!-- Sub-header bar -->
    <div class="studio-sub-header">
      <span class="back-link" @click="$router.push('/home')">← 返回首页</span>
      <h2>✍️ 创作工作台</h2>
    </div>

    <!-- 左侧: 创作需求输入 -->
    <aside class="studio-sidebar">

      <div class="input-section">
        <label class="section-label">📝 创作需求</label>
        <n-input
          v-model:value="inputText"
          type="textarea"
          placeholder="例如：我是卖充电宝的，帮我写一套抖音带货内容…"
          :autosize="{ minRows: 3, maxRows: 6 }"
          :disabled="isLoading"
        />
      </div>

      <div class="input-section">
        <label class="section-label">📱 目标平台</label>
        <div class="platform-checkboxes">
          <label class="platform-check" v-for="p in platforms" :key="p.value">
            <n-checkbox :value="p.value" :checked="selectedPlatforms.includes(p.value)" @update:checked="(v: boolean) => togglePlatform(p.value, v)" />
            <span class="platform-check-label" :style="{ color: p.color }">{{ p.value }}</span>
            <span class="platform-dot" :style="{ background: p.color }"></span>
          </label>
        </div>
      </div>

      <div class="input-section">
        <label class="section-label">📋 内容类型</label>
        <n-checkbox-group v-model:value="selectedTypes">
          <n-space>
            <n-checkbox value="标题" label="🔥 爆款标题" />
            <n-checkbox value="脚本" label="🎬 短视频脚本" />
            <n-checkbox value="图文" label="📝 图文文案" />
            <n-checkbox value="建议" label="💡 发布建议" />
          </n-space>
        </n-checkbox-group>
      </div>

      <n-button
        type="primary"
        block
        size="large"
        :loading="isLoading"
        :disabled="!inputText.trim() || selectedPlatforms.length === 0"
        @click="handleGenerate"
        class="generate-btn"
      >
        🚀 生成内容
      </n-button>

      <div class="quick-templates">
        <label class="section-label">⚡ 快捷模板</label>
        <div class="template-buttons">
          <button class="template-btn" @click="quickFill('我是卖充电宝的，帮我写抖音带货文案')">
            <span class="tpl-icon">🛍️</span>
            <span class="tpl-text">带货文案</span>
          </button>
          <button class="template-btn" @click="quickFill('帮我写一个小红书种草笔记，产品是蓝牙耳机')">
            <span class="tpl-icon">🌿</span>
            <span class="tpl-text">种草笔记</span>
          </button>
          <button class="template-btn" @click="quickFill('帮我生成5个B站科技类视频标题')">
            <span class="tpl-icon">📺</span>
            <span class="tpl-text">爆款标题</span>
          </button>
        </div>
      </div>
    </aside>

    <!-- 右侧: 结果展示 -->
    <main class="studio-main">
      <div v-if="!resultContent && !isLoading" class="studio-empty">
        <div class="empty-icon">🚀</div>
        <h1>AI 自媒体内容助手</h1>
        <p>输入你的产品或话题，选择平台和内容类型，AI 帮你生成可直接发布的爆款内容</p>
        <div class="feature-cards">
          <div class="feature-card" v-for="card in featureCardList" :key="card.title" :style="{ borderLeft: `3px solid ${card.color}` }">
            <div class="fc-icon">{{ card.icon }}</div>
            <div class="fc-title">{{ card.title }}</div>
            <div class="fc-desc">{{ card.desc }}</div>
          </div>
        </div>
      </div>

      <div v-else-if="isLoading" class="studio-loading">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
        </div>
        <h3>AI 正在创作中…</h3>
        <p>{{ loadingHint }}</p>
        <div class="loading-platforms">
          <span v-for="p in selectedPlatforms" :key="p" class="loading-platform-tag" :style="{ background: platformColorMap[p] || '#FF6B35' }">{{ p }}</span>
        </div>
        <div v-if="streamingContent" class="streaming-preview">
          <div v-html="renderMd(streamingContent)" class="md-content" />
        </div>
      </div>

      <div v-else class="studio-result">
        <div class="result-toolbar">
          <h3>📋 生成结果</h3>
          <n-space>
            <n-button size="small" secondary @click="copyAll">📋 复制全部</n-button>
            <n-button size="small" secondary @click="exportMD">⬇ 导出 Markdown</n-button>
            <n-button size="small" type="primary" ghost @click="handleRegenerate">🔄 重新生成</n-button>
          </n-space>
        </div>
        <div class="result-scroll">
          <div v-html="renderMd(resultContent)" class="md-content" />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import MarkdownIt from 'markdown-it'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const platformColorMap: Record<string, string> = {
  '抖音': '#FF0050',
  '小红书': '#FF2442',
  'B站': '#FB7299',
  '视频号': '#07C160',
  '快手': '#FF4906',
}

const platforms = [
  { value: '抖音', color: '#FF0050' },
  { value: '小红书', color: '#FF2442' },
  { value: 'B站', color: '#FB7299' },
  { value: '视频号', color: '#07C160' },
  { value: '快手', color: '#FF4906' },
]

const featureCardList = [
  { icon: '🔥', title: '爆款标题', desc: '5大平台风格适配', color: '#FF0050' },
  { icon: '🎬', title: '视频脚本', desc: '完整口播+分镜', color: '#FF2442' },
  { icon: '📝', title: '图文文案', desc: '小红书/公众号风格', color: '#FB7299' },
  { icon: '💡', title: '发布建议', desc: '最佳时间+互动话术', color: '#07C160' },
]

function togglePlatform(value: string, checked: boolean) {
  if (checked) {
    if (!selectedPlatforms.value.includes(value)) selectedPlatforms.value.push(value)
  } else {
    selectedPlatforms.value = selectedPlatforms.value.filter(p => p !== value)
  }
}

const LOADING_HINTS = [
  '正在分析你的创作需求…',
  '匹配最佳标题模板中…',
  '根据平台风格调整内容…',
  '正在生成爆款标题…',
  '撰写短视频脚本中…',
  '优化发布建议…',
]

const inputText = ref('')
const selectedPlatforms = ref<string[]>(['抖音'])
const selectedTypes = ref<string[]>(['标题', '脚本', '图文', '建议'])
const isLoading = ref(false)
const resultContent = ref('')
const streamingContent = ref('')
const loadingHint = ref('')
let hintTimer: ReturnType<typeof setInterval> | null = null

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
function renderMd(t: string) { return t ? md.render(t) : '' }

function quickFill(template: string) { inputText.value = template }

async function handleGenerate() {
  if (!inputText.value.trim() || isLoading.value) return

  isLoading.value = true
  streamingContent.value = ''
  resultContent.value = ''

  let hintIndex = 0
  loadingHint.value = LOADING_HINTS[0]
  hintTimer = setInterval(() => {
    hintIndex = (hintIndex + 1) % LOADING_HINTS.length
    loadingHint.value = LOADING_HINTS[hintIndex]
  }, 2000)

  try {
    const platformInfo = selectedPlatforms.value.join('、')
    const typeInfo = selectedTypes.value.join('、')
    const fullQuestion = `目标平台: ${platformInfo}\n内容类型: ${typeInfo}\n\n创作需求: ${inputText.value}`

    // 创建 session
    const createRes = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authStore.token}` },
      body: JSON.stringify({ title: inputText.value.slice(0, 30) }),
    })
    if (!createRes.ok) throw new Error('创建会话失败')
    const session = await createRes.json()
    const sessionId = session.id

    // SSE 请求
    const response = await fetch(`/api/chat/ask?session_id=${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authStore.token}` },
      body: JSON.stringify({ question: fullQuestion }),
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No reader')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6)
        if (data === '[DONE]') continue
        try {
          const event = JSON.parse(data)
          if (event.type === 'token') streamingContent.value += event.content || ''
          else if (event.type === 'done') resultContent.value = event.data?.full_answer || streamingContent.value
        } catch {}
      }
    }
  } catch (e: any) {
    message.error('生成失败: ' + (e.message || '请重试'))
    if (streamingContent.value && !resultContent.value) resultContent.value = streamingContent.value
    if (!resultContent.value) resultContent.value = '抱歉，内容生成失败，请重试。'
  } finally {
    isLoading.value = false
    if (hintTimer) { clearInterval(hintTimer); hintTimer = null }
  }
}

function copyAll() {
  if (!resultContent.value) return
  navigator.clipboard.writeText(resultContent.value).then(() => message.success('已复制'))
}

function exportMD() {
  if (!resultContent.value) return
  const blob = new Blob([resultContent.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `自媒体内容_${new Date().toISOString().slice(0,10)}.md`; a.click()
  URL.revokeObjectURL(url)
  message.success('已导出')
}

function handleRegenerate() { resultContent.value = ''; streamingContent.value = ''; handleGenerate() }

onUnmounted(() => { if (hintTimer) clearInterval(hintTimer) })

onMounted(() => {
  // Handle template from query params (from dashboard quick start / templates)
  const template = route.query.template as string | undefined
  if (template) {
    inputText.value = template
    // Optional: auto-select platforms from query
    const platformsQuery = route.query.platforms as string | undefined
    if (platformsQuery) {
      selectedPlatforms.value = platformsQuery.split(',').filter(p => platforms.some(pl => pl.value === p))
    }
  }
})
</script>

<style scoped>
.studio-page { display: flex; flex-wrap: wrap; height: 100%; }

/* ── Sub-header bar ── */
.studio-sub-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 20px;
  border-bottom: 1px solid #FDE8E0;
  background: rgba(255, 251, 248, .9);
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}

.back-link {
  font-size: 13px;
  color: #FF6B35;
  cursor: pointer;
  font-weight: 600;
  transition: opacity .15s;
  user-select: none;
}

.back-link:hover {
  opacity: .7;
}

.studio-sub-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #1A0F2E;
}

/* ── Sidebar area ── */
.studio-sidebar { width: 320px; min-width: 320px; max-width: 360px; padding: 20px; background: #FFFBF8; border-right: 1px solid #FDE8E0; display: flex; flex-direction: column; gap: 4px; overflow-y: auto; }
.input-section { margin-top: 14px; }
.section-label { display: block; font-size: 12px; font-weight: 700; color: #FF6B35; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }

/* Platform checkboxes with brand colors */
.platform-checkboxes { display: flex; flex-wrap: wrap; gap: 6px; }
.platform-check { display: flex; align-items: center; gap: 4px; cursor: pointer; padding: 2px 0; }
.platform-check-label { font-size: 13px; font-weight: 600; }
.platform-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-left: 2px; }

/* Generate button */
.generate-btn { margin-top: 16px; height: 48px; font-size: 16px; font-weight: 700; border-radius: 12px; }

/* Quick templates */
.quick-templates { margin-top: 20px; padding-top: 16px; border-top: 1px solid #FDE8E0; }
.template-buttons { display: flex; flex-direction: column; gap: 6px; }
.template-btn {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border: 1px solid #FDE8E0; border-radius: 10px; background: #FFFBF8;
  cursor: pointer; font-size: 13px; color: #555; transition: all .15s;
  font-family: inherit; width: 100%; text-align: left;
}
.template-btn:hover { background: #FFF0EB; border-color: #FFB088; color: #FF6B35; }
.tpl-icon { font-size: 16px; flex-shrink: 0; }
.tpl-text { font-weight: 500; }

/* Main area */
.studio-main { flex: 1 1 400px; display: flex; flex-direction: column; min-width: 0; min-height: 0; background: #fff; }
.studio-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px; text-align: center; }
.empty-icon { font-size: 64px; margin-bottom: 16px; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
.studio-empty h1 { font-size: 26px; font-weight: 700; margin: 0 0 8px; color: #1A0F2E; }
.studio-empty p { color: #888; margin: 0 0 32px; max-width: 440px; line-height: 1.6; }
.feature-cards { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
.feature-card {
  padding: 16px 20px; background: #FFFBF8; border-radius: 12px; text-align: center;
  min-width: 130px; border-left: 3px solid #FF6B35; box-shadow: 0 2px 10px rgba(255,107,53,.08);
  transition: transform .15s, box-shadow .15s;
}
.feature-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(255,107,53,.15); }
.fc-icon { font-size: 28px; margin-bottom: 4px; }
.fc-title { font-size: 14px; font-weight: 700; color: #1A0F2E; }
.fc-desc { font-size: 12px; color: #999; margin-top: 2px; }

/* Loading */
.studio-loading { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px; }
.loading-spinner { margin-bottom: 16px; }
.spinner-ring {
  width: 48px; height: 48px; border: 4px solid #f0e0d0; border-top: 4px solid #FF6B35;
  border-radius: 50%; animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.studio-loading h3 { margin: 12px 0 6px; font-size: 18px; color: #333; }
.studio-loading p { color: #999; font-size: 14px; margin: 0 0 16px; }
.loading-platforms { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-bottom: 24px; }
.loading-platform-tag {
  padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
  color: #fff; animation: pulse 1.5s infinite;
}
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .5; } }
.streaming-preview { width: 100%; max-width: 820px; max-height: 60vh; overflow-y: auto; }

/* Result */
.studio-result { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.result-toolbar {
  padding: 14px 24px; border-bottom: 1px solid #FDE8E0;
  background: rgba(255,251,248,.8); backdrop-filter: blur(8px);
  display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;
}
.result-toolbar h3 { margin: 0; font-size: 16px; font-weight: 600; color: #1A0F2E; }
.result-scroll { flex: 1; overflow-y: auto; padding: 24px 32px; }

/* Markdown content */
.md-content { max-width: 820px; margin: 0 auto; font-size: 15px; line-height: 1.85; color: #1e1e2e; }
.md-content :deep(h1), .md-content :deep(h2), .md-content :deep(h3) { margin: 18px 0 8px; font-weight: 700; }
.md-content :deep(h2) {
  font-size: 18px; border-bottom: 2px solid transparent;
  background: linear-gradient(90deg, #FF6B35 0%, #FF6B35 40px, #FDE8E0 40px, #FDE8E0 100%) bottom / 100% 2px no-repeat;
  padding-bottom: 6px; color: #1A0F2E;
}
.md-content :deep(p) { margin: 0 0 10px; }
.md-content :deep(table) { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 14px; border-radius: 8px; overflow: hidden; }
.md-content :deep(th) { background: #FF6B35; color: #fff; padding: 8px 12px; text-align: left; font-weight: 600; border: none; }
.md-content :deep(td) { padding: 8px 12px; border-bottom: 1px solid #FDE8E0; }
.md-content :deep(tr:nth-child(even) td) { background: #FFFBF8; }
.md-content :deep(tr:hover td) { background: #FFF0EB; }
.md-content :deep(code) { background: #FFF0EB; color: #E11D48; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.md-content :deep(pre) { background: #1A0F2E; color: #e0d0f0; padding: 16px; border-radius: 10px; overflow-x: auto; }
.md-content :deep(pre code) { background: transparent; color: inherit; padding: 0; }
.md-content :deep(blockquote) { border-left: 3px solid #FF6B35; margin: 10px 0; padding: 8px 16px; background: #FFFBF8; border-radius: 0 8px 8px 0; color: #666; }
.md-content :deep(strong) { color: #FF6B35; }
.md-content :deep(ul), .md-content :deep(ol) { padding-left: 20px; }
.md-content :deep(li) { margin-bottom: 4px; }

/* Dark mode */
[data-theme="dark"] .studio-sub-header { background: rgba(15, 10, 20, .9); border-bottom-color: #2a1a2a; }
[data-theme="dark"] .studio-sub-header h2 { color: #eee; }
[data-theme="dark"] .studio-sidebar { background: #120a18; border-right-color: #2a1a2a; }
[data-theme="dark"] .section-label { color: #aaa; }
[data-theme="dark"] .quick-templates { border-top-color: #2a1a2a; }
[data-theme="dark"] .template-btn { background: #1a0f1e; border-color: #2a1a2a; color: #999; }
[data-theme="dark"] .template-btn:hover { background: #2a1528; border-color: #FF6B35; color: #ffb080; }
[data-theme="dark"] .studio-main { background: #0F0A14; }
[data-theme="dark"] .studio-empty h1 { color: #eee; }
[data-theme="dark"] .feature-card { background: #1a0f1e; }
[data-theme="dark"] .fc-title { color: #ddd; }
[data-theme="dark"] .studio-loading h3 { color: #ddd; }
[data-theme="dark"] .result-toolbar { border-bottom-color: #2a1a2a; background: rgba(15,10,20,.8); }
[data-theme="dark"] .result-toolbar h3 { color: #eee; }
[data-theme="dark"] .md-content { color: #d8d8e8; }
[data-theme="dark"] .md-content :deep(h2) { color: #eee; background: linear-gradient(90deg, #FF6B35 0%, #FF6B35 40px, #2a1a2a 40px, #2a1a2a 100%) bottom / 100% 2px no-repeat; }
[data-theme="dark"] .md-content :deep(th) { background: #3a1a2a; }
[data-theme="dark"] .md-content :deep(td) { border-bottom-color: #2a1a2a; }
[data-theme="dark"] .md-content :deep(tr:nth-child(even) td) { background: #120a18; }
[data-theme="dark"] .md-content :deep(tr:hover td) { background: #1a1020; }
[data-theme="dark"] .md-content :deep(code) { background: #2a1a2a; color: #ff8080; }
[data-theme="dark"] .md-content :deep(pre) { background: #0a0614; }
[data-theme="dark"] .md-content :deep(blockquote) { background: #1a0f1e; border-left-color: #FF6B35; color: #999; }
[data-theme="dark"] .md-content :deep(strong) { color: #ffa070; }
[data-theme="dark"] .spinner-ring { border-color: #2a1a2a; border-top-color: #FF6B35; }
</style>
