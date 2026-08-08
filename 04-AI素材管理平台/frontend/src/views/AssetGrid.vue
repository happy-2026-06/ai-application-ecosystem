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
        <n-button size="large" secondary type="info" style="margin-right: 8px; border-radius: 12px;" @click="showFreeStockModal = true">🌐 免费图库</n-button>
        <n-button type="primary" size="large" class="upload-btn" @click="triggerUpload">📤 上传素材</n-button>
        <input ref="fileInputRef" type="file" multiple accept="image/*,video/*,.pdf,.doc,.docx" style="display:none" @change="onFileChange" />
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

      <!-- 素材网格 / 图搜图上传区 -->
      <main class="asset-grid-area">
        <!-- 图搜图上传区 -->
        <div v-if="searchMode === 'image'" class="image-search-zone fade-in">
          <div class="image-search-dropzone" @click="triggerImageSearch" @dragover.prevent @drop.prevent="onDropImageSearch">
            <div class="is-icon">🖼️</div>
            <p>点击或拖拽图片到这里进行以图搜图</p>
            <span class="is-hint">目前基于文件名语义匹配，视觉搜索(CLIP)即将上线</span>
            <input ref="imageSearchInputRef" type="file" accept="image/*" style="display:none" @change="onImageSearchFile" />
          </div>
          <div v-if="imageSearchFile" class="image-search-preview">
            <img :src="imageSearchPreviewUrl" alt="搜索图片" class="is-preview-img" />
            <span class="is-preview-name">{{ imageSearchFile.name }}</span>
            <n-button size="small" @click="clearImageSearch">✕ 清除</n-button>
          </div>
        </div>

        <!-- 上传进度面板（可折叠） -->
        <div v-if="uploadQueue.length > 0" class="upload-panel fade-in">
          <div class="up-header" @click="uploadPanelOpen = !uploadPanelOpen">
            <div class="up-header-left">
              <span class="up-toggle">{{ uploadPanelOpen ? '▼' : '▶' }}</span>
              <span class="up-title">📤 上传进度</span>
              <span class="up-summary">{{ uploadDoneCount }}/{{ uploadQueue.length }} 完成</span>
            </div>
            <n-button text size="tiny" @click.stop="clearDoneUploads" v-if="uploadDoneCount > 0">清除已完成</n-button>
          </div>
          <div v-show="uploadPanelOpen" class="up-body">
            <div v-for="(item, idx) in uploadQueue" :key="idx" class="upload-item">
              <div class="uq-left">
                <img v-if="item.previewUrl" :src="item.previewUrl" class="uq-thumb" />
                <span v-else class="uq-icon">{{ item.icon }}</span>
                <div class="uq-name-area">
                  <div v-if="item.editingName !== undefined" class="uq-edit-row">
                    <n-input
                      v-model:value="item.editingName"
                      size="small"
                      placeholder="输入新文件名（不带扩展名）"
                      @keyup.enter="finishRename(item)"
                      @keyup.esc="item.editingName = undefined"
                      style="width: 160px;"
                    />
                    <n-button size="tiny" type="primary" @click="finishRename(item)">✓</n-button>
                    <n-button size="tiny" @click="item.editingName = undefined">✕</n-button>
                  </div>
                  <template v-else>
                    <div class="uq-filename" @click="startRename(item)" title="点击修改文件名">{{ item.customName || item.name }}</div>
                    <div class="uq-original" v-if="item.customName && item.customName !== item.name">原名: {{ item.name }}</div>
                  </template>
                </div>
              </div>
              <div class="uq-right">
                <n-progress
                  :percentage="item.progress"
                  :status="item.status === 'error' ? 'error' : item.status === 'done' ? 'success' : 'default'"
                  :height="12"
                  :border-radius="6"
                  :show-indicator="false"
                  style="flex: 1;"
                />
                <span class="uq-status" :class="'uq-' + item.status">{{ item.statusText }}</span>
              </div>
            </div>
          </div>
        </div>

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
              <img v-if="isImage(asset)" :src="authUrl(asset.id) || undefined" :alt="asset.filename" class="ac-img" @error="onImgError" />
              <div v-else class="ac-type-icon">{{ typeIcon(asset.file_type) }}</div>
              <div v-if="asset.status === 'processing'" class="ac-status-badge processing">处理中</div>
            </div>
            <div class="ac-info">
              <div v-if="editingAssetId === asset.id" class="ac-edit-row" @click.stop>
                <n-input
                  v-model:value="editingAssetName"
                  size="small"
                  @keyup.enter="saveAssetRename(asset)"
                  @keyup.esc="cancelAssetRename"
                  style="flex: 1; font-size: 12px;"
                />
                <n-button size="tiny" type="primary" @click="saveAssetRename(asset)">✓</n-button>
                <n-button size="tiny" @click="cancelAssetRename">✕</n-button>
              </div>
              <div v-else class="ac-name" :title="asset.filename" @click.stop="startAssetRename(asset)">{{ asset.filename }}</div>
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
              <div class="ac-actions">
                <n-button text size="tiny" type="primary" @click.stop="openPreview(asset)" title="预览">🔍</n-button>
                <n-button text size="tiny" @click.stop="handleDownload(asset)" title="下载">⬇</n-button>
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
          <h3>
            <template v-if="isEditingName">
              <n-input
                v-model:value="editNameValue"
                size="small"
                style="flex: 1;"
                @keyup.enter="saveEditName"
                @keyup.esc="isEditingName = false"
              />
              <n-button size="tiny" type="primary" @click="saveEditName" style="margin-left: 4px;">✓</n-button>
              <n-button size="tiny" @click="isEditingName = false" style="margin-left: 2px;">✕</n-button>
            </template>
            <template v-else>
              <span class="detail-name-text" @dblclick="startEditName" title="双击编辑名称">{{ selectedAsset.filename }}</span>
            </template>
          </h3>
          <n-button text @click="closeDetail">✕</n-button>
        </div>
        <div class="detail-thumb">
          <img v-if="isImage(selectedAsset)" :src="authUrl(selectedAsset.id) || undefined" :alt="selectedAsset.filename" class="dt-preview" @error="onImgError" />
          <div v-else class="dt-icon">{{ typeIcon(selectedAsset.file_type) }}</div>
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
          <h4>
            📝 手动标签
            <n-button text size="tiny" type="primary" @click="startAddTag" style="margin-left: 4px;">+ 添加</n-button>
          </h4>
          <div class="tag-list">
            <n-tag
              v-for="t in selectedAsset.tags || []" :key="t" type="success" size="small"
              closable @close="removeTag(t)"
            >{{ t }}</n-tag>
            <span v-if="!(selectedAsset.tags || []).length && !isAddingTag" class="no-data">暂无</span>
            <div v-if="isAddingTag" class="tag-add-row">
              <n-input v-model:value="newTagValue" size="tiny" placeholder="新标签" style="width: 100px;" @keyup.enter="addTag" />
              <n-button size="tiny" type="primary" @click="addTag">✓</n-button>
              <n-button size="tiny" @click="isAddingTag = false">✕</n-button>
            </div>
          </div>
        </div>
        <div class="detail-section">
          <h4>📋 基本信息</h4>
          <div class="info-row">
            <span>类型</span>
            <n-select v-model:value="editStatus" size="tiny" :options="statusOptions" style="width: 110px;" @update:value="saveStatus" />
          </div>
          <div class="info-row"><span>大小</span><span>{{ formatSize(selectedAsset.file_size) }}</span></div>
          <div class="info-row"><span>版本</span><span>v{{ selectedAsset.version }}</span></div>
          <div class="info-row"><span>上传时间</span><span>{{ formatDate(selectedAsset.created_at) }}</span></div>
        </div>
        <div class="detail-actions">
          <n-button block type="primary" @click="openPreview(selectedAsset)">🔍 预览</n-button>
          <n-button block secondary @click="handleDownload(selectedAsset)" style="margin-top: 6px;">⬇ 下载</n-button>
          <n-button block type="error" @click="handleDelete(selectedAsset)" style="margin-top: 6px;">🗑 删除</n-button>
        </div>
      </aside>
    </div>

    <!-- ═══ 预览弹窗 ═══ -->
    <n-modal v-model:show="showPreview" preset="card" :title="'🔍 ' + (previewAsset?.filename || '预览')" size="huge" style="max-width: 1100px; width: 90vw; height: 85vh;" :mask-closable="true">
      <template #header-extra>
        <n-button text size="small" @click="showPreview = false">✕ 关闭</n-button>
      </template>
      <div class="preview-body">
        <!-- 图片 -->
        <div v-if="isImage(previewAsset)" class="preview-image-wrapper">
          <img :src="authUrl(previewAsset?.id || '') || undefined" :alt="previewAsset?.filename" class="preview-img" />
        </div>
        <!-- 文档等非图片 — 信息展示 -->
        <div v-else class="preview-doc">
          <div class="preview-doc-icon">{{ typeIcon(previewAsset?.file_type || '') }}</div>
          <h3>{{ previewAsset?.filename }}</h3>
          <div class="preview-meta">
            <div class="pm-row"><span>类型</span><span>{{ previewAsset?.file_type }}</span></div>
            <div class="pm-row"><span>大小</span><span>{{ formatSize(previewAsset?.file_size || 0) }}</span></div>
            <div class="pm-row"><span>状态</span><span>{{ previewAsset?.status }}</span></div>
            <div class="pm-row"><span>版本</span><span>v{{ previewAsset?.version }}</span></div>
            <div class="pm-row"><span>上传时间</span><span>{{ formatDate(previewAsset?.created_at || '') }}</span></div>
          </div>
          <div class="preview-tags">
            <h4>🏷️ 标签</h4>
            <n-tag v-for="t in (previewAsset?.ai_tags || [])" :key="t" type="info" size="small" style="margin: 2px;">{{ t }}</n-tag>
            <n-tag v-for="t in (previewAsset?.tags || [])" :key="t" type="success" size="small" style="margin: 2px;">{{ t }}</n-tag>
            <span v-if="!(previewAsset?.ai_tags || []).length && !(previewAsset?.tags || []).length" class="no-data">暂无标签</span>
          </div>
          <div v-if="previewAsset?.ai_description" class="preview-desc">
            <h4>📝 AI 描述</h4>
            <p>{{ previewAsset?.ai_description }}</p>
          </div>
          <div class="preview-doc-actions">
            <n-button type="primary" @click="handleDownload(previewAsset!)">⬇ 下载文件</n-button>
          </div>
        </div>
      </div>
    </n-modal>

    <!-- ═══ Free Stock Photo Modal ═══ -->
    <n-modal v-model:show="showFreeStockModal" preset="card" title="🌐 免费图库 — Lorem Picsum" size="huge" style="max-width: 900px;" :mask-closable="true">
      <template #header-extra>
        <n-button text size="small" @click="freeStockPage = Math.max(1, freeStockPage - 1)" :disabled="freeStockPage <= 1">◀ 上一页</n-button>
        <span style="margin: 0 12px; font-size: 13px; color: var(--text-muted);">第 {{ freeStockPage }} 页</span>
        <n-button text size="small" @click="loadFreeStock(freeStockPage + 1)">下一页 ▶</n-button>
      </template>

      <!-- URL Import -->
      <div class="url-import-row">
        <n-input v-model:value="importUrl" placeholder="或者粘贴图片 URL 直接导入…" size="small" clearable style="flex: 1;" />
        <n-input v-model:value="importUrlTags" placeholder="标签(逗号分隔)" size="small" style="width: 140px; margin: 0 8px;" />
        <n-button size="small" type="primary" @click="handleUrlImport" :loading="urlImporting">⬇ 导入</n-button>
      </div>

      <n-divider />

      <!-- Loading -->
      <div v-if="freeStockLoading" class="fs-loading">
        <div class="loading-spinner" />
        <p>加载免费图库…</p>
      </div>

      <!-- Photo Grid -->
      <div v-else class="fs-grid">
        <div v-for="photo in freeStockPhotos" :key="photo.id" class="fs-card">
          <div class="fs-thumb">
            <img :src="photo.thumbnail" :alt="'Photo by ' + photo.author" loading="lazy" style="width:100%;height:100%;object-fit:cover;border-radius:8px;" />
          </div>
          <div class="fs-info">
            <span class="fs-author">📷 {{ photo.author }}</span>
            <span class="fs-size">{{ photo.width }}×{{ photo.height }}</span>
            <n-button size="tiny" type="primary" @click="handleImportFreePhoto(photo)" :loading="photo._importing">⬇ 导入</n-button>
          </div>
        </div>
      </div>

      <div v-if="!freeStockLoading && freeStockPhotos.length === 0" style="text-align: center; padding: 40px; color: var(--text-muted);">
        <p>图库暂时无法加载，请检查网络后重试</p>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { assetApi, type AssetItem } from '../api/assets'

