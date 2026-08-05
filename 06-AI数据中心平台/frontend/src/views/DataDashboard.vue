<template>
  <div class="data-page">
    <!-- 顶部统计卡片 -->
    <header class="data-stats">
      <div class="stat-card">
        <div class="sc-icon">📊</div>
        <div class="sc-value">{{ stats.total }}</div>
        <div class="sc-label">数据集</div>
      </div>
      <div class="stat-card">
        <div class="sc-icon">✅</div>
        <div class="sc-value green">{{ stats.labeled }}</div>
        <div class="sc-label">已标注 (条)</div>
      </div>
      <div class="stat-card">
        <div class="sc-icon">⚡</div>
        <div class="sc-value yellow">{{ stats.processing }}</div>
        <div class="sc-label">处理中</div>
      </div>
      <div class="stat-card">
        <div class="sc-icon">⚠️</div>
        <div class="sc-value red">{{ stats.needsClean }}</div>
        <div class="sc-label">需清洗</div>
      </div>
      <div class="stat-card">
        <div class="sc-icon">📈</div>
        <div class="sc-value blue">{{ stats.monthlyNew }}</div>
        <div class="sc-label">本月新增 (条)</div>
      </div>
    </header>

    <div class="data-body">
      <!-- 数据集列表 -->
      <main class="dataset-list">
        <div class="list-header">
          <h3>📦 数据集</h3>
          <n-button size="small" type="primary">📥 导入数据</n-button>
        </div>

        <div v-if="loading" class="list-loading">⏳ 加载中…</div>

        <div v-else-if="datasets.length === 0" class="list-empty">
          <div class="empty-icon">📦</div>
          <h3>还没有数据集</h3>
          <p>点击"导入数据"开始构建你的数据底座</p>
        </div>

        <div v-for="ds in datasets" :key="ds.id" class="dataset-card" :class="{ selected: selectedId === ds.id }" @click="selectDataset(ds)">
          <div class="ds-main">
            <div class="ds-icon">{{ ds.source && sourceIcon(ds.source) }}</div>
            <div class="ds-info">
              <div class="ds-name">
                {{ ds.name }}
                <n-tag :type="statusType(ds.status)" size="tiny" :bordered="false">{{ statusLabel(ds.status) }}</n-tag>
                <n-tag size="tiny" :bordered="false">v{{ ds.version }}</n-tag>
              </div>
              <div class="ds-meta">
                {{ ds.record_count.toLocaleString() }} 条 · {{ formatSize(ds.file_size) }} · {{ formatDate(ds.created_at) }}
              </div>
              <div class="ds-tags">
                <n-tag v-for="t in (ds.tags || [])" :key="t" size="tiny" :bordered="false">{{ t }}</n-tag>
              </div>
            </div>
          </div>
          <div class="ds-actions">
            <n-button text size="tiny">🔍 详情</n-button>
          </div>
        </div>
      </main>

      <!-- 右侧质量报告 -->
      <aside class="quality-panel">
        <h3>📋 质量概览</h3>
        <div v-if="!selectedDataset" class="qp-empty">选择一个数据集查看质量报告</div>
        <template v-else>
          <div class="quality-bar" v-for="q in qualityMetrics" :key="q.key">
            <div class="qb-header">
              <span>{{ q.label }}</span>
              <span :style="{ color: q.color }">{{ q.value }}%</span>
            </div>
            <n-progress type="line" :percentage="q.value" :color="q.color" :height="6" :border-radius="3" />
          </div>

          <h4 style="margin-top: 20px;">📜 版本历史</h4>
          <div class="version-list">
            <div v-for="v in versions" :key="v.id" class="version-item">
              <div class="vi-tag">v{{ v.version }}</div>
              <div class="vi-info">
                <div class="vi-date">{{ formatDate(v.created_at) }}</div>
                <div class="vi-changes">{{ v.changelog }}</div>
              </div>
            </div>
          </div>
        </template>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import apiClient from '../api/client'

interface Dataset {
  id: string; name: string; description: string; source: string
  record_count: number; file_size: number; status: string
  tags: string[]; version: number; created_at: string; updated_at: string
}
interface Version { id: string; version: number; created_at: string; changelog: string }

const loading = ref(false)
const datasets = ref<Dataset[]>([])
const selectedId = ref('')
const selectedDataset = ref<Dataset | null>(null)
const versions = ref<Version[]>([])

const stats = reactive({ total: 0, labeled: 0, processing: 0, needsClean: 0, monthlyNew: 0 })

const qualityMetrics = reactive([
  { key: 'accuracy', label: '标签准确率', value: 96, color: '#10b981' },
  { key: 'completeness', label: '数据完整率', value: 88, color: '#f59e0b' },
  { key: 'duplication', label: '去重率', value: 88, color: '#667eea' },
  { key: 'anomaly', label: '异常率', value: 3, color: '#ef4444' },
])

function sourceIcon(s: string): string {
  const m: Record<string, string> = { 'rag客服': '💬', '自媒体助手': '✍️', '脚本工坊': '🎬', '素材管理': '🖼️', '销售培训': '🎯' }
  return m[s] || '📊'
}
function statusType(s: string): 'success' | 'warning' | 'info' | 'error' {
  const m: Record<string, 'success' | 'warning' | 'info' | 'error'> = { ready: 'success', cleaning: 'warning', labeling: 'info', collecting: 'error', completed: 'success' }
  return m[s] || 'info'
}
function statusLabel(s: string): string {
  const m: Record<string, string> = { ready: '✅ 就绪', cleaning: '🔄 清洗中', labeling: '🏷️ 标注中', collecting: '⏳ 采集中', completed: '✅ 完成' }
  return m[s] || s
}
function formatSize(b: number): string {
  if (!b) return '0 B'
  const u = ['B', 'KB', 'MB', 'GB']; let i = 0, s = b
  while (s >= 1024 && i < 3) { s /= 1024; i++ }
  return s.toFixed(1) + ' ' + u[i]
}
function formatDate(d: string): string {
  return d ? new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' }) : ''
}

