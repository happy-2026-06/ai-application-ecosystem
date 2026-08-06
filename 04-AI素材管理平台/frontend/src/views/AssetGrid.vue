<template>
  <div class="asset-page">
    <!-- 顶部搜索栏 -->
    <header class="asset-topbar">
      <div class="topbar-left">
        <h2>🖼️ 素材管理</h2>
      </div>
      <div class="topbar-search">
        <n-input
          v-model:value="searchText"
          placeholder="搜索素材 — 试试输入夕阳、城市…"
          clearable
          size="large"
          round
          @keydown.enter="handleSearch"
        >
          <template #prefix>
            <span>🔍</span>
          </template>
        </n-input>
        <n-button-group style="margin-left: 8px;">
          <n-button :type="searchMode === 'text' ? 'primary' : 'default'" @click="searchMode = 'text'">📝 文搜图</n-button>
          <n-button :type="searchMode === 'image' ? 'primary' : 'default'" @click="searchMode = 'image'">🖼️ 图搜图</n-button>
        </n-button-group>
      </div>
      <div class="topbar-actions">
        <n-upload multiple :show-file-list="false" @change="handleUpload as any">
          <n-button type="primary" size="large">📤 上传素材</n-button>
        </n-upload>
      </div>
    </header>

    <div class="asset-body">
      <!-- 左侧标签筛选 -->
      <aside class="asset-filters">
        <div class="filter-section">
          <h4>📂 文件类型</h4>
          <n-space vertical>
            <n-button text :type="fileTypeFilter === '' ? 'primary' : 'default'" @click="fileTypeFilter = ''">全部</n-button>
            <n-button text :type="fileTypeFilter === 'image' ? 'primary' : 'default'" @click="fileTypeFilter = 'image'">🖼️ 图片</n-button>
            <n-button text :type="fileTypeFilter === 'video' ? 'primary' : 'default'" @click="fileTypeFilter = 'video'">🎬 视频</n-button>
            <n-button text :type="fileTypeFilter === 'document' ? 'primary' : 'default'" @click="fileTypeFilter = 'document'">📄 文档</n-button>
          </n-space>
        </div>
        <div class="filter-section">
          <h4>🏷️ 热门标签</h4>
          <div class="tag-cloud">
            <n-tag
              v-for="tag in popularTags"
              :key="tag"
              :type="tagFilter === tag ? 'primary' : 'default'"
              closable
              @click="tagFilter = tagFilter === tag ? '' : tag"
              @close="tagFilter = ''"
              style="cursor: pointer; margin: 4px;"
            >
              {{ tag }}
            </n-tag>
          </div>
        </div>
        <div class="filter-section">
          <h4>📊 统计</h4>
          <div class="stats-mini">
            <div class="stat-item">
              <span class="stat-num">{{ stats.total }}</span>
              <span class="stat-label">总素材</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ stats.tagged }}</span>
              <span class="stat-label">已标签</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ stats.totalSize }}</span>
              <span class="stat-label">总大小</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 素材网格 -->
      <main class="asset-grid-area">
        <!-- 加载中 -->
        <div v-if="loading" class="grid-loading">
          <div class="loading-icon">⏳</div>
          <p>加载素材中…</p>
        </div>

        <!-- 空状态 -->
        <div v-else-if="assets.length === 0" class="grid-empty">
          <div class="empty-icon">📁</div>
          <h2>还没有素材</h2>
          <p>点击右上角"上传素材"开始管理你的数字资产</p>
          <div class="feature-hints">
            <div class="hint-card">
              <div class="hc-icon">🏷️</div>
              <div>AI 自动打标签</div>
            </div>
            <div class="hint-card">
              <div class="hc-icon">🔍</div>
              <div>自然语言搜索</div>
            </div>
            <div class="hint-card">
              <div class="hc-icon">📋</div>
              <div>版本管理</div>
            </div>
          </div>
        </div>

        <!-- 素材网格 -->
        <div v-else class="asset-grid">
          <div
            v-for="asset in assets"
            :key="asset.id"
            class="asset-card"
            :class="{ selected: selectedId === asset.id }"
            @click="selectAsset(asset)"
          >
            <div class="ac-thumb">
              <div class="ac-type-icon">{{ typeIcon(asset.file_type) }}</div>
            </div>
            <div class="ac-info">
              <div class="ac-name" :title="asset.filename">{{ asset.filename }}</div>
              <div class="ac-meta">{{ formatSize(asset.file_size) }}</div>
              <div class="ac-tags">
                <n-tag
                  v-for="t in (asset.ai_tags || asset.tags || ['未分类']).slice(0, 3)"
                  :key="t"
                  size="tiny"
                  :bordered="false"
                >{{ t }}</n-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="grid-pagination">
          <n-pagination
            v-model:page="currentPage"
            :page-count="totalPages"
            @update:page="loadAssets"
          />
        </div>
      </main>

      <!-- 右侧详情面板 (选中素材时出现) -->
      <aside v-if="selectedAsset" class="asset-detail">
        <div class="detail-header">
          <h3>{{ selectedAsset.filename }}</h3>
          <n-button text @click="selectedAsset = null; selectedId = ''">✕</n-button>
        </div>
        <div class="detail-thumb">
          <div class="dt-icon">{{ typeIcon(selectedAsset.file_type) }}</div>
          <div class="dt-size">{{ formatSize(selectedAsset.file_size) }}</div>
        </div>
        <div class="detail-section">
          <h4>🏷️ AI 智能标签</h4>
          <div class="tag-list">
            <n-tag v-for="t in selectedAsset.ai_tags || []" :key="t" type="info" size="small">{{ t }}</n-tag>
            <span v-if="!(selectedAsset.ai_tags || []).length" class="no-data">处理中…</span>
          </div>
        </div>
        <div class="detail-section">
          <h4>📝 手动标签</h4>
          <div class="tag-list">
            <n-tag v-for="t in selectedAsset.tags || []" :key="t" type="success" size="small">{{ t }}</n-tag>
            <span v-if="!(selectedAsset.tags || []).length" class="no-data">暂无</span>
          </div>
        </div>
        <div class="detail-section">
          <h4>📋 基本信息</h4>
          <div class="info-row"><span>类型</span><span>{{ selectedAsset.file_type }}</span></div>
          <div class="info-row"><span>大小</span><span>{{ formatSize(selectedAsset.file_size) }}</span></div>
          <div class="info-row"><span>版本</span><span>v{{ selectedAsset.version }}</span></div>
          <div class="info-row"><span>上传时间</span><span>{{ formatDate(selectedAsset.created_at) }}</span></div>
        </div>
        <div class="detail-actions">
          <n-button block size="small" @click="handleDownload(selectedAsset)">⬇ 下载</n-button>
          <n-button block size="small" type="error" @click="handleDelete(selectedAsset)" style="margin-top: 8px;">🗑 删除</n-button>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import apiClient from '../api/client'