const message = useMessage()
const authStore = useAuthStore()
const searchText = ref(''); const searchMode = ref('text')
const fileTypeFilter = ref(''); const tagFilter = ref('')
const loading = ref(false); const assets = ref<AssetItem[]>([])
const selectedId = ref(''); const selectedAsset = ref<AssetItem | null>(null)
const currentPage = ref(1); const totalPages = ref(1)
const sortBy = ref('date')

// ── Popular tags (now fetched from API) ──
const popularTags = ref<string[]>(['夕阳', '城市', '海滩', '汽车', '美食', '人物', '建筑', '风景', '产品'])

// ── Stats ──
const stats = reactive({ total: 0, tagged: 0, totalSize: '0 B' })

// ── Upload queue ──
interface UploadItem {
  name: string; customName?: string; editingName?: string; file: File;
  previewUrl?: string; icon: string;
  progress: number; status: 'pending' | 'uploading' | 'done' | 'error'; statusText: string
}
const uploadQueue = ref<UploadItem[]>([])
const uploadPanelOpen = ref(true)
const uploadDoneCount = ref(0)

// ── Inline editing ──
const isEditingName = ref(false); const editNameValue = ref('')
const isAddingTag = ref(false); const newTagValue = ref('')
// Grid card inline rename
const editingAssetId = ref(''); const editingAssetName = ref('')
const editStatus = ref('ready')
const statusOptions = [
  { label: '✅ 就绪', value: 'ready' },
  { label: '⏳ 处理中', value: 'processing' },
  { label: '📦 已归档', value: 'archived' },
]

