<template>
  <div class="asset-page">
    <!-- 顶部搜索栏 -->
    <header class="asset-topbar">
      <div class="topbar-left">
        <h2>🗂️ 素材管理</h2>
        <span class="topbar-count" v-if="!loading">共 {{ stats.total }} 个素材</span>
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
          <template #prefix><span>🔍</span></template>
        </n-input>
        <n-button-group style="margin-left: 8px;">
          <n-button :type="searchMode === 'text' ? 'primary' : 'default'" @click="searchMode = 'text'">📝 文搜图</n-button>
          <n-button :type="searchMode === 'image' ? 'primary' : 'default'" @click="searchMode = 'image'">🖼️ 图搜图</n-button>
        </n-button-group>
      </div>
      <div class="topbar-actions">
        <n-button-group style="margin-right: 8px;">
          <n-button :type="sortBy === 'date' ? 'primary' : 'default'" size="small" @click="sortBy = 'date'; loadAssets()">🕐 时间</n-button>
          <n-button :type="sortBy === 'name' ? 'primary' : 'default'" size="small" @click="sortBy = 'name'; loadAssets()">📋 名称</n-button>
          <n-button :type="sortBy === 'size' ? 'primary' : 'default'" size="small" @click="sortBy = 'size'; loadAssets()">📦 大小</n-button>
        </n-button-group>
        <n-upload multiple :show-file-list="false" @change="handleUpload as any">
          <n-button type="primary" size="large" class="upload-btn">📤 上传素材</n-button>
        </n-upload>
      </div>
    </header>

    <div class="asset-body">
      <!-- 左侧标签筛选 -->
      <aside class="asset-filters">
        <div class="filter-section">
          <h4>📂 文件类型</h4>
          <n-space vertical>
            <n-button text :type="fileTypeFilter === '' ? 'primary' : 'default'" @click="fileTypeFilter = ''; loadAssets()">全部</n-button>
            <n-button text :type="fileTypeFilter === 'image' ? 'primary' : 'default'" @click="fileTypeFilter = 'image'; loadAssets()">🖼️ 图片</n-button>
            <n-button text :type="fileTypeFilter === 'video' ? 'primary' : 'default'" @click="fileTypeFilter = 'video'; loadAssets()">🎬 视频</n-button>
            <n-button text :type="fileTypeFilter === 'document' ? 'primary' : 'default'" @click="fileTypeFilter = 'document'; loadAssets()">📄 文档</n-button>
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
              @click="tagFilter = tagFilter === tag ? '' : tag; loadAssets()"
              @close="tagFilter = ''; loadAssets()"
              style="cursor: pointer; margin: 4px;"
            >{{ tag }}</n-tag>
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
        <div v-if="loading" class="grid-loading">
          <div class="loading-spinner" />
          <p>加载素材中…</p>
        </div>

        <div v-else-if="assets.length === 0" class="grid-empty slide-up">
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

        <div v-else class="asset-grid fade-in">
          <div
            v-for="asset in assets"
            :key="asset.id"
            class="asset-card"
            :class="{ selected: selectedId === asset.id }"
            @click="selectAsset(asset)"
          >
            <div class="ac-thumb">
              <div class="ac-type-icon">{{ typeIcon(asset.file_type) }}</div>
              <div v-if="asset.status === 'processing'" class="ac-status-badge processing">处理中</div>
            </div>
            <div class="ac-info">
              <div class="ac-name" :title="asset.filename">{{ asset.filename }}</div>
              <div class="ac-meta">
                <span>{{ formatSize(asset.file_size) }}</span>
                <span v-if="asset.version > 1" class="ac-version">v{{ asset.version }}</span>
              </div>
              <div class="ac-tags">
                <n-tag
                  v-for="t in (asset.ai_tags || asset.tags || ['未分类']).slice(0, 3)"
                  :key="t" size="tiny" :bordered="false"
                >{{ t }}</n-tag>
              </div>
            </div>
          </div>
        </div>

        <div v-if="totalPages > 1" class="grid-pagination">
          <n-pagination v-model:page="currentPage" :page-count="totalPages" @update:page="loadAssets" />
        </div>
      </main>

      <!-- 右侧详情面板 -->
      <aside v-if="selectedAsset" class="asset-detail anim-scale-in">
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
          <div class="info-row"><span>状态</span><span>{{ selectedAsset.status === 'ready' ? '✅ 就绪' : selectedAsset.status === 'processing' ? '⏳ 处理中' : '📦 已归档' }}</span></div>
          <div class="info-row"><span>上传时间</span><span>{{ formatDate(selectedAsset.created_at) }}</span></div>
        </div>
        <div class="detail-actions">
          <n-button block secondary @click="handleDownload(selectedAsset)">⬇ 下载</n-button>
          <n-button block type="error" @click="handleDelete(selectedAsset)" style="margin-top: 8px;">🗑 删除</n-button>
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
  id: string; filename: string; file_type: string; file_size: number
  tags: string[]; ai_tags: string[]; ai_description: string | null
  thumbnail_path: string | null; status: string; version: number; created_at: string
}