interface AssetItem {
  id: string
  filename: string
  file_type: string
  file_size: number
  tags: string[]
  ai_tags: string[]
  ai_description: string | null
  thumbnail_path: string | null
  status: string
  version: number
  created_at: string
}

const message = useMessage()

const searchText = ref('')
const searchMode = ref('text')
const fileTypeFilter = ref('')
const tagFilter = ref('')
const loading = ref(false)
const assets = ref<AssetItem[]>([])
const selectedId = ref('')
const selectedAsset = ref<AssetItem | null>(null)
const currentPage = ref(1)
const totalPages = ref(1)

const popularTags = ['夕阳', '城市', '海滩', '汽车', '美食', '人物', '建筑', '风景', '产品']

const stats = reactive({ total: 0, tagged: 0, totalSize: '' })

function typeIcon(type: string): string {
  if (type.startsWith('image')) return '🖼️'
  if (type.startsWith('video')) return '🎬'
  if (type.startsWith('document')) return '📄'
  return '📁'
}

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return `${size.toFixed(1)} ${units[i]}`
}

function formatDate(d: string): string {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

async function loadAssets() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: currentPage.value, page_size: 24 }
    if (fileTypeFilter.value) params.file_type = fileTypeFilter.value
    if (tagFilter.value) params.tag = tagFilter.value
    if (searchText.value) params.search = searchText.value

    const res = await apiClient.get('/assets/list', { params })
    assets.value = res.data.items
    totalPages.value = Math.ceil(res.data.total / 24)
    stats.total = res.data.total
    stats.tagged = res.data.items.filter((a: AssetItem) => (a.ai_tags || []).length > 0).length
  } catch (e) {
    console.error('Load assets failed:', e)
  } finally {
    loading.value = false
  }
}

function handleSearch() { currentPage.value = 1; loadAssets() }
function selectAsset(asset: AssetItem) { selectedId.value = asset.id; selectedAsset.value = asset }