// ── Image search ──
const imageSearchInputRef = ref<HTMLInputElement | null>(null)
const imageSearchFile = ref<File | null>(null)
const imageSearchPreviewUrl = ref('')

// ── Free stock photo modal ──
const showFreeStockModal = ref(false)
const freeStockLoading = ref(false)
const freeStockPhotos = ref<any[]>([])
const freeStockPage = ref(1)
const importUrl = ref('')
const importUrlTags = ref('')
const urlImporting = ref(false)

// ── Preview modal ──
const showPreview = ref(false)
const previewAsset = ref<AssetItem | null>(null)

// ── Helpers ──
function typeIcon(type: string): string {
  if (type.startsWith('image')) return '🖼️'
  if (type.startsWith('video')) return '🎬'
  if (type.startsWith('document')) return '📄'
  return '📁'
}

function isImage(asset: AssetItem): boolean {
  return (asset.file_type || '').startsWith('image')
}

/** Build a token-authenticated URL for <img>/<a> elements */
function authUrl(assetId: string): string {
  return assetApi.getAuthUrl(assetId)
}

function onImgError(e: Event) {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
  const parent = img.parentElement
  if (parent) {
    const fallback = document.createElement('div')
    fallback.className = 'ac-type-icon'
    fallback.textContent = '🖼️'
    parent.prepend(fallback)
  }
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

// ── Load assets ──
async function loadAssets() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: currentPage.value, page_size: 24 }
    if (fileTypeFilter.value) params.file_type = fileTypeFilter.value
    if (tagFilter.value) params.tag = tagFilter.value
    if (searchText.value) params.search = searchText.value
    if (sortBy.value === 'name') params.sort = 'name'
    else if (sortBy.value === 'size') params.sort = 'size'

    const [listRes, statsRes] = await Promise.all([
      assetApi.list(params),
      assetApi.getStats(),
    ])
    assets.value = listRes.data.items
    totalPages.value = Math.ceil(listRes.data.total / 24)
    stats.total = statsRes.data.total
    stats.tagged = statsRes.data.tagged
    stats.totalSize = formatSize(statsRes.data.total_size_bytes || 0)

    // Also refresh sidebar stats
    try {
      const authStore = (await import('../stores/auth')).useAuthStore()
      // sidebar stats are fetched independently in AppLayout
    } catch {}
  } catch (e) {
    console.error('Load assets failed:', e)
  } finally {
    loading.value = false
  }
}

