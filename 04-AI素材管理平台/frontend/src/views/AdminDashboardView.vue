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
        <span class="sc-icon">🗂️</span>
        <div class="sc-num">{{ dash?.total_assets || 0 }}</div>
        <div class="sc-label">总素材</div>
      </div>
      <div class="stat-card">
        <span class="sc-icon">🏷️</span>
        <div class="sc-num">{{ dash?.tagged_assets || 0 }}</div>
        <div class="sc-label">已标签</div>
      </div>
    </div>

    <!-- Asset detail cards -->
    <div class="detail-cards">
      <div class="d-card">
        <h3>📁 素材概览</h3>
        <div class="d-stat">
          <span class="d-num">{{ dash?.ready_assets || 0 }}</span>
          <span class="d-text">✅ 就绪</span>
        </div>
        <div class="d-stat">
          <span class="d-num">{{ dash?.processing_assets || 0 }}</span>
          <span class="d-text">⏳ 处理中</span>
        </div>
        <div class="d-stat">
          <span class="d-num large">{{ dash?.tagged_percentage || 0 }}%</span>
          <span class="d-text">标签覆盖率</span>
        </div>
      </div>
      <div class="d-card">
        <h3>💾 存储概览</h3>
        <div class="d-stat">
          <span class="d-num large">{{ formatSize(dash?.total_storage_bytes || 0) }}</span>
          <span class="d-text">总存储量</span>
        </div>
        <div v-if="dash?.assets_by_type" class="type-bars">
          <div v-for="(count, type) in dash.assets_by_type" :key="type" class="type-bar-row">
            <span class="type-label">{{ typeLabel(type) }}</span>
            <div class="type-bar-track">
              <div class="type-bar-fill" :style="{ width: pctOfTotal(count) + '%' }" />
            </div>
            <span class="type-count">{{ count }}</span>
          </div>
        </div>
      </div>
      <div class="d-card">
        <h3>💬 用户反馈</h3>
        <div class="d-stat good">
          <span class="d-num">{{ dash?.feedback?.positive || 0 }}</span>
          <span class="d-text">👍 正面反馈</span>
        </div>
        <div class="d-stat warn">
          <span class="d-num">{{ dash?.feedback?.negative || 0 }}</span>
          <span class="d-text">👎 负面反馈</span>
        </div>
        <div class="d-stat">
          <span class="d-num">{{ dash?.total_sessions || 0 }}</span>
          <span class="d-text">📋 总会话</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../api/client'

const dash = ref<any>(null)

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0; let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return `${size.toFixed(1)} ${units[i]}`
}

function typeLabel(type: string): string {
  const map: Record<string, string> = { image: '🖼️ 图片', video: '🎬 视频', document: '📄 文档' }
  return map[type] || type
}

function pctOfTotal(count: number): number {
  const total = dash.value?.total_assets || 1
  return Math.round((count / total) * 100)
}

onMounted(async () => {
  try {
    const res = await apiClient.get('/admin/dashboard')
    dash.value = res.data
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
.d-card h3 { margin: 0 0 12px; font-size: 14px; color: var(--text-secondary); }
.d-stat { display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; }
.d-stat.good { color: #10B981; }
.d-stat.warn { color: #F59E0B; }
.d-num { font-size: 24px; font-weight: 800; color: var(--text-primary); }
.d-stat.good .d-num { color: #10B981; }
.d-stat.warn .d-num { color: #F59E0B; }
.d-num.large { font-size: 36px; }
.d-text { font-size: 13px; color: var(--text-muted); }

/* Type bars */
.type-bars { margin-top: 8px; }
.type-bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 12px; }
.type-label { width: 70px; color: var(--text-secondary); flex-shrink: 0; }
.type-bar-track { flex: 1; height: 8px; background: var(--bg-surface); border-radius: 4px; overflow: hidden; }
.type-bar-fill { height: 100%; background: var(--primary-gradient); border-radius: 4px; transition: width .5s var(--ease-smooth); }
.type-count { width: 30px; text-align: right; color: var(--text-primary); font-weight: 600; }

/* Dark */
[data-theme="dark"] .stat-card, [data-theme="dark"] .d-card { background: var(--bg-card); border-color: var(--border); }
</style>
