<template>
  <div class="training-page">
    <!-- 左侧: 对练对话区 -->
    <div class="training-chat">
      <!-- 角色选择 -->
      <div v-if="!sessionActive" class="training-setup">
        <div class="setup-icon">🎯</div>
        <h1>AI 销售培训系统</h1>
        <p>选择客户类型，开始角色扮演对练。AI 将扮演客户并实时评分</p>

        <div class="customer-types">
          <div
            v-for="c in customerTypes"
            :key="c.key"
            class="customer-card"
            :class="{ selected: selectedType === c.key }"
            @click="selectedType = c.key"
          >
            <div class="cc-icon">{{ c.icon }}</div>
            <div class="cc-name">{{ c.name }}</div>
            <div class="cc-level">难度: {{ '⭐'.repeat(c.difficulty) }}</div>
            <div class="cc-desc">{{ c.desc }}</div>
          </div>
        </div>

        <n-input
          v-model:value="productContext"
          type="textarea"
          placeholder="输入产品背景知识，如：我们卖智能手表，核心卖点是健康监测、7天续航、防水…"
          :autosize="{ minRows: 2, maxRows: 4 }"
          style="max-width: 500px; margin-top: 16px;"
        />

        <n-button
          type="primary"
          size="large"
          :disabled="!selectedType"
          @click="startSession"
          style="margin-top: 20px;"
        >
          🎭 开始对练
        </n-button>
      </div>

      <!-- 对练对话 -->
      <template v-else>
        <div class="chat-header">
          <div class="ch-left">
            <span class="ch-icon">{{ currentCustomer?.icon }}</span>
            <div>
              <strong>{{ currentCustomer?.name }}</strong>
              <span class="ch-round">第 {{ currentRound }} 轮</span>
            </div>
          </div>
          <n-space>
            <n-button size="small" @click="endSession">⏹ 结束</n-button>
            <n-button size="small" @click="resetSession">🔄 换客户</n-button>
          </n-space>
        </div>

        <div class="chat-messages" ref="chatContainer">
          <div v-for="(msg, i) in messages" :key="i" class="chat-msg" :class="msg.role">
            <div class="cm-role">{{ msg.role === 'customer' ? currentCustomer?.icon + ' 客户' : '🧑 我' }}</div>
            <div class="cm-content">{{ msg.content }}</div>
            <div v-if="msg.hint" class="cm-hint">💡 {{ msg.hint }}</div>
          </div>

          <div v-if="isThinking" class="chat-msg customer">
            <div class="cm-role">{{ currentCustomer?.icon }} 客户</div>
            <div class="cm-content thinking">正在思考…</div>
          </div>
        </div>

        <div class="chat-input">
          <n-input
            v-model:value="userInput"
            type="textarea"
            placeholder="输入你的回应…"
            :autosize="{ minRows: 1, maxRows: 3 }"
            :disabled="isThinking"
            @keydown.enter.exact.prevent="handleSend"
          />
          <n-button type="primary" :disabled="!userInput.trim() || isThinking" @click="handleSend" style="margin-left: 8px;">发送</n-button>
        </div>
      </template>
    </div>

    <!-- 右侧: 实时评分面板 -->
    <aside class="training-scores" v-if="sessionActive">
      <h3>📊 实时评分</h3>

      <div class="score-card" v-for="dim in scoreDimensions" :key="dim.key">
        <div class="sc-header">
          <span class="sc-label">{{ dim.icon }} {{ dim.label }}</span>
          <span class="sc-value" :class="dim.levelClass">{{ dim.score }}</span>
        </div>
        <n-progress
          type="line"
          :percentage="dim.score"
          :color="dim.color"
          :height="8"
          :border-radius="4"
        />
        <div class="sc-comment">{{ dim.comment }}</div>
      </div>

      <div class="score-overall">
        <div class="so-label">综合评分</div>
        <div class="so-value">{{ overallScore }}</div>
        <div class="so-max">/ 100</div>
      </div>

      <div class="coach-hints">
        <h4>💡 教练提示</h4>
        <div v-if="coachHints.length === 0" class="no-hints">开始对话后会实时显示建议</div>
        <div v-for="(hint, i) in coachHints" :key="i" class="hint-item">
          {{ hint }}
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import { chatApi } from '../api/chat'
import { useAuthStore } from '../stores/auth'

const message = useMessage()
const authStore = useAuthStore()

const customerTypes = [
  { key: 'picky', icon: '🧐', name: '挑剔型', difficulty: 3, desc: '"太贵了，别家更便宜" — 反复质疑，吹毛求疵' },
  { key: 'price', icon: '💰', name: '价格敏感型', difficulty: 2, desc: '"能不能便宜点？" — 对价格极度敏感，反复砍价' },
  { key: 'hesitant', icon: '🤔', name: '犹豫型', difficulty: 4, desc: '"我再看看" — 摇摆不定，需要反复确认' },
  { key: 'expert', icon: '🎓', name: '专业型', difficulty: 5, desc: '"你们参数和行业标准不符" — 了解行业，问专业问题' },
]

