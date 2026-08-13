<template>
  <div class="history-panel">
    <div class="hp-header">
      <h3>📋 训练记录</h3>
      <n-button size="small" quaternary @click="$emit('close')">✕</n-button>
    </div>

    <!-- Stats -->
    <div class="hp-stats" v-if="sessions.length > 0">
      <div class="stat-card">
        <div class="stat-val">{{ sessions.length }}</div>
        <div class="stat-label">总训练次数</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{{ avgScore }}</div>
        <div class="stat-label">平均分</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{{ bestScore }}</div>
        <div class="stat-label">最高分</div>
      </div>
    </div>

    <!-- Filter -->
    <div class="hp-filter" v-if="sessions.length > 0">
      <n-select
        v-model:value="filterType"
        :options="filterOptions"
        placeholder="筛选客户类型"
        clearable
        size="small"
        style="width: 160px;"
      />
    </div>

    <!-- List -->
    <div class="hp-list" v-if="filteredSessions.length > 0">
      <div
        v-for="s in filteredSessions"
        :key="s.id"
        class="hp-item"
        @click="$emit('select', s.id)"
      >
        <div class="hpi-left">
          <span class="hpi-icon">{{ typeIcon(s.customer_type) }}</span>
          <div>
            <div class="hpi-title">{{ typeName(s.customer_type) }}</div>
            <div class="hpi-meta">
              {{ s.total_rounds }} 轮 · {{ formatDate(s.created_at) }}
              <n-tag :type="s.status === 'completed' ? 'success' : 'info'" size="tiny" style="margin-left: 4px;">
                {{ s.status === 'completed' ? '已完成' : '进行中' }}
              </n-tag>
            </div>
          </div>
        </div>
        <div class="hpi-right">
          <span class="hpi-score" :class="scoreColor(s.overall_score)">
            {{ s.overall_score ?? '-' }}
          </span>
        </div>
      </div>
    </div>

    <div class="hp-empty" v-else>
      <div class="hpe-icon">🎯</div>
      <p>还没有训练记录</p>
      <p class="hpe-sub">开始你的第一次销售对练吧！</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { trainingApi, type TrainingSession } from '../api/training'

defineEmits<{
  select: [sessionId: string]
  close: []
}>()

const sessions = ref<TrainingSession[]>([])
const filterType = ref<string | null>(null)
const filterOptions = [
  { label: '🧐 挑剔型', value: 'picky' },
  { label: '💰 价格敏感型', value: 'price' },
  { label: '🤔 犹豫型', value: 'hesitant' },
  { label: '🎓 专业型', value: 'expert' },
]

const typeMap: Record<string, string> = { picky: '挑剔型', price: '价格敏感型', hesitant: '犹豫型', expert: '专业型' }
const iconMap: Record<string, string> = { picky: '🧐', price: '💰', hesitant: '🤔', expert: '🎓' }

function typeName(t: string) { return typeMap[t] || t }
function typeIcon(t: string) { return iconMap[t] || '🎯' }
function scoreColor(s: number | null) {
  if (!s) return ''
  if (s >= 80) return 'excellent'
  if (s >= 60) return 'good'
  if (s >= 40) return 'fair'
  return 'poor'
}
function formatDate(d: string) {
  const date = new Date(d)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

const filteredSessions = computed(() => {
  if (!filterType.value) return sessions.value
  return sessions.value.filter(s => s.customer_type === filterType.value)
})

const avgScore = computed(() => {
  const scores = sessions.value.map(s => s.overall_score).filter(Boolean) as number[]
  return scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : '-'
})

const bestScore = computed(() => {
  const scores = sessions.value.map(s => s.overall_score).filter(Boolean) as number[]
  return scores.length ? Math.max(...scores) : '-'
})

onMounted(async () => {
  try {
    const res = await trainingApi.listSessions(1, 50)
    sessions.value = res.data.filter(s => s.status !== 'deleted')
  } catch {}
})
</script>

<style scoped>
.history-panel { padding: 4px 0; }
.hp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.hp-header h3 { margin: 0; font-size: 16px; }

.hp-stats { display: flex; gap: 8px; margin-bottom: 16px; }
.stat-card { flex: 1; text-align: center; padding: 10px 8px; background: #f8fdfb; border-radius: 10px; }
.stat-val { font-size: 22px; font-weight: 700; color: #10b981; }
.stat-label { font-size: 11px; color: #999; margin-top: 2px; }

.hp-filter { margin-bottom: 12px; }

.hp-list { max-height: 400px; overflow-y: auto; }
.hp-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 12px; border-radius: 10px; cursor: pointer;
  transition: background .15s; margin-bottom: 4px;
}
.hp-item:hover { background: #f0fdf5; }
.hpi-left { display: flex; align-items: center; gap: 10px; }
.hpi-icon { font-size: 24px; }
.hpi-title { font-size: 14px; font-weight: 600; color: #333; }
.hpi-meta { font-size: 11px; color: #999; margin-top: 2px; }
.hpi-score { font-size: 20px; font-weight: 700; }
.hpi-score.excellent { color: #10b981; }
.hpi-score.good { color: #059669; }
.hpi-score.fair { color: #f59e0b; }
.hpi-score.poor { color: #ef4444; }

.hp-empty { text-align: center; padding: 40px 20px; }
.hpe-icon { font-size: 48px; margin-bottom: 12px; }
.hp-empty p { color: #666; margin: 0; font-size: 14px; }
.hpe-sub { color: #aaa; font-size: 12px; margin-top: 4px; }

[data-theme="dark"] .stat-card { background: #1a2a22; }
[data-theme="dark"] .hp-item:hover { background: #0a2e1f; }
[data-theme="dark"] .hpi-title { color: #ddd; }
[data-theme="dark"] .hp-empty p { color: #888; }
</style>