async function loadPopularTags() {
  try {
    const res = await assetApi.getPopularTags()
    if (res.data.tags.length > 0) {
      popularTags.value = res.data.tags
    }
  } catch { /* keep defaults */ }
}

async function loadStats() {
  try {
    const res = await assetApi.getStats()
    stats.total = res.data.total
    stats.tagged = res.data.tagged
    stats.totalSize = formatSize(res.data.total_size_bytes)
  } catch { /* silent */ }
}

async function refreshAfterChange() {
  loadAssets()
  loadPopularTags()
  loadStats()
}

function handleSearch() { currentPage.value = 1; loadAssets() }

// ── Select & detail ──
async function selectAsset(asset: AssetItem) {
  selectedId.value = asset.id
  // Fetch full detail
  try {
    const res = await assetApi.get(asset.id)
    selectedAsset.value = res.data
    editStatus.value = res.data.status
  } catch {
    selectedAsset.value = asset
  }
}

function closeDetail() {
  selectedAsset.value = null
  selectedId.value = ''
  isEditingName.value = false
  isAddingTag.value = false
}

// ── Upload ──
const fileInputRef = ref<HTMLInputElement | null>(null)

function triggerUpload() {
  fileInputRef.value?.click()
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return

  for (const file of files) {
    // Strip extension for display name
    const baseName = file.name.replace(/\.[^.]+$/, '')
    const ext = file.name.split('.').pop()?.toLowerCase() || ''
    const isImg = ['jpg','jpeg','png','gif','webp','svg','bmp'].includes(ext)
    const isVid = ['mp4','mov','avi','webm','mkv'].includes(ext)
    const icon = isImg ? '🖼️' : isVid ? '🎬' : '📄'
    let previewUrl: string | undefined
    if (isImg) {
      previewUrl = URL.createObjectURL(file)
    }
    const item: UploadItem = {
      name: file.name, customName: baseName, file: file,
      previewUrl, icon,
      progress: 0, status: 'pending', statusText: '等待中…',
    }
    uploadQueue.value.push(item)
  }

  uploadPanelOpen.value = true

  // Process uploads sequentially so each can have its own name
  let successCount = 0; let failCount = 0
  for (const item of uploadQueue.value) {
    if (item.status !== 'pending') continue
    item.status = 'uploading'; item.statusText = '上传中…'
    try {
      const uploadName = item.customName !== item.file.name.replace(/\.[^.]+$/, '')
        ? item.customName : undefined
      const res = await assetApi.upload(item.file, undefined, uploadName, (pct) => {
        item.progress = pct
        item.statusText = `${pct}%`
      })
      item.progress = 100
      item.status = 'done'
      item.statusText = '✅ 完成'
      successCount++
      console.log('Upload success:', res.data)
    } catch (e: any) {
      item.status = 'error'
      item.statusText = '❌ 失败'
      failCount++
      const detail = e?.response?.data?.detail || e?.response?.status || e?.code || e?.message || String(e)
      console.error('Upload failed:', e?.response?.status, e?.response?.data, e)
      message.error('上传失败: ' + detail)
    }
  }

  // Clean up preview URLs
  for (const item of uploadQueue.value) {
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl)
  }

  input.value = ''
  updateUploadCounts()

  // Remove done/error items after 3s
  setTimeout(() => {
    uploadQueue.value = uploadQueue.value.filter(u => u.status === 'uploading' || u.status === 'pending')
    updateUploadCounts()
  }, 3000)

  if (successCount > 0) {
    message.success(`上传成功 ${successCount} 个文件，AI 正在生成标签…`)
    loadAssets()
    loadPopularTags()
  }
}

