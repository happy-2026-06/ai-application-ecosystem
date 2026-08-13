<template>
  <div class="training-page">
    <!-- Left: Training Area -->
    <div class="training-main">
      <!-- Setup Screen -->
      <div v-if="!sessionActive" class="setup-area">
        <div class="setup-hero">
          <div class="setup-icon-wrap"><span>🎯</span></div>
          <h1>开始销售对练</h1>
          <p>选择一个客户类型，AI 将扮演该客户与你进行真实的销售对话，并实时给出评分和建议</p>
        </div>

        <div class="customer-grid">
          <div
            v-for="c in customerTypes"
            :key="c.key"
            class="customer-card"
            :class="{ selected: selectedType === c.key }"
            @click="selectedType = c.key"
          >
            <div class="cc-icon">{{ c.icon }}</div>
            <div class="cc-info">
              <div class="cc-name">{{ c.name }}</div>
              <div class="cc-stars">{{ '⭐'.repeat(c.difficulty) }}</div>
            </div>
            <div class="cc-desc">{{ c.desc }}</div>
            <div class="cc-check" v-if="selectedType === c.key">✓</div>
          </div>
        </div>

        <div class="setup-actions">
          <n-input
            v-model:value="productContext"
            type="textarea"
            placeholder="输入你的产品背景信息（可选）&#10;例如：我们卖智能手表，核心卖点是健康监测、7天续航、50米防水…"
            :autosize="{ minRows: 2, maxRows: 4 }"
            class="setup-input"
          />
          <div class="setup-btns">
            <n-button
              type="primary"
              size="large"
              :disabled="!selectedType"
              :loading="isStarting"
              @click="startSession"
              class="start-btn"
            >
              🎭 开始对练
            </n-button>
            <n-button size="large" @click="showHistory = true" class="history-btn">
              📋 训练记录
            </n-button>
          </div>
        </div>
      </div>

      <!-- Active Training -->
      <template v-else>
        <div class="chat-header">
          <div class="ch-left">
            <span class="ch-icon">{{ currentCustomer?.icon }}</span>
            <div class="ch-info">
              <strong>{{ currentCustomer?.name }}</strong>
              <span>第 {{ currentRound }} 轮对话</span>
            </div>
          </div>
          <div class="ch-actions">
            <n-button v-if="!isReplay" size="small" quaternary @click="endSession">⏹ 结束训练</n-button>
            <n-button v-else size="small" quaternary @click="openReport">📊 查看报告</n-button>
            <n-button size="small" quaternary @click="resetSession">{{ isReplay ? '✕ 退出回放' : '🔄 换客户' }}</n-button>
          </div>
        </div>

        <div v-if="isReplay" class="replay-banner">👁️ 查看历史记录 — 该训练已结束，以下为只读回放</div>

        <div class="chat-messages" ref="chatContainer">
          <div v-for="(msg, i) in messages" :key="i" class="chat-msg" :class="msg.role">
            <div class="cm-avatar">
              {{ msg.role === 'customer' ? currentCustomer?.icon : '🧑' }}
            </div>
            <div class="cm-body">
              <div class="cm-name">
                {{ msg.role === 'customer' ? currentCustomer?.name + ' (客户)' : '我' }}
              </div>
              <div class="cm-content">{{ msg.content }}</div>
              <div v-if="msg.hint" class="cm-hint">
                💡 {{ msg.hint }}
              </div>
            </div>
          </div>

          <div v-if="isThinking" class="chat-msg customer">
            <div class="cm-avatar">{{ currentCustomer?.icon }}</div>
            <div class="cm-body">
              <div class="cm-name">{{ currentCustomer?.name }} (客户)</div>
              <div class="cm-content thinking">
                <span class="thinking-dots">正在思考<span>...</span></span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="isReplay" class="replay-bar">
          <span class="replay-bar-text">👁️ 训练已结束，无法继续对话 — 可查看报告或开始新一轮对练</span>
          <n-button size="small" quaternary type="primary" @click="openReport">📊 查看报告</n-button>
          <n-button size="small" type="primary" @click="resetSession">🎭 开始新对练</n-button>
        </div>
        <div v-else class="chat-input-bar">
          <n-input
            v-model:value="userInput"
            type="textarea"
            placeholder="输入你的回应…"
            :autosize="{ minRows: 1, maxRows: 3 }"
            :disabled="isThinking"
            @keydown.enter.exact.prevent="handleSend"
            class="chat-field"
          />
          <n-button
            type="primary"
            :disabled="!userInput.trim() || isThinking"
            :loading="isThinking"
            @click="handleSend"
            class="send-btn"
          >
            发送
          </n-button>
        </div>
      </template>
    </div>

    <!-- Right: Score Panel -->
    <aside class="score-panel" v-if="sessionActive">
      <div class="sp-header">
        <h3>📊 实时评分</h3>
        <div class="sp-overall">
          <div class="spo-value">{{ overallScore }}</div>
          <div class="spo-label">综合分</div>
        </div>
      </div>

      <div class="sp-dimensions">
        <div class="sp-dim" v-for="dim in scoreDimensions" :key="dim.key">
          <div class="spd-header">
            <span class="spd-label">{{ dim.icon }} {{ dim.label }}</span>
            <span class="spd-score" :class="dim.levelClass">{{ dim.score }}</span>
          </div>
          <div class="spd-bar">
            <div class="spd-fill" :style="{ width: dim.score + '%', background: dim.color }" />
          </div>
          <div class="spd-comment">{{ dim.comment || '等待首轮对话' }}</div>
        </div>
      </div>

      <div class="sp-hints">
        <div class="sph-title">💡 教练提示</div>
        <div v-if="coachHints.length === 0" class="sph-empty">开始对话后这里会实时显示教练建议</div>
        <div v-for="(hint, i) in coachHints" :key="i" class="sph-item">
          <div class="sph-num">{{ i + 1 }}</div>
          <div>{{ hint }}</div>
        </div>
      </div>
    </aside>

    <!-- History Modal -->
    <n-modal v-model:show="showHistory" title="训练记录" style="width: 800px;" :mask-closable="true">
      <TrainingHistory @select="loadHistorySession" @close="showHistory = false" />
    </n-modal>

    <!-- Report Modal -->
    <n-modal v-model:show="showReport" title="训练总结报告" style="width: 700px;" :mask-closable="true">
      <div v-if="reportData" class="report-content">
        <div class="report-hero">
          <div class="rh-label">综合评分</div>
          <div class="rh-value">{{ reportData.session.overall_score ?? overallScore }}</div>
        </div>
        <div class="report-section">
          <h4>📈 进步曲线</h4>
          <template v-if="trendEntries.length">
            <div class="trend-chart">
              <div class="trend-y-axis">
                <span class="trend-y-label" style="top: 0%">100</span>
                <span class="trend-y-label" style="top: 25%">75</span>
                <span class="trend-y-label" style="top: 50%">50</span>
                <span class="trend-y-label" style="top: 75%">25</span>
                <span class="trend-y-label" style="top: 100%">0</span>
              </div>
              <div class="trend-cols">
                <div v-for="entry in trendEntries" :key="entry.round" class="trend-col">
                  <span class="trend-val">{{ entry.overall }}</span>
                  <div class="trend-bars">
                    <div class="trend-gridline" style="top: 0%" />
                    <div class="trend-gridline" style="top: 25%" />
                    <div class="trend-gridline" style="top: 50%" />
                    <div class="trend-gridline" style="top: 75%" />
                    <div
                      v-for="dim in scoreDimensions"
                      :key="dim.key"
                      class="trend-bar"
                      :style="{ height: barHeight(entry[dim.key]), background: dim.color }"
                      :title="`第${entry.round}轮 · ${dim.label}: ${entry[dim.key] ?? 0}分`"
                    />
                    <div
                      class="trend-bar trend-bar-overall"
                      :style="{ height: barHeight(entry.overall) }"
                      :title="`第${entry.round}轮 · 综合: ${entry.overall}分`"
                    />
                  </div>
                  <span class="trend-round">第{{ entry.round }}轮</span>
                </div>
              </div>
            </div>
            <div class="trend-legend">
              <span v-for="dim in scoreDimensions" :key="dim.key" class="trend-legend-item">
                <i class="tli-dot" :style="{ background: dim.color }" />{{ dim.label }}
              </span>
              <span class="trend-legend-item"><i class="tli-dot tli-overall" />综合</span>
            </div>
          </template>
          <p v-else class="trend-empty">暂无评分数据 — 完成至少一轮对话后即可查看进步曲线</p>
        </div>
        <div class="report-section" v-if="reportData.strengths.length">
          <h4>💪 优势</h4>
          <ul><li v-for="s in reportData.strengths" :key="s">{{ s }}</li></ul>
        </div>
        <div class="report-section" v-if="reportData.improvements.length">
          <h4>🔧 待改进</h4>
          <ul><li v-for="s in reportData.improvements" :key="s">{{ s }}</li></ul>
        </div>
        <div class="report-section" v-if="reportData.recommendation">
          <h4>📈 训练建议</h4>
          <p>{{ reportData.recommendation }}</p>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import { trainingApi, type TrainingReport } from '../api/training'