function selectDataset(ds: Dataset) {
  selectedId.value = ds.id; selectedDataset.value = ds
  // Mock versions
  versions.value = [
    { id: '1', version: ds.version || 3, created_at: ds.created_at, changelog: '新增数据 + 清洗去重' },
    { id: '2', version: (ds.version || 3) - 1, created_at: new Date(Date.now() - 14*864e5).toISOString(), changelog: '清洗去重，移除空值' },
    { id: '3', version: (ds.version || 3) - 2, created_at: new Date(Date.now() - 30*864e5).toISOString(), changelog: '初始采集版本' },
  ]
}

async function loadData() {
  loading.value = true
  try {
    // For now use mock data — in production load from API
    datasets.value = [
      { id: '1', name: '电商客服对话', description: '', source: 'rag客服', record_count: 12500, file_size: 8.3*1024*1024, status: 'ready', tags: ['客服', '对话', '已标注'], version: 3, created_at: '2024-08-01T10:00:00Z', updated_at: '2024-08-01T10:00:00Z' },
      { id: '2', name: '商品评论数据', description: '', source: '自媒体助手', record_count: 8200, file_size: 5.1*1024*1024, status: 'labeling', tags: ['评论', '情感分析'], version: 2, created_at: '2024-07-28T10:00:00Z', updated_at: '2024-07-28T10:00:00Z' },
      { id: '3', name: '产品FAQ数据', description: '', source: '脚本工坊', record_count: 3400, file_size: 2.2*1024*1024, status: 'collecting', tags: ['FAQ', '产品'], version: 1, created_at: '2024-07-20T10:00:00Z', updated_at: '2024-07-20T10:00:00Z' },
    ]
    stats.total = datasets.value.length
    stats.labeled = 12500
    stats.processing = 8200
    stats.needsClean = 3400
    stats.monthlyNew = 2100
  } finally {
    loading.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.data-page { display: flex; flex-direction: column; height: 100%; background: #fff; }
.data-stats { display: flex; gap: 12px; padding: 16px 24px; border-bottom: 1px solid #f0f0f0; flex-shrink: 0; }
.stat-card { flex: 1; text-align: center; padding: 12px; background: #fafbfd; border-radius: 10px; }
.sc-icon { font-size: 24px; margin-bottom: 4px; }
.sc-value { font-size: 22px; font-weight: 700; color: #333; }
.sc-value.green { color: #10b981; }
.sc-value.yellow { color: #f59e0b; }
.sc-value.red { color: #ef4444; }
.sc-value.blue { color: #667eea; }
.sc-label { font-size: 12px; color: #999; margin-top: 2px; }

.data-body { flex: 1; display: flex; min-height: 0; }
.dataset-list { flex: 1; overflow-y: auto; padding: 16px 24px; border-right: 1px solid #f0f0f0; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.list-header h3 { margin: 0; font-size: 16px; }
.list-loading, .list-empty { text-align: center; padding: 60px 20px; color: #999; }
.empty-icon { font-size: 48px; margin-bottom: 8px; }

.dataset-card { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; margin-bottom: 6px; background: #fafbfd; border-radius: 10px; border: 2px solid transparent; cursor: pointer; transition: all .15s; }
.dataset-card:hover { border-color: #e0e3ee; }
.dataset-card.selected { border-color: #667eea; background: #f0f2fb; }
.ds-main { display: flex; gap: 12px; }
.ds-icon { font-size: 28px; }
.ds-name { font-size: 14px; font-weight: 600; color: #333; display: flex; align-items: center; gap: 6px; }
.ds-meta { font-size: 12px; color: #999; margin: 2px 0 4px; }
.ds-tags { display: flex; gap: 4px; }

.quality-panel { width: 300px; min-width: 300px; padding: 16px; overflow-y: auto; background: #fafbfd; }
.quality-panel h3 { margin: 0 0 16px; font-size: 16px; }
.qp-empty { text-align: center; padding: 40px 10px; color: #ccc; font-size: 13px; }
.quality-bar { margin-bottom: 14px; }
.qb-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }

.version-list { margin-top: 8px; }
.version-item { display: flex; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.vi-tag { font-size: 12px; font-weight: 700; color: #667eea; min-width: 28px; }
.vi-date { font-size: 11px; color: #999; }
.vi-changes { font-size: 13px; color: #555; }

[data-theme="dark"] .data-page { background: #101014; }
[data-theme="dark"] .data-stats { border-bottom-color: #222; }
[data-theme="dark"] .stat-card { background: #1a1a24; }
[data-theme="dark"] .sc-value { color: #ddd; }
[data-theme="dark"] .dataset-list { border-right-color: #222; }
[data-theme="dark"] .dataset-card { background: #1a1a24; }
[data-theme="dark"] .dataset-card:hover { border-color: #333; }
[data-theme="dark"] .dataset-card.selected { border-color: #667eea; background: #1e1e30; }
[data-theme="dark"] .ds-name { color: #ddd; }
[data-theme="dark"] .quality-panel { background: #14141a; }
[data-theme="dark"] .version-item { border-bottom-color: #2a2a38; }
[data-theme="dark"] .vi-changes { color: #aaa; }
</style>