function updateUploadCounts() {
  uploadDoneCount.value = uploadQueue.value.filter(u => u.status === 'done').length
}

function clearDoneUploads() {
  uploadQueue.value = uploadQueue.value.filter(u => u.status !== 'done' && u.status !== 'error')
  updateUploadCounts()
}

// ── Upload queue rename ──
function startRename(item: UploadItem) {
  item.editingName = item.customName || item.name.replace(/\.[^.]+$/, '')
}

function finishRename(item: UploadItem) {
  if (item.editingName !== undefined && item.editingName.trim()) {
    item.customName = item.editingName.trim()
  }
  item.editingName = undefined
}

// ── Grid card inline rename ──
function startAssetRename(asset: AssetItem) {
  editingAssetId.value = asset.id
  editingAssetName.value = asset.original_name || asset.filename
}

async function saveAssetRename(asset: AssetItem) {
  const name = editingAssetName.value.trim()
  if (!name) { cancelAssetRename(); return }
  try {
    const res = await assetApi.update(asset.id, { original_name: name })
    // Update both list and detail panel
    const idx = assets.value.findIndex(a => a.id === asset.id)
    if (idx >= 0) assets.value[idx] = res.data
    if (selectedAsset.value?.id === asset.id) selectedAsset.value = res.data
    editingAssetId.value = ''
    editingAssetName.value = ''
    message.success('名称已更新')
  } catch { message.error('改名失败') }
}