import { useAuthStore } from '../stores/auth'
import TrainingHistory from './TrainingHistory.vue'

const message = useMessage()
const authStore = useAuthStore()

const customerTypes = [
  { key: 'picky', icon: '🧐', name: '挑剔型', difficulty: 3, desc: '"太贵了，别家更便宜" — 反复质疑、吹毛求疵' },
  { key: 'price', icon: '💰', name: '价格敏感型', difficulty: 2, desc: '"能不能便宜点？" — 极度敏感、反复砍价' },
  { key: 'hesitant', icon: '🤔', name: '犹豫型', difficulty: 4, desc: '"我再看看" — 摇摆不定、需要反复确认' },
  { key: 'expert', icon: '🎓', name: '专业型', difficulty: 5, desc: '"参数和行业标准不符" — 了解行业、问专业问题' },
]

const selectedType = ref('')
const productContext = ref('')
const sessionActive = ref(false)
const isStarting = ref(false)
const currentSessionId = ref('')
const currentRound = ref(0)
const userInput = ref('')
const isThinking = ref(false)
const showHistory = ref(false)
const showReport = ref(false)
const reportData = ref<TrainingReport | null>(null)
const isReplay = ref(false)

interface ChatMsg { role: string; content: string; hint?: string }
const messages = ref<ChatMsg[]>([])