const selectedType = ref('')
const productContext = ref('')
const sessionActive = ref(false)
const currentRound = ref(0)
const userInput = ref('')
const isThinking = ref(false)
const messages = ref<{ role: string; content: string; hint?: string }[]>([])

const scoreDimensions = ref([
  { key: 'fluency', icon: '🗣️', label: '流畅度', score: 0, color: '#667eea', comment: '', levelClass: '' },
  { key: 'persuasiveness', icon: '💪', label: '说服力', score: 0, color: '#10b981', comment: '', levelClass: '' },
  { key: 'knowledge', icon: '📚', label: '产品知识', score: 0, color: '#f59e0b', comment: '', levelClass: '' },
  { key: 'objection', icon: '🛡️', label: '异议处理', score: 0, color: '#ef4444', comment: '', levelClass: '' },
  { key: 'emotion', icon: '😌', label: '情绪控制', score: 0, color: '#8b5cf6', comment: '', levelClass: '' },
])
const coachHints = ref<string[]>([])

const chatContainer = ref<HTMLElement | null>(null)

const currentCustomer = computed(() => customerTypes.find(c => c.key === selectedType.value))
const overallScore = computed(() => {
  const scores = scoreDimensions.value.map(d => d.score)
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
})

function scoreLevel(v: number): string {
  if (v >= 80) return 'excellent'
  if (v >= 60) return 'good'
  if (v >= 40) return 'fair'
  return 'poor'
}

function startSession() {
  if (!selectedType.value) return
  sessionActive.value = true
  currentRound.value = 0
  messages.value = []
  coachHints.value = []
  scoreDimensions.value.forEach(d => { d.score = 0; d.comment = ''; d.levelClass = '' })
  // AI 客户开场
  const openings: Record<string, string> = {
    picky: '你们这个产品也太贵了吧？我朋友在别家买的才一半的价格。你说说，凭什么这么贵？',
    price: '你好，这款产品能不能便宜点？我预算有限，如果价格合适我就考虑。',
    hesitant: '产品看着挺好的，但我不着急买，想再看看别家的对比一下。',
    expert: '我看到你们的参数写着续航30小时，但行业标准测试条件下同类产品最多20小时，你们是怎么测出来的？',
  }
  messages.value.push({ role: 'customer', content: openings[selectedType.value] || '你好，开始吧。' })
  currentRound.value = 1
  nextTick(() => scrollToBottom())
}

function resetSession() { sessionActive.value = false; selectedType.value = '' }

async function handleSend() {
  const text = userInput.value.trim()
  if (!text || isThinking.value) return
  userInput.value = ''
  messages.value.push({ role: 'user', content: text })
  isThinking.value = true
  nextTick(() => scrollToBottom())

  try {
    const question = [
      `客户类型: ${currentCustomer.value?.name}`,
      `对话轮次: 第${currentRound.value}轮`,
      productContext.value ? `产品背景: ${productContext.value}` : '',
      `我的回应: ${text}`,
    ].filter(Boolean).join('\n')

    const response = await chatApi.askQuestion('training-room', question, authStore.token)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No reader')
    const decoder = new TextDecoder()
    let buffer = ''
    let fullContent = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          try {
            const event = JSON.parse(data)
            if (event.type === 'token') fullContent += event.content || ''
            else if (event.type === 'done') fullContent = event.data?.full_answer || fullContent
          } catch {}
        }
      }
    }

    // Parse AI response: customer text + coach hints + scores
    const customerLine = fullContent.match(/\*\*👤 客户\*\*[：:]\s*(.+)/)
    const hintLine = fullContent.match(/\*\*💡 教练提示\*\*[：:]\s*(.+)/)

    if (customerLine) {
      messages.value.push({ role: 'customer', content: customerLine[1], hint: hintLine?.[1] })
    } else {
      messages.value.push({ role: 'customer', content: fullContent.slice(0, 200) || '嗯，你继续说。' })
    }
    if (hintLine) coachHints.value.unshift(hintLine[1])

    // Mock score update (in production: parse from AI response)
    scoreDimensions.value.forEach(d => {
      d.score = Math.max(10, Math.min(95, (d.score || 40) + Math.floor(Math.random() * 15) - 5))
      d.levelClass = scoreLevel(d.score)
      if (!d.comment) d.comment = ['继续保持', '有进步', '还需加强', '表现出色'][Math.floor(Math.random() * 4)]
    })

    currentRound.value++
    nextTick(() => scrollToBottom())
  } catch (e: any) {
    message.error('响应失败: ' + (e.message || '请重试'))
  } finally {
    isThinking.value = false
  }
}