function cancelAssetRename() {
  editingAssetId.value = ''
  editingAssetName.value = ''
}

// ── Download ──
function handleDownload(asset: AssetItem) {
  const url = assetApi.getAuthUrl(asset.id)
  const a = document.createElement('a')
  a.href = url
  a.download = asset.original_name || asset.filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// ── Delete ──
async function handleDelete(asset: AssetItem) {
  try {
    await assetApi.remove(asset.id)
    message.success('已删除')
    closeDetail()
    refreshAfterChange()
  } catch { message.error('删除失败') }
}

// ── Inline editing ──
function startEditName() {
  if (!selectedAsset.value) return
  editNameValue.value = selectedAsset.value.original_name || selectedAsset.value.filename
  isEditingName.value = true
}

async function saveEditName() {
  if (!selectedAsset.value || !editNameValue.value.trim()) return
  try {
    const res = await assetApi.update(selectedAsset.value.id, { original_name: editNameValue.value.trim() })
    selectedAsset.value = res.data
    isEditingName.value = false
    message.success('名称已更新')
    loadAssets()
  } catch { message.error('更新失败') }
}

// ── Tag editing ──
function startAddTag() { isAddingTag.value = true; newTagValue.value = '' }

async function addTag() {
  if (!selectedAsset.value || !newTagValue.value.trim()) return
  const current = selectedAsset.value.tags || []
  if (current.includes(newTagValue.value.trim())) {
    message.warning('标签已存在')
    return
  }
  const newTags = [...current, newTagValue.value.trim()]
  try {
    const res = await assetApi.update(selectedAsset.value.id, { tags: newTags })
    selectedAsset.value = res.data
    isAddingTag.value = false
    newTagValue.value = ''
    loadPopularTags()
  } catch { message.error('添加标签失败') }
}

async function removeTag(tag: string) {
  if (!selectedAsset.value) return
  const newTags = (selectedAsset.value.tags || []).filter(t => t !== tag)
  try {
    const res = await assetApi.update(selectedAsset.value.id, { tags: newTags })
    selectedAsset.value = res.data
    loadPopularTags()
  } catch { message.error('移除标签失败') }
}

// ── Status change ──
async function saveStatus(value: string) {
  if (!selectedAsset.value) return
  try {
    const res = await assetApi.update(selectedAsset.value.id, { status: value })
    selectedAsset.value = res.data
    message.success('状态已更新')
  } catch { message.error('更新状态失败') }
}

// ── Image search ──
function triggerImageSearch() { imageSearchInputRef.value?.click() }

function onDropImageSearch(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image')) {
    handleImageSearchFile(file)
  }
}

function onImageSearchFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) handleImageSearchFile(file)
}

function handleImageSearchFile(file: File) {
  imageSearchFile.value = file
  imageSearchPreviewUrl.value = URL.createObjectURL(file)
  // Extract search keyword from filename
  const name = file.name.replace(/\.[^.]+$/, '')
  searchText.value = name
  searchMode.value = 'text'  // Fall back to text search until CLIP is integrated
  handleSearch()
  message.info('已根据文件名进行语义搜索 (视觉搜索即将上线)')
}

function clearImageSearch() {
  imageSearchFile.value = null
  if (imageSearchPreviewUrl.value) {
    URL.revokeObjectURL(imageSearchPreviewUrl.value)
    imageSearchPreviewUrl.value = ''
  }
}

// ── Preview ──
function openPreview(asset: AssetItem) {
  previewAsset.value = asset
  showPreview.value = true
}

// ── Init ──
onMounted(() => {
  loadAssets()
  loadStats()
  loadPopularTags()
})