const scoreDimensions = ref([
  { key: 'fluency', icon: '🗣️', label: '流畅度', score: 0, color: '#3b82f6', comment: '', levelClass: '' },
  { key: 'persuasiveness', icon: '💪', label: '说服力', score: 0, color: '#22c55e', comment: '', levelClass: '' },
  { key: 'knowledge', icon: '📚', label: '产品知识', score: 0, color: '#f59e0b', comment: '', levelClass: '' },
  { key: 'objection', icon: '🛡️', label: '异议处理', score: 0, color: '#ef4444', comment: '', levelClass: '' },
  { key: 'emotion', icon: '😌', label: '情绪控制', score: 0, color: '#8b5cf6', comment: '', levelClass: '' },
])
const coachHints = ref<string[]>([])
const chatContainer = ref<HTMLElement | null>(null)

const currentCustomer = computed(() => customerTypes.find(c => c.key === selectedType.value))
const overallScore = computed(() => {
  const scores = scoreDimensions.value.map(d => d.score)
  if (scores.every(s => s === 0)) return 0
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
})

// 进步曲线数据（报告中的 score_trend）
const trendEntries = computed(() => reportData.value?.score_trend ?? [])
function barHeight(v: number | undefined): string {
  const score = Math.max(0, Math.min(100, Number(v) || 0))
  return score + '%'
}

function scoreLevel(v: number): string {
  if (v >= 80) return 'excellent'
  if (v >= 60) return 'good'
  if (v >= 40) return 'fair'
  return 'poor'
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  })
}