function endSession() {
  const total = overallScore.value
  const level = total >= 80 ? '优秀' : total >= 60 ? '良好' : total >= 40 ? '及格' : '需加强'
  message.success(`训练结束！综合评分: ${total}分 (${level})`)
}

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.training-page { display: flex; height: 100%; background: #fff; }

/* 左侧对话区 */
.training-chat { flex: 1; display: flex; flex-direction: column; min-width: 0; }

/* 设置页 */
.training-setup {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 40px; text-align: center;
}
.setup-icon { font-size: 56px; margin-bottom: 12px; }
.training-setup h1 { margin: 0 0 4px; font-size: 24px; color: #1a1a2e; }
.training-setup p { color: #888; margin: 0 0 24px; }
.customer-types { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; max-width: 700px; }
.customer-card {
  padding: 16px; background: #f8f9fb; border-radius: 12px; cursor: pointer;
  border: 2px solid transparent; width: 150px; transition: all .15s;
}
.customer-card:hover { border-color: #e0e3ee; transform: translateY(-2px); }
.customer-card.selected { border-color: #667eea; background: #f0f2fb; }
.cc-icon { font-size: 32px; margin-bottom: 4px; }
.cc-name { font-size: 15px; font-weight: 600; color: #333; }
.cc-level { font-size: 12px; color: #f59e0b; margin: 2px 0; }
.cc-desc { font-size: 11px; color: #999; }

/* 对话头 */
.chat-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; border-bottom: 1px solid #f0f0f0;
}
.ch-left { display: flex; align-items: center; gap: 8px; }
.ch-icon { font-size: 24px; }
.ch-round { font-size: 12px; color: #999; margin-left: 8px; }

/* 消息 */
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; }
.chat-msg { margin-bottom: 16px; max-width: 80%; }
.chat-msg.customer { margin-right: auto; }
.chat-msg.user { margin-left: auto; text-align: right; }
.cm-role { font-size: 12px; color: #999; margin-bottom: 4px; }
.cm-content {
  padding: 12px 16px; border-radius: 14px; font-size: 14px; line-height: 1.6;
}
.chat-msg.customer .cm-content { background: #f7f8fc; color: #1e1e2e; border-bottom-left-radius: 4px; }
.chat-msg.user .cm-content { background: linear-gradient(135deg, #667eea, #7c3aed); color: #fff; border-bottom-right-radius: 4px; }
.cm-content.thinking { color: #999; font-style: italic; }
.cm-hint { margin-top: 6px; padding: 6px 10px; background: #fef9e7; border-radius: 8px; font-size: 12px; color: #92400e; }

/* 输入 */
.chat-input { display: flex; align-items: flex-end; padding: 12px 20px; border-top: 1px solid #f0f0f0; }

/* 右侧评分 */
.training-scores {
  width: 280px; min-width: 280px; padding: 16px; border-left: 1px solid #eef0f4;
  overflow-y: auto; background: #fafbfd;
}
.training-scores h3 { margin: 0 0 16px; font-size: 16px; }
.score-card { margin-bottom: 14px; }
.sc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.sc-label { font-size: 13px; font-weight: 500; color: #555; }
.sc-value { font-size: 16px; font-weight: 700; }
.sc-value.excellent { color: #10b981; }
.sc-value.good { color: #667eea; }
.sc-value.fair { color: #f59e0b; }
.sc-value.poor { color: #ef4444; }
.sc-comment { font-size: 11px; color: #999; margin-top: 2px; }

.score-overall { text-align: center; padding: 16px; margin: 16px 0; background: linear-gradient(135deg, #667eea10, #7c3aed10); border-radius: 14px; }
.so-label { font-size: 12px; color: #999; }
.so-value { font-size: 36px; font-weight: 700; color: #667eea; line-height: 1.2; }
.so-max { font-size: 13px; color: #999; }

.coach-hints { margin-top: 16px; }
.coach-hints h4 { margin: 0 0 8px; font-size: 13px; color: #888; }
.no-hints { font-size: 12px; color: #ccc; }
.hint-item { padding: 6px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; color: #555; }

/* 暗色 */
[data-theme="dark"] .training-page { background: #101014; }
[data-theme="dark"] .training-setup h1 { color: #eee; }
[data-theme="dark"] .customer-card { background: #1e1e28; }
[data-theme="dark"] .customer-card:hover { border-color: #333; }
[data-theme="dark"] .customer-card.selected { border-color: #667eea; background: #1e1e30; }
[data-theme="dark"] .cc-name { color: #ddd; }
[data-theme="dark"] .chat-header { border-bottom-color: #222; }
[data-theme="dark"] .chat-msg.customer .cm-content { background: #1a1a24; color: #d8d8e8; }
[data-theme="dark"] .cm-hint { background: #2a2410; color: #e5c07b; }
[data-theme="dark"] .chat-input { border-top-color: #222; }
[data-theme="dark"] .training-scores { background: #14141a; border-left-color: #222; }
[data-theme="dark"] .sc-label { color: #aaa; }
[data-theme="dark"] .hint-item { border-bottom-color: #2a2a38; color: #aaa; }
[data-theme="dark"] .score-overall { background: rgba(102,126,234,.08); }
</style>