const message = useMessage()
const searchText = ref(''); const searchMode = ref('text')
const fileTypeFilter = ref(''); const tagFilter = ref('')
const loading = ref(false); const assets = ref<AssetItem[]>([])
const selectedId = ref(''); const selectedAsset = ref<AssetItem | null>(null)
const currentPage = ref(1); const totalPages = ref(1)
const sortBy = ref('date')

const popularTags = ['夕阳', '城市', '海滩', '汽车', '美食', '人物', '建筑', '风景', '产品']
const stats = reactive({ total: 0, tagged: 0, totalSize: '0 B' })

function typeIcon(type: string): string {
  if (type.startsWith('image')) return '🖼️'
  if (type.startsWith('video')) return '🎬'
  if (type.startsWith('document')) return '📄'
  return '📁'
}

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0; let size = bytes
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
    if (sortBy.value === 'name') params.sort = 'name'
    else if (sortBy.value === 'size') params.sort = 'size'

    const res = await apiClient.get('/assets/list', { params })
    assets.value = res.data.items
    totalPages.value = Math.ceil(res.data.total / 24)
    stats.total = res.data.total
    stats.tagged = res.data.items.filter((a: AssetItem) => (a.ai_tags || []).length > 0).length

    let totalBytes = 0
    res.data.items.forEach((a: AssetItem) => { totalBytes += a.file_size || 0 })
    stats.totalSize = formatSize(totalBytes)
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
    setTimeout(() => loadAssets(), 2000)
  } catch (e: any) {
    message.error('上传失败: ' + (e.response?.data?.detail || e.message))
  }
}

function handleDownload(asset: AssetItem) {
  message.info('下载功能需配合对象存储使用')
}

async function handleDelete(asset: AssetItem) {
  try {
    await apiClient.delete(`/assets/${asset.id}`)
    message.success('已删除')
    selectedAsset.value = null; selectedId.value = ''
    loadAssets()
  } catch { message.error('删除失败') }
}

onMounted(() => loadAssets())
</script>

<style scoped>
.asset-page { display: flex; flex-direction: column; height: 100%; background: var(--bg-body); transition: background var(--transition-normal); }

/* ═══ Top Bar ═══ */
.asset-topbar {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 24px; border-bottom: 1px solid var(--border-light);
  flex-shrink: 0; background: var(--bg-card);
}
.topbar-left { display: flex; align-items: baseline; gap: 12px; }
.topbar-left h2 { margin: 0; font-size: 18px; font-weight: 700; color: var(--text-primary); white-space: nowrap; }
.topbar-count { font-size: 13px; color: var(--text-muted); }
.topbar-search { flex: 1; display: flex; align-items: center; max-width: 600px; }
.topbar-actions { flex-shrink: 0; display: flex; align-items: center; }

.upload-btn {
  background: var(--primary-gradient) !important; border: none !important;
  font-weight: 600 !important; border-radius: 12px !important;
}

/* ═══ Body ═══ */
.asset-body { flex: 1; display: flex; min-height: 0; overflow: hidden; }