function applyScores(scores: Record<string, number> | null) {
  if (!scores) return
  for (const dim of scoreDimensions.value) {
    if (scores[dim.key] !== undefined) {
      dim.score = scores[dim.key]
      dim.levelClass = scoreLevel(dim.score)
      dim.comment = dim.score >= 80 ? '表现出色' : dim.score >= 60 ? '良好' : dim.score >= 40 ? '有待提升' : '需要重点练习'
    }
  }
}

async function startSession() {
  if (!selectedType.value) return
  isStarting.value = true
  try {
    const res = await trainingApi.createSession(selectedType.value, productContext.value || undefined)
    const session = res.data
    currentSessionId.value = session.id
    sessionActive.value = true
    isReplay.value = false
    currentRound.value = 0
    messages.value = []
    coachHints.value = []
    scoreDimensions.value.forEach(d => { d.score = 0; d.comment = ''; d.levelClass = '' })
    const roundsRes = await trainingApi.getRounds(session.id)
    if (roundsRes.data.length > 0) {
      messages.value.push({ role: 'customer', content: roundsRes.data[0].customer_response })
    }
    currentRound.value = 1
    scrollToBottom()
  } catch (e: any) {
    message.error('创建会话失败: ' + (e?.response?.data?.detail || e.message))
  } finally { isStarting.value = false }
}

function resetSession() {
  sessionActive.value = false
  isReplay.value = false
  selectedType.value = ''
  currentSessionId.value = ''
  userInput.value = ''
}

async function handleSend() {
  const text = userInput.value.trim()
  if (!text || isThinking.value || !currentSessionId.value || isReplay.value) return
  userInput.value = ''
  messages.value.push({ role: 'user', content: text })
  isThinking.value = true
  scrollToBottom()

  try {
    const response = await trainingApi.respond(currentSessionId.value, text, authStore.token)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const reader = response.body?.getReader()
    if (!reader) throw new Error('No reader')
    const decoder = new TextDecoder()
    let buffer = '', customerText = '', hintText: string | null = null, scoresData: Record<string, number> | null = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        if (line.slice(6) === '[DONE]') continue
        try {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'done') {
            customerText = event.data?.customer_response || customerText
            hintText = event.data?.coach_hint || null
            scoresData = event.data?.scores || null
          }
        } catch {}
      }
    }

    messages.value.push({ role: 'customer', content: customerText || '嗯，继续说。', hint: hintText || undefined })
    if (hintText) coachHints.value.unshift(hintText)
    applyScores(scoresData)
    currentRound.value++
    scrollToBottom()
  } catch (e: any) { message.error('响应失败: ' + (e.message || '请重试')) }
  finally { isThinking.value = false }
}

async function openReport() {
  if (!currentSessionId.value) return
  try {
    const reportRes = await trainingApi.getReport(currentSessionId.value)
    reportData.value = reportRes.data
    showReport.value = true
  } catch { message.error('获取报告失败') }
}

async function endSession() {
  try {
    if (currentSessionId.value) {
      await trainingApi.endSession(currentSessionId.value)
      message.success(`训练结束！综合评分: ${overallScore.value} 分`)
      await openReport()
    }
    sessionActive.value = false
    isReplay.value = false
  } catch { message.error('结束训练失败') }
}

async function loadHistorySession(sessionId: string) {
  showHistory.value = false
  try {
    const res = await trainingApi.getSession(sessionId)
    const session = res.data
    currentSessionId.value = session.id
    selectedType.value = session.customer_type
    productContext.value = session.product_context || ''
    sessionActive.value = true
    // 已结束的会话为只读回放；进行中的会话可继续对练
    isReplay.value = session.status !== 'active'
    currentRound.value = session.total_rounds
    messages.value = []
    coachHints.value = []
    const roundsRes = await trainingApi.getRounds(sessionId)
    for (const r of roundsRes.data) {
      if (r.round_number === 0) {
        messages.value.push({ role: 'customer', content: r.customer_response })
      } else {
        messages.value.push({ role: 'user', content: r.user_response })
        messages.value.push({ role: 'customer', content: r.customer_response, hint: r.coach_hint || undefined })
        if (r.coach_hint) coachHints.value.unshift(r.coach_hint)
        if (r.scores) applyScores(r.scores)
      }
    }
    scrollToBottom()
  } catch { message.error('加载历史记录失败') }
}
</script>

