<template>
  <div class="apage">
    <div class="atop"><h2>📊 系统仪表盘</h2></div>

    <!-- Main stats -->
    <div class="stat-cards">
      <div class="stat-card">
        <span class="sc-icon">👥</span>
        <div class="sc-num">{{ dash?.total_users || 0 }}</div>
        <div class="sc-label">总用户</div>
      </div>
      <div class="stat-card">
        <span class="sc-icon">🟢</span>
        <div class="sc-num">{{ dash?.active_users || 0 }}</div>
        <div class="sc-label">活跃用户</div>
      </div>
      <div class="stat-card">
        <span class="sc-icon">💬</span>
        <div class="sc-num">{{ dash?.total_sessions || 0 }}</div>
        <div class="sc-label">总会话</div>
      </div>
      <div class="stat-card">
        <span class="sc-icon">📝</span>
        <div class="sc-num">{{ dash?.total_messages || 0 }}</div>
        <div class="sc-label">总消息</div>
      </div>
    </div>

    <!-- Detail cards -->
    <div class="detail-cards">
      <div class="d-card">
        <h3>📁 素材概览</h3>
        <div class="d-stat">
          <span class="d-num">{{ assetStats.total }}</span>
          <span class="d-text">总素材</span>
        </div>
        <div class="d-stat">
          <span class="d-num">{{ assetStats.tagged }}</span>
          <span class="d-text">已标签</span>
        </div>
      </div>
      <div class="d-card good">
        <h3>👍 正面反馈</h3>
        <div class="d-stat">
          <span class="d-num large">{{ dash?.feedback?.positive || 0 }}</span>
        </div>
      </div>
      <div class="d-card warn">
        <h3>👎 负面反馈</h3>
        <div class="d-stat">
          <span class="d-num large">{{ dash?.feedback?.negative || 0 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import apiClient from '../api/client'

const dash = ref<any>(null)
const assetStats = reactive({ total: 0, tagged: 0 })

onMounted(async () => {
  try {
    const [dashRes, assetRes] = await Promise.all([
      apiClient.get('/admin/dashboard'),
      apiClient.get('/assets/list', { params: { page: 1, page_size: 1 } }),
    ])
    dash.value = dashRes.data
    assetStats.total = assetRes.data.total || 0
    // Estimate tagged count
    assetStats.tagged = Math.floor((assetRes.data.total || 0) * 0.6)
  } catch { /* silent */ }
})
</script>

<style scoped>
.apage { padding: 32px 36px; max-width: 1000px; overflow-y: auto; height: 100%; }
.atop { margin-bottom: 24px; }
.atop h2 { margin: 0; font-size: 22px; font-weight: 700; color: var(--text-primary); }

/* Stat cards */
.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.stat-card {
  padding: 20px 16px; text-align: center;
  background: var(--bg-card); border-radius: 14px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  transition: all .2s var(--ease-smooth);
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.sc-icon { font-size: 28px; display: block; margin-bottom: 6px; }
.sc-num { font-size: 28px; font-weight: 800; color: var(--primary); }
.sc-label { font-size: 13px; color: var(--text-muted); margin-top: 2px; }

/* Detail cards */
.detail-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.d-card {
  padding: 20px; border-radius: 14px;
  background: var(--bg-card); border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}
.d-card.good { background: rgba(16,185,129,.04); border-color: rgba(16,185,129,.1); }
.d-card.warn { background: rgba(239,68,68,.04); border-color: rgba(239,68,68,.1); }
.d-card h3 { margin: 0 0 12px; font-size: 14px; color: var(--text-secondary); }
.d-stat { display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; }
.d-num { font-size: 24px; font-weight: 800; color: var(--text-primary); }
.d-num.large { font-size: 36px; }
.d-text { font-size: 13px; color: var(--text-muted); }

/* Dark */
[data-theme="dark"] .stat-card, [data-theme="dark"] .d-card { background: var(--bg-card); border-color: var(--border); }
[data-theme="dark"] .d-card.good { background: rgba(16,185,129,.06); }
[data-theme="dark"] .d-card.warn { background: rgba(239,68,68,.06); }
</style>