/* ═══ Filters ═══ */
.asset-filters {
  width: 200px; min-width: 200px; padding: 16px;
  border-right: 1px solid var(--border-light); overflow-y: auto;
  background: var(--bg-card);
}
.filter-section { margin-bottom: 20px; }
.filter-section h4 { margin: 0 0 8px; font-size: 12px; color: var(--text-muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.tag-cloud { display: flex; flex-wrap: wrap; gap: 2px; }
.stats-mini { display: flex; flex-wrap: wrap; gap: 8px; }
.stat-item { flex: 1; min-width: 60px; text-align: center; padding: 10px 8px; background: var(--bg-surface); border-radius: 10px; }
.stat-num { display: block; font-size: 18px; font-weight: 700; color: var(--primary); }
.stat-label { display: block; font-size: 11px; color: var(--text-muted); margin-top: 2px; }

/* ═══ Grid Area ═══ */
.asset-grid-area { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; background: var(--bg-body); }
.grid-loading, .grid-empty {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: var(--text-muted);
}

.loading-spinner {
  width: 36px; height: 36px; border: 3px solid var(--border-light);
  border-top-color: var(--primary); border-radius: 50%;
  animation: spin 0.8s linear infinite; margin-bottom: 12px;
}

.empty-icon { font-size: 64px; margin-bottom: 12px; }
.grid-empty h2 { margin: 0 0 6px; font-size: 20px; color: var(--text-primary); }
.grid-empty p { color: var(--text-muted); font-size: 14px; margin: 0 0 28px; }
.feature-hints { display: flex; gap: 12px; }
.hint-card {
  padding: 14px 22px; background: var(--bg-surface); border-radius: 12px;
  text-align: center; font-size: 13px; color: var(--text-secondary);
  border: 1px solid var(--border-light);
}
.hc-icon { font-size: 24px; margin-bottom: 6px; }

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
}
.asset-card {
  background: var(--bg-card); border-radius: 14px; overflow: hidden;
  border: 2px solid transparent; cursor: pointer;
  transition: all .2s var(--ease-smooth);
  box-shadow: var(--shadow-sm);
}
.asset-card:hover { border-color: rgba(99,102,241,.25); transform: translateY(-2px); box-shadow: var(--shadow-md); }
.asset-card.selected { border-color: var(--primary); background: var(--primary-light); }

.ac-thumb {
  height: 120px;
  background: linear-gradient(135deg, rgba(99,102,241,.08), rgba(168,85,247,.05));
  display: flex; align-items: center; justify-content: center;
  position: relative;
}
.ac-type-icon { font-size: 44px; }
.ac-status-badge {
  position: absolute; top: 8px; right: 8px; padding: 2px 8px;
  border-radius: 6px; font-size: 10px; font-weight: 600;
  background: rgba(245,158,11,.15); color: #D97706;
}
.ac-info { padding: 10px 12px; }
.ac-name {
  font-size: 13px; font-weight: 600; color: var(--text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ac-meta { font-size: 11px; color: var(--text-muted); margin: 3px 0 6px; display: flex; gap: 6px; align-items: center; }
.ac-version { background: var(--primary-light); color: var(--primary); padding: 0 6px; border-radius: 4px; font-size: 10px; font-weight: 700; }
.ac-tags { display: flex; flex-wrap: wrap; gap: 3px; }

.grid-pagination { display: flex; justify-content: center; padding: 20px 0; }

/* ═══ Detail Panel ═══ */
.asset-detail {
  width: 280px; min-width: 280px; border-left: 1px solid var(--border-light);
  padding: 20px; overflow-y: auto; background: var(--bg-card);
  animation: scaleIn 0.25s var(--ease-spring) both;
}
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.detail-header h3 { margin: 0; font-size: 15px; word-break: break-word; color: var(--text-primary); }
.detail-thumb {
  height: 160px; border-radius: 12px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(99,102,241,.08), rgba(168,85,247,.05));
}
.dt-icon { font-size: 52px; }
.dt-size { font-size: 13px; color: var(--text-muted); margin-top: 6px; }
.detail-section { margin-bottom: 16px; }
.detail-section h4 { margin: 0 0 8px; font-size: 12px; color: var(--text-muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 4px; }
.no-data { font-size: 12px; color: var(--text-muted); }
.info-row { display: flex; justify-content: space-between; padding: 8px 0; font-size: 13px; border-bottom: 1px solid var(--border-light); }
.info-row span:first-child { color: var(--text-muted); }
.info-row span:last-child { color: var(--text-primary); font-weight: 500; }
.detail-actions { margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border-light); }

/* ═══ Animations ═══ */
.anim-scale-in { animation: scaleIn 0.3s var(--ease-spring) both; }
.fade-in { animation: fadeIn 0.3s var(--ease-smooth) both; }
.slide-up { animation: slideUp 0.4s var(--ease-smooth) both; }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes scaleIn { from { opacity: 0; transform: scale(.94); } to { opacity: 1; transform: scale(1); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

/* ═══ Dark Mode ═══ */
[data-theme="dark"] .asset-topbar { background: var(--bg-card); border-bottom-color: var(--border); }
[data-theme="dark"] .asset-filters { background: var(--bg-card); border-right-color: var(--border); }
[data-theme="dark"] .asset-detail { background: var(--bg-card); border-left-color: var(--border); }
[data-theme="dark"] .asset-grid-area { background: var(--bg-body); }
[data-theme="dark"] .stat-item { background: var(--bg-surface); }
[data-theme="dark"] .ac-thumb { background: linear-gradient(135deg, rgba(99,102,241,.06), rgba(168,85,247,.04)); }
[data-theme="dark"] .asset-card { background: var(--bg-card); }
[data-theme="dark"] .asset-card:hover { border-color: rgba(99,102,241,.2); }
[data-theme="dark"] .detail-thumb { background: linear-gradient(135deg, rgba(99,102,241,.06), rgba(168,85,247,.04)); }
</style>