// ── Free stock photo functions ──
async function loadFreeStock(page: number) {
  freeStockLoading.value = true
  freeStockPage.value = page
  try {
    const res = await assetApi.getFreeStockPhotos(page, 12)
    freeStockPhotos.value = res.data.photos.map((p: any) => ({ ...p, _importing: false }))
  } catch (e) {
    console.error('Failed to load free stock:', e)
    freeStockPhotos.value = []
    message.error('免费图库加载失败，请检查网络')
  } finally {
    freeStockLoading.value = false
  }
}

// Watch modal to load photos on first open
watch(showFreeStockModal, (val) => {
  if (val && freeStockPhotos.value.length === 0) {
    loadFreeStock(1)
  }
})

async function handleImportFreePhoto(photo: any) {
  photo._importing = true
  try {
    await assetApi.importFromUrl(photo.download_url)
    message.success('素材导入成功！AI 正在生成标签…')
    photo._importing = false
    refreshAfterChange()
  } catch (e: any) {
    photo._importing = false
    const detail = e?.response?.data?.detail || '导入失败'
    message.error('导入失败: ' + detail)
  }
}

async function handleUrlImport() {
  const url = importUrl.value.trim()
  if (!url) { message.warning('请输入图片 URL'); return }
  urlImporting.value = true
  try {
    await assetApi.importFromUrl(url, importUrlTags.value.trim() || undefined)
    message.success('导入成功！AI 正在生成标签…')
    importUrl.value = ''
    importUrlTags.value = ''
    refreshAfterChange()
  } catch (e: any) {
    const detail = e?.response?.data?.detail || '导入失败'
    message.error('导入失败: ' + detail)
  } finally {
    urlImporting.value = false
  }
}
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