async function handleUpload(options: { file: File; fileList: File[] }) {
  const form = new FormData()
  form.append('file', options.file)
  try {
    await apiClient.post('/assets/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    message.success('上传成功，AI 正在生成标签…')
    loadAssets()
  } catch (e: any) {
    message.error('上传失败: ' + (e.response?.data?.detail || e.message))
  }
}

function handleDownload(asset: AssetItem) {
  message.info('下载功能需要配合对象存储(MinIO)使用')
}

async function handleDelete(asset: AssetItem) {
  try {
    await apiClient.delete(`/assets/${asset.id}`)
    message.success('已删除')
    selectedAsset.value = null
    selectedId.value = ''
    loadAssets()
  } catch (e: any) {
    message.error('删除失败')
  }
}

onMounted(() => loadAssets())
</script>

<style scoped>
.asset-page { display: flex; flex-direction: column; height: 100%; background: #fff; }

/* 顶部栏 */
.asset-topbar {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 24px; border-bottom: 1px solid #f0f0f0; flex-shrink: 0;
  background: #fafbfd;
}
.topbar-left h2 { margin: 0; font-size: 18px; white-space: nowrap; }
.topbar-search { flex: 1; display: flex; align-items: center; max-width: 600px; }
.topbar-actions { flex-shrink: 0; }

/* 主体 */
.asset-body { flex: 1; display: flex; min-height: 0; overflow: hidden; }

/* 左侧筛选 */
.asset-filters {
  width: 200px; min-width: 200px; padding: 16px;
  border-right: 1px solid #eef0f4; overflow-y: auto;
  background: #f8f9fb;
}
.filter-section { margin-bottom: 20px; }
.filter-section h4 { margin: 0 0 8px; font-size: 13px; color: #888; font-weight: 600; text-transform: uppercase; }
.tag-cloud { display: flex; flex-wrap: wrap; gap: 2px; }
.stats-mini { display: flex; flex-wrap: wrap; gap: 8px; }
.stat-item { flex: 1; min-width: 60px; text-align: center; padding: 8px; background: #fff; border-radius: 8px; }
.stat-num { display: block; font-size: 18px; font-weight: 700; color: #667eea; }
.stat-label { display: block; font-size: 11px; color: #999; margin-top: 2px; }

/* 素材网格 */
.asset-grid-area { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
.grid-loading, .grid-empty {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.empty-icon, .loading-icon { font-size: 56px; margin-bottom: 12px; }
.grid-empty h2 { margin: 0 0 4px; font-size: 20px; color: #333; }
.grid-empty p { color: #999; font-size: 14px; margin: 0 0 24px; }
.feature-hints { display: flex; gap: 12px; }
.hint-card { padding: 12px 20px; background: #f5f6fa; border-radius: 10px; text-align: center; font-size: 13px; color: #666; }
.hc-icon { font-size: 24px; margin-bottom: 4px; }

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.asset-card {
  background: #fafbfd; border-radius: 12px; overflow: hidden;
  border: 2px solid transparent; cursor: pointer; transition: all .15s;
}
.asset-card:hover { border-color: #e0e3ee; transform: translateY(-1px); }
.asset-card.selected { border-color: #667eea; background: #f0f2fb; }
.ac-thumb {
  height: 120px; background: linear-gradient(135deg, #667eea15, #7c3aed10);
  display: flex; align-items: center; justify-content: center;
}
.ac-type-icon { font-size: 40px; }
.ac-info { padding: 10px 12px; }
.ac-name {
  font-size: 13px; font-weight: 600; color: #333;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ac-meta { font-size: 11px; color: #aaa; margin: 2px 0 6px; }
.ac-tags { display: flex; flex-wrap: wrap; gap: 3px; }

.grid-pagination { display: flex; justify-content: center; padding: 16px 0; }

/* 右侧详情 */
.asset-detail {
  width: 280px; min-width: 280px; border-left: 1px solid #eef0f4;
  padding: 16px; overflow-y: auto; background: #fafbfd;
}
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.detail-header h3 { margin: 0; font-size: 15px; word-break: break-word; }
.detail-thumb {
  height: 160px; background: linear-gradient(135deg, #667eea15, #7c3aed10);
  border-radius: 10px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; margin-bottom: 16px;
}
.dt-icon { font-size: 48px; }
.dt-size { font-size: 13px; color: #999; margin-top: 4px; }
.detail-section { margin-bottom: 16px; }
.detail-section h4 { margin: 0 0 8px; font-size: 13px; color: #888; }
.tag-list { display: flex; flex-wrap: wrap; gap: 4px; }
.no-data { font-size: 12px; color: #ccc; }
.info-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; border-bottom: 1px solid #f0f0f0; }
.info-row span:first-child { color: #999; }
.info-row span:last-child { color: #333; font-weight: 500; }
.detail-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #eef0f4; }

/* 暗色模式 */
[data-theme="dark"] .asset-page { background: #101014; }
[data-theme="dark"] .asset-topbar { background: #16161d; border-bottom-color: #222; }
[data-theme="dark"] .asset-filters { background: #14141a; border-right-color: #222; }
[data-theme="dark"] .asset-detail { background: #14141a; border-left-color: #222; }
[data-theme="dark"] .stat-item { background: #1e1e28; }
[data-theme="dark"] .stat-num { color: #8899ee; }
[data-theme="dark"] .asset-card { background: #1a1a24; }
[data-theme="dark"] .asset-card:hover { border-color: #333; }
[data-theme="dark"] .asset-card.selected { border-color: #667eea; background: #1e1e30; }
[data-theme="dark"] .ac-name { color: #ddd; }
[data-theme="dark"] .grid-empty h2 { color: #ddd; }
[data-theme="dark"] .detail-header h3 { color: #ddd; }
[data-theme="dark"] .info-row span:last-child { color: #ccc; }
[data-theme="dark"] .hint-card { background: #1e1e28; color: #aaa; }
</style>