<style scoped>
.training-page { display: flex; height: 100%; background: #f8fafc; }

/* ── 对练主区域 ── */
.training-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

/* ── 设置页 ── */
.setup-area {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 48px 40px; overflow-y: auto;
}
.setup-hero { text-align: center; margin-bottom: 36px; }
.setup-icon-wrap {
  width: 80px; height: 80px; line-height: 80px; border-radius: 24px;
  background: linear-gradient(135deg, #eff6ff, #eef2ff);
  display: inline-block; margin-bottom: 20px; font-size: 36px;
}
.setup-hero h1 { font-size: 28px; font-weight: 800; color: #0f172a; margin: 0 0 8px; }
.setup-hero p { color: #64748b; font-size: 15px; margin: 0; max-width: 500px; line-height: 1.5; }

/* 客户卡片 */
.customer-grid { display: flex; gap: 14px; margin-bottom: 28px; max-width: 700px; }
.customer-card {
  flex: 1; padding: 20px 16px; background: #fff; border-radius: 16px;
  border: 2px solid #e8ecf1; cursor: pointer; transition: all .2s;
  position: relative; text-align: center;
}
.customer-card:hover { border-color: #93c5fd; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.04); }
.customer-card.selected { border-color: #3b82f6; background: #f8faff; box-shadow: 0 4px 20px rgba(59,130,246,.08); }
.cc-icon { font-size: 36px; margin-bottom: 8px; }
.cc-name { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 2px; }
.cc-stars { font-size: 11px; margin-bottom: 8px; }
.cc-desc { font-size: 12px; color: #94a3b8; line-height: 1.5; }
.cc-check {
  position: absolute; top: 10px; right: 10px;
  width: 22px; height: 22px; border-radius: 50%;
  background: #3b82f6; color: #fff; font-size: 12px; line-height: 22px;
  text-align: center; font-weight: 700;
}

/* 设置按钮 */
.setup-actions { width: 100%; max-width: 540px; }
.setup-input { margin-bottom: 16px; }
:deep(.setup-input .n-input) {
  --n-border: 1px solid #e2e8f0 !important;
  --n-border-focus: 1px solid #3b82f6 !important;
  --n-color: #fff !important; --n-color-focus: #fff !important;
  --n-text-color: #334155 !important; --n-placeholder-color: #94a3b8 !important;
  border-radius: 14px !important;
}
.setup-btns { display: flex; gap: 12px; }
.start-btn {
  flex: 1; height: 48px !important; font-size: 16px !important; font-weight: 700 !important;
  border-radius: 14px !important; background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
  border: none !important; box-shadow: 0 4px 16px rgba(59,130,246,.2);
}
.start-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(99,102,241,.3) !important; }
.history-btn {
  height: 48px !important; font-size: 15px !important; border-radius: 14px !important;
  border: 1px solid #e2e8f0 !important; color: #475569 !important; background: #fff !important;
}
.history-btn:hover { border-color: #cbd5e1 !important; background: #f8fafc !important; }

/* ── 对话区域 ── */
.chat-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 24px; border-bottom: 1px solid #e8ecf1;
  background: #fff;
}
.ch-left { display: flex; align-items: center; gap: 10px; }
.ch-icon { font-size: 28px; }
.ch-info strong { display: block; font-size: 14px; color: #1e293b; }
.ch-info span { font-size: 12px; color: #94a3b8; }

/* 消息 */
.chat-messages { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.chat-msg { display: flex; gap: 12px; max-width: 85%; }
.chat-msg.user { align-self: flex-end; flex-direction: row-reverse; }
.cm-avatar {
  width: 36px; height: 36px; border-radius: 12px; display: flex; align-items: center;
  justify-content: center; font-size: 18px; background: #f1f5f9; flex-shrink: 0;
}
.chat-msg.user .cm-avatar { background: #eff6ff; }
.cm-body { min-width: 0; }
.cm-name { font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
.chat-msg.user .cm-name { text-align: right; }
.cm-content {
  padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6;
  background: #f1f5f9; color: #334155;
}
.chat-msg.user .cm-content {
  background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff;
}
.cm-content.thinking { color: #94a3b8; font-style: italic; }
.cm-hint {
  margin-top: 6px; padding: 8px 12px; background: #fffbeb; border: 1px solid #fde68a;
  border-radius: 10px; font-size: 12px; color: #92400e; line-height: 1.5;
}

/* 输入 */
.chat-input-bar {
  display: flex; align-items: flex-end; gap: 10px;
  padding: 16px 24px; border-top: 1px solid #e8ecf1; background: #fff;
}
:deep(.chat-field .n-input) {
  --n-border: 1px solid #e2e8f0 !important;
  --n-border-focus: 1px solid #3b82f6 !important;
  --n-color: #f8fafc !important; --n-color-focus: #fff !important;
  --n-text-color: #334155 !important; --n-placeholder-color: #94a3b8 !important;
  border-radius: 14px !important;
}
.send-btn {
  height: 42px !important; padding: 0 20px !important; font-weight: 700 !important;
  border-radius: 12px !important; background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
  border: none !important; flex-shrink: 0;
}

/* ── 评分面板 ── */
.score-panel {
  width: 300px; min-width: 300px; padding: 24px; border-left: 1px solid #e8ecf1;
  background: #fff; overflow-y: auto; display: flex; flex-direction: column; gap: 20px;
}
.sp-header { display: flex; justify-content: space-between; align-items: flex-start; }
.sp-header h3 { margin: 0; font-size: 15px; color: #1e293b; }
.sp-overall { text-align: center; }
.spo-value { font-size: 36px; font-weight: 800; color: #3b82f6; line-height: 1; }
.spo-label { font-size: 11px; color: #94a3b8; }

.sp-dimensions { display: flex; flex-direction: column; gap: 14px; }
.sp-dim { display: flex; flex-direction: column; gap: 4px; }
.spd-header { display: flex; justify-content: space-between; align-items: center; }
.spd-label { font-size: 13px; font-weight: 500; color: #475569; }
.spd-score { font-size: 16px; font-weight: 700; }
.spd-score.excellent { color: #22c55e; }
.spd-score.good { color: #3b82f6; }
.spd-score.fair { color: #f59e0b; }
.spd-score.poor { color: #ef4444; }
.spd-bar { height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.spd-fill { height: 100%; border-radius: 3px; transition: width .4s cubic-bezier(0.4,0,0.2,1); }
.spd-comment { font-size: 11px; color: #94a3b8; }

/* 教练提示 */
.sp-hints { border-top: 1px solid #f1f5f9; padding-top: 16px; }
.sph-title { font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 10px; }
.sph-empty { font-size: 12px; color: #cbd5e1; }
.sph-item { display: flex; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f8fafc; font-size: 13px; color: #64748b; line-height: 1.5; }
.sph-num { width: 20px; height: 20px; line-height: 20px; border-radius: 50%; background: #f1f5f9; text-align: center; font-size: 11px; flex-shrink: 0; font-weight: 600; color: #64748b; }

/* ── 报告弹窗 ── */
.report-content { padding: 8px 0; }
.report-hero { text-align: center; padding: 28px; background: linear-gradient(135deg, #eff6ff, #eef2ff); border-radius: 16px; margin-bottom: 20px; }
.rh-label { font-size: 13px; color: #64748b; margin-bottom: 4px; }
.rh-value { font-size: 56px; font-weight: 800; color: #3b82f6; line-height: 1; }
.report-section { margin-top: 16px; }
.report-section h4 { margin: 0 0 8px; font-size: 14px; color: #1e293b; }
.report-section ul { margin: 0; padding-left: 20px; }
.report-section li { font-size: 13px; color: #64748b; line-height: 1.8; }
.report-section p { font-size: 14px; color: #64748b; line-height: 1.6; }

/* ── 进步曲线 ── */
.trend-chart { display: flex; gap: 6px; padding-left: 26px; position: relative; }
.trend-y-axis { position: absolute; left: 0; top: 18px; height: 150px; width: 24px; }
.trend-y-label {
  position: absolute; right: 2px; transform: translateY(-50%);
  font-size: 10px; color: #94a3b8; line-height: 1;
}
.trend-cols { flex: 1; display: flex; gap: 10px; overflow-x: auto; padding-bottom: 2px; }
.trend-col { flex: 1 0 auto; min-width: 52px; display: flex; flex-direction: column; align-items: center; }
.trend-val { height: 18px; line-height: 18px; font-size: 11px; font-weight: 700; color: #10b981; }
.trend-bars {
  height: 150px; width: 100%; display: flex; align-items: flex-end; justify-content: center;
  gap: 3px; border-bottom: 1px solid #e2e8f0; position: relative;
}
.trend-gridline { position: absolute; left: 0; right: 0; height: 1px; background: #f1f5f9; pointer-events: none; }
.trend-bar {
  width: 5px; border-radius: 2px 2px 0 0; min-height: 2px;
  transition: height .4s cubic-bezier(0.4,0,0.2,1);
}
.trend-bar-overall {
  width: 9px; border-radius: 3px 3px 0 0;
  background: linear-gradient(180deg, #10b981, #059669);
}
.trend-round { margin-top: 6px; font-size: 11px; color: #94a3b8; white-space: nowrap; }
.trend-legend { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
.trend-legend-item { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: #64748b; }
.tli-dot { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
.tli-overall { background: linear-gradient(180deg, #10b981, #059669); }
.trend-empty { font-size: 13px; color: #94a3b8; }

/* ── 历史回放（只读） ── */
.replay-banner {
  padding: 10px 24px; background: #ecfdf5; border-bottom: 1px solid #d1fae5;
  font-size: 13px; color: #047857; font-weight: 600;
}
.replay-bar {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 24px; border-top: 1px solid #e8ecf1; background: #fff;
}
.replay-bar-text { flex: 1; font-size: 13px; color: #64748b; }

/* ── Thinking dots ── */
.thinking-dots span { animation: dotPulse 1.5s infinite; }

/* ── 暗色模式 ── */
[data-theme="dark"] .training-page { background: #0f172a; }
[data-theme="dark"] .setup-hero h1 { color: #f1f5f9; }
[data-theme="dark"] .setup-icon-wrap { background: rgba(59,130,246,.1); }
[data-theme="dark"] .customer-card { background: #1e293b; border-color: #334155; }
[data-theme="dark"] .customer-card.selected { border-color: #3b82f6; background: rgba(59,130,246,.08); }
[data-theme="dark"] .cc-name { color: #e2e8f0; }
[data-theme="dark"] .chat-header { background: #1e293b; border-bottom-color: #334155; }
[data-theme="dark"] .cm-content { background: #334155; }
[data-theme="dark"] .cm-hint { background: rgba(250,204,21,.08); border-color: rgba(250,204,21,.15); color: #facc15; }
[data-theme="dark"] .chat-input-bar { background: #1e293b; border-top-color: #334155; }
[data-theme="dark"] .score-panel { background: #1e293b; border-left-color: #334155; }
[data-theme="dark"] .sp-header h3 { color: #e2e8f0; }
[data-theme="dark"] .spd-label { color: #94a3b8; }
[data-theme="dark"] .spd-bar { background: #334155; }
[data-theme="dark"] .sph-item { border-bottom-color: #334155; }
[data-theme="dark"] .sph-num { background: #334155; }
[data-theme="dark"] .sp-hints { border-top-color: #334155; }
[data-theme="dark"] .trend-bars { border-bottom-color: #334155; }
[data-theme="dark"] .trend-gridline { background: #334155; }
[data-theme="dark"] .trend-y-label, [data-theme="dark"] .trend-round, [data-theme="dark"] .trend-legend-item { color: #94a3b8; }
[data-theme="dark"] .replay-banner { background: rgba(16,185,129,.08); border-bottom-color: rgba(16,185,129,.2); color: #34d399; }
[data-theme="dark"] .replay-bar { background: #1e293b; border-top-color: #334155; }
[data-theme="dark"] .replay-bar-text { color: #94a3b8; }

@keyframes dotPulse {
  0%, 20% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}
</style>
