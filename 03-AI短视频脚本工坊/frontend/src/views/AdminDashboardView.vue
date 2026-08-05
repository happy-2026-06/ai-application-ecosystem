<template>
  <div class="apage">
    <PageHeader title="系统仪表盘" subtitle="平台使用数据概览" />

    <!-- Stats row -->
    <div class="stats-row">
      <div class="stat-card" v-for="(s, i) in stats" :key="s.label" :class="'stat-accent-' + (i+1)">
        <div class="stat-value">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- Secondary row -->
    <div class="secondary-row">
      <div class="sec-card">
        <h4>📚 知识库概况</h4>
        <div class="sec-stats">
          <div class="sec-stat">
            <span class="ss-value">{{ dash?.total_documents || 0 }}</span>
            <span class="ss-label">文档总数</span>
          </div>
          <div class="sec-stat">
            <span class="ss-value">{{ dash?.total_chunks || 0 }}</span>
            <span class="ss-label">总片段数</span>
          </div>
        </div>
      </div>

      <div class="sec-card feedback-positive">
        <h4>👍 正面反馈</h4>
        <div class="sec-stat single">
          <span class="ss-value large">{{ dash?.feedback?.positive || 0 }}</span>
        </div>
      </div>

      <div class="sec-card feedback-negative">
        <h4>👎 负面反馈</h4>
        <div class="sec-stat single">
          <span class="ss-value large">{{ dash?.feedback?.negative || 0 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '../api/client'
import { useMessage } from 'naive-ui'
import PageHeader from '../components/PageHeader.vue'

const message = useMessage()
const dash = ref<any>(null)

const stats = computed(() => [
  { label: '总用户', value: dash.value?.total_users || 0 },
  { label: '活跃用户', value: dash.value?.active_users || 0 },
  { label: '总会话', value: dash.value?.total_sessions || 0 },
  { label: '总消息', value: dash.value?.total_messages || 0 },
])

onMounted(async () => {
  try {
    const r = await apiClient.get('/admin/dashboard')
    dash.value = r.data
  } catch { message.error('加载仪表盘失败') }
})
</script>

<style scoped>
.apage { padding: 28px 32px; max-width: 960px; overflow-y: auto; height: 100%; }

/* Stats row */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.stat-card {
  background: var(--bg-card); border-radius: var(--radius);
  padding: 22px 20px; text-align: center;
  box-shadow: var(--shadow-sm);
  border-top: 3px solid var(--primary);
  transition: transform .2s;
}
.stat-card:hover { transform: translateY(-2px); }
.stat-accent-1 { border-top-color: #C8A951; }
.stat-accent-2 { border-top-color: #E8A840; }
.stat-accent-3 { border-top-color: #7FB8A0; }
.stat-accent-4 { border-top-color: #C08060; }
.stat-value { font-size: 28px; font-weight: 800; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; text-transform: uppercase; letter-spacing: .5px; }

/* Secondary row */
.secondary-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.sec-card {
  background: var(--bg-card); border-radius: var(--radius);
  padding: 20px; box-shadow: var(--shadow-sm);
}
.sec-card h4 { margin: 0 0 14px; font-size: 15px; color: var(--text-primary); }
.sec-stats { display: flex; gap: 20px; }
.sec-stat { text-align: center; }
.sec-stat.single { display: flex; justify-content: center; }
.ss-value { font-size: 24px; font-weight: 700; color: var(--text-primary); display: block; }
.ss-value.large { font-size: 36px; }
.ss-label { font-size: 12px; color: var(--text-secondary); }
.feedback-positive { border-left: 3px solid #22C55E; }
.feedback-negative { border-left: 3px solid #EF4444; }

/* Dark mode */
[data-theme="dark"] .stat-card { background: #1A1A25; }
[data-theme="dark"] .stat-value { color: #E8E8F0; }
[data-theme="dark"] .sec-card { background: #1A1A25; }
[data-theme="dark"] .sec-card h4 { color: #E8E8F0; }
[data-theme="dark"] .ss-value { color: #E8E8F0; }
</style>