/* ═══ Image Search Zone ═══ */
.image-search-zone { margin-bottom: 16px; }
.image-search-dropzone {
  border: 2px dashed var(--border); border-radius: 14px;
  padding: 32px; text-align: center; cursor: pointer;
  background: var(--bg-surface); transition: all .2s var(--ease-smooth);
}
.image-search-dropzone:hover { border-color: var(--primary); background: var(--primary-light); }
.is-icon { font-size: 48px; margin-bottom: 10px; }
.image-search-dropzone p { margin: 0 0 6px; font-size: 14px; color: var(--text-secondary); font-weight: 600; }
.is-hint { font-size: 12px; color: var(--text-muted); }
.image-search-preview {
  display: flex; align-items: center; gap: 12px; margin-top: 12px;
  padding: 10px 14px; background: var(--bg-card); border-radius: 10px;
  border: 1px solid var(--border-light);
}
.is-preview-img { width: 48px; height: 48px; object-fit: cover; border-radius: 8px; }
.is-preview-name { flex: 1; font-size: 13px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ═══ Upload Panel ═══ */
.upload-panel {
  margin-bottom: 16px;
  background: var(--bg-card); border-radius: 14px;
  border: 1px solid var(--border-light); overflow: hidden;
}
.up-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 16px; cursor: pointer; user-select: none;
  background: var(--bg-surface); transition: background .15s;
}
.up-header:hover { background: var(--primary-light); }
.up-header-left { display: flex; align-items: center; gap: 8px; }
.up-toggle { font-size: 10px; color: var(--text-muted); }
.up-title { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.up-summary { font-size: 12px; color: var(--text-muted); }
.up-body { padding: 8px 12px 12px; display: flex; flex-direction: column; gap: 6px; }
.upload-item {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 8px 12px;
  background: var(--bg-surface); border-radius: 10px; border: 1px solid var(--border-light);
}
.uq-left { display: flex; align-items: center; gap: 8px; min-width: 0; flex: 1; }
.uq-thumb { width: 36px; height: 36px; object-fit: cover; border-radius: 6px; flex-shrink: 0; }
.uq-icon { font-size: 22px; flex-shrink: 0; }
.uq-name-area { min-width: 0; }
.uq-filename { font-size: 13px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; cursor: pointer; border-bottom: 1px dashed transparent; transition: all .15s; }
.uq-filename:hover { color: var(--primary); border-bottom-color: var(--primary); }
.uq-original { font-size: 11px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }
.uq-edit-row { display: flex; align-items: center; gap: 4px; }
.uq-right { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.uq-status { font-size: 12px; white-space: nowrap; font-weight: 600; }
.uq-done { color: #10B981; }
.uq-error { color: #EF4444; }
.uq-uploading { color: var(--primary); }
.uq-pending { color: var(--text-muted); }

/* ═══ Card actions ═══ */
.ac-actions {
  display: flex; gap: 2px; margin-top: 4px; padding-top: 4px;
  border-top: 1px solid var(--border-light);
}

/* ═══ Preview Modal ═══ */
.preview-body { height: calc(85vh - 120px); display: flex; align-items: center; justify-content: center; overflow: hidden; }
.preview-image-wrapper { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: var(--bg-body); border-radius: 12px; }
.preview-img { max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px; }
.preview-doc { width: 100%; max-width: 600px; text-align: center; overflow-y: auto; max-height: 100%; }
.preview-doc-icon { font-size: 72px; margin-bottom: 12px; }
.preview-doc h3 { margin: 0 0 16px; font-size: 18px; color: var(--text-primary); word-break: break-word; }
.preview-meta { text-align: left; margin-bottom: 16px; }
.pm-row { display: flex; justify-content: space-between; padding: 8px 0; font-size: 13px; border-bottom: 1px solid var(--border-light); }
.pm-row span:first-child { color: var(--text-muted); }
.pm-row span:last-child { color: var(--text-primary); font-weight: 500; }
.preview-tags, .preview-desc { text-align: left; margin-bottom: 16px; }
.preview-tags h4, .preview-desc h4 { margin: 0 0 8px; font-size: 12px; color: var(--text-muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.preview-desc p { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
.preview-doc-actions { margin-top: 16px; }

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
  position: relative; overflow: hidden;
}
.ac-img {
  width: 100%; height: 100%;
  object-fit: cover;
  transition: transform 0.3s var(--ease-smooth);
}
.asset-card:hover .ac-img { transform: scale(1.05); }
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
  cursor: pointer; padding: 2px 4px; margin: -2px -4px;
  border-radius: 4px; transition: background .15s;
}
.ac-name:hover { background: var(--bg-surface); color: var(--primary); }
.ac-edit-row { display: flex; align-items: center; gap: 3px; }
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
.detail-header h3 { margin: 0; font-size: 15px; word-break: break-word; color: var(--text-primary); flex: 1; }
.detail-name-text { cursor: pointer; padding: 2px 4px; border-radius: 4px; transition: background .15s; }
.detail-name-text:hover { background: var(--bg-surface); }
.detail-thumb {
  height: 200px; border-radius: 12px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(99,102,241,.08), rgba(168,85,247,.05));
  overflow: hidden;
}
.dt-preview {
  width: 100%; height: 100%;
  object-fit: contain;
  border-radius: 12px;
}
.dt-icon { font-size: 52px; }
.dt-size { font-size: 13px; color: var(--text-muted); margin-top: 6px; }
.detail-section { margin-bottom: 16px; }
.detail-section h4 { margin: 0 0 8px; font-size: 12px; color: var(--text-muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; }
.tag-list { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
.tag-add-row { display: flex; align-items: center; gap: 4px; margin-top: 4px; }
.no-data { font-size: 12px; color: var(--text-muted); }
.info-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 13px; border-bottom: 1px solid var(--border-light); }
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
[data-theme="dark"] .image-search-dropzone { background: var(--bg-surface); border-color: var(--border); }
[data-theme="dark"] .image-search-dropzone:hover { background: var(--primary-light); }
[data-theme="dark"] .image-search-preview { background: var(--bg-card); border-color: var(--border); }
[data-theme="dark"] .upload-panel { background: var(--bg-card); border-color: var(--border); }
[data-theme="dark"] .up-header { background: var(--bg-surface); }
[data-theme="dark"] .upload-item { background: var(--bg-surface); border-color: var(--border); }
[data-theme="dark"] .preview-image-wrapper { background: var(--bg-body); }

/* ═══ Free Stock Modal ═══ */
.url-import-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }

.fs-loading {
  display: flex; flex-direction: column; align-items: center; padding: 40px; color: var(--text-muted);
}
.fs-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.fs-card {
  background: var(--bg-surface); border-radius: 10px; overflow: hidden;
  border: 1px solid var(--border-light); transition: all .2s var(--ease-smooth);
}
.fs-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.fs-thumb { height: 100px; overflow: hidden; }
.fs-info {
  padding: 6px 8px; display: flex; flex-direction: column; gap: 2px;
}
.fs-author { font-size: 11px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fs-size { font-size: 10px; color: var(--text-muted); }
.fs-info .n-button { margin-top: 4px; width: 100%; }
</style>