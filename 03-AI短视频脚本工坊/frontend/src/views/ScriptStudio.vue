<template>
  <div class="studio-page">
    <!-- Left: History + Input -->
    <aside class="studio-sidebar">
      <!-- History section -->
      <div class="history-section" v-if="historySessions.length > 0">
        <div class="section-header">
          <label class="section-label">📝 历史记录 ({{ historySessions.length }})</label>
          <n-space>
            <n-button v-if="batchMode" text size="tiny" type="error" @click="batchDelete">🗑 删除选中({{ selectedIds.size }})</n-button>
            <n-button text size="tiny" @click="toggleBatchMode">{{ batchMode ? '取消' : '批量' }}</n-button>
            <n-button text size="tiny" type="primary" @click="showNewScript">+ 新建</n-button>
          </n-space>
        </div>
        <n-input
          v-if="historySessions.length > 5"
          v-model:value="historySearch"
          placeholder="搜索历史…"
          size="small"
          clearable
          class="history-search"
        />
        <div class="history-list">
          <div
            v-for="s in filteredHistory"
            :key="s.id"
            class="history-item"
            :class="{ active: s.id === currentSessionId }"
            @click="batchMode ? toggleSelect(s.id) : loadHistory(s)"
          >
            <n-checkbox v-if="batchMode" :checked="selectedIds.has(s.id)" size="small" @click.stop="toggleSelect(s.id)" style="margin-right:4px;" />
            <span class="hi-title" :title="cleanTitle(s.title)">{{ cleanTitle(s.title) }}</span>
            <span class="hi-date">{{ formatDate(s.updated_at) }}</span>
            <n-popconfirm v-if="!batchMode" @positive-click="deleteHistory(s.id)">
              <template #trigger>
                <n-button text size="tiny" class="hi-delete" @click.stop>🗑</n-button>
              </template>
              确认删除？
            </n-popconfirm>
          </div>
        </div>
      </div>

      <!-- New script mode: input form -->
      <template v-if="isNewScript">
        <div class="sidebar-header">
          <h2>🎬 脚本工坊</h2>
          <p>输入产品信息，AI 生成可拍摄的分镜脚本</p>
        </div>

        <div class="input-section">
          <label class="input-label">📦 产品名称 <span class="required">*</span></label>
          <n-input
            v-model:value="productName"
            placeholder="如：智能蓝牙耳机"
            :disabled="isLoading"
            size="large"
          />
        </div>

        <div class="input-section">
          <label class="input-label">✨ 核心卖点</label>
          <n-input
            v-model:value="sellingPoints"
            type="textarea"
            placeholder="每个卖点一行，如：&#10;降噪40dB，地铁也能安静听歌&#10;续航30小时，一周充一次"
            :autosize="{ minRows: 3, maxRows: 5 }"
            :disabled="isLoading"
          />
        </div>

        <div class="input-section">
          <label class="input-label">💰 价格（可选）</label>
          <n-input
            v-model:value="price"
            placeholder="如：¥299"
            :disabled="isLoading"
          />
        </div>

        <div class="input-section">
          <label class="input-label">🎭 模板风格</label>
          <n-radio-group v-model:value="templateStyle">
            <n-space vertical>
              <n-radio value="带货">
                <span class="radio-label">🛍️ 带货类</span>
                <span class="radio-desc">— 痛点前置+卖点演示+价格锚点</span>
              </n-radio>
              <n-radio value="测评">
                <span class="radio-label">📊 测评对比类</span>
                <span class="radio-desc">— 产品对比+实测数据+结论推荐</span>
              </n-radio>
              <n-radio value="开箱">
                <span class="radio-label">📦 沉浸开箱类</span>
                <span class="radio-desc">— 悬念+开箱过程+第一视角</span>
              </n-radio>
            </n-space>
          </n-radio-group>
        </div>

        <div class="input-section">
          <label class="input-label">📱 目标平台</label>
          <div class="platform-chips">
            <span
              v-for="p in platformOptions"
              :key="p"
              class="plat-chip"
              :class="{ active: targetPlatform === p }"
              :style="{ '--pc': platformColor(p) }"
              @click="targetPlatform = p"
            >{{ p }}</span>
          </div>
        </div>

        <n-button
          type="primary" block size="large"
          :loading="isLoading"
          :disabled="!productName.trim()"
          @click="handleGenerate"
          class="gen-btn"
        >
          🎥 生成分镜脚本
        </n-button>

        <div class="quick-templates">
          <label class="input-label">⚡ 快捷填充</label>
          <n-space vertical>
            <n-button text @click="quickFill('充电宝', '20000mAh大容量\n支持快充\n小巧便携', '¥99', '带货')" class="quick-btn">🔋 充电宝带货</n-button>
            <n-button text @click="quickFill('蓝牙耳机', '主动降噪\n30h续航\nHiFi音质', '¥299', '测评')" class="quick-btn">🎧 耳机测评</n-button>
            <n-button text @click="quickFill('智能手表', '健康监测\n运动模式\n7天续航', '¥599', '开箱')" class="quick-btn">⌚ 手表开箱</n-button>
          </n-space>
        </div>
      </template>

      <!-- Viewing history mode -->
      <div v-else class="sidebar-header history-mode-header">
        <p>查看历史脚本</p>
        <n-button size="small" type="primary" @click="showNewScript">🆕 新建脚本</n-button>
      </div>
    </aside>

    <!-- Right: Results -->
    <main class="studio-main">
      <!-- Empty state -->
      <EmptyState
        v-if="!resultContent && !isLoading && isNewScript"
        icon="🎬"
        title="AI 视界工坊"
        description="输入产品信息，选择模板风格和目标平台，AI 帮你生成可直接拍摄的专业分镜脚本"
      >
        <template #actions>
          <div class="feature-cards">
            <div class="feature-card">
              <div class="fc-icon">📋</div>
              <div class="fc-title">分镜表</div>
              <div class="fc-desc">镜号/时长/画面/口播</div>
            </div>
            <div class="feature-card">
              <div class="fc-icon">🎤</div>
              <div class="fc-title">口播稿</div>
              <div class="fc-desc">完整逐字文案</div>
            </div>
            <div class="feature-card">
              <div class="fc-icon">🎥</div>
              <div class="fc-title">拍摄建议</div>
              <div class="fc-desc">B-roll/转场/字幕</div>
            </div>
            <div class="feature-card">
              <div class="fc-icon">📊</div>
              <div class="fc-title">平台适配</div>
              <div class="fc-desc">5平台差异化建议</div>
            </div>
          </div>
        </template>
      </EmptyState>

      <!-- Empty history -->
      <EmptyState
        v-else-if="!resultContent && !isLoading && !isNewScript"
        icon="📝"
        title="选择一个历史脚本"
        description="从左侧列表中选择一个之前生成的脚本查看，或者点击新建开始创作"
      />

      <!-- Loading state -->
      <LoadingSpinner
        v-else-if="isLoading"
        :platforms="[targetPlatform]"
      />

      <!-- Result state -->
      <div v-else class="studio-result">
        <div class="result-toolbar">
          <h3>{{ isNewScript ? '📋 生成结果' : '📋 ' + (currentHistoryTitle || '历史脚本') }}</h3>
          <n-space>
            <n-button size="small" @click="copyAll">📋 复制</n-button>
            <n-button size="small" @click="exportMD">⬇ 导出 MD</n-button>
            <n-divider vertical />
            <n-button size="small" type="warning" @click="showTTSModal = true" :disabled="!currentSessionId">🎙️ AI配音</n-button>
            <n-button size="small" type="info" @click="showSubtitleModal = true" :disabled="!currentSessionId">📝 字幕导出</n-button>
            <n-button size="small" type="success" @click="showGuideModal = true">📖 使用指南</n-button>
            <n-button size="small" type="error" @click="showVideoModal = true" :disabled="!currentSessionId">🎬 AI视频</n-button>
            <n-divider vertical />
            <n-button size="small" v-if="!isNewScript" type="primary" @click="showNewScript">🆕 新建</n-button>
            <n-button size="small" v-else @click="handleRegenerate">🔄 重新生成</n-button>
          </n-space>
        </div>
        <div class="result-scroll">
          <div v-html="renderMd(resultContent)" class="md-content" />
        </div>
      </div>
    </main>

    <!-- ═══════════════════════════════════════════════════════════════════
         Modal Dialogs: TTS / Subtitle / Video / CapCut
         ═══════════════════════════════════════════════════════════════════ -->

    <!-- TTS Modal -->
    <n-modal v-model:show="showTTSModal" preset="card" title="🎙️ AI配音 — 生成口播音频" style="max-width:580px;" :mask-closable="false">
      <n-space vertical>
        <n-form-item label="语音选择">
          <n-select
            v-model:value="ttsVoice"
            :options="ttsVoiceOptions"
            placeholder="选择语音角色"
            filterable
          />
        </n-form-item>
        <n-form-item label="语速">
          <n-slider v-model:value="ttsSpeed" :min="-30" :max="30" :step="5"
            :format-tooltip="(v: number) => (v >= 0 ? '+' : '') + v + '%'" />
        </n-form-item>
        <!-- TTS Progress -->
        <n-form-item v-if="ttsLoading" label="生成进度">
          <n-progress type="line" :percentage="ttsProgress" :indicator-placement="'inside'"
            :status="ttsProgress === 100 ? 'success' : 'default'" />
          <p style="color:var(--text-muted);font-size:12px;margin:4px 0 0;">{{ ttsProgressText }}</p>
        </n-form-item>
        <!-- TTS Result: audio player + download -->
        <n-form-item v-if="ttsFileName && !ttsLoading" label="✅ 生成完成">
          <n-space vertical style="width:100%">
            <n-space>
              <n-tag type="success">{{ ttsFileName }}</n-tag>
              <n-button size="small" type="info" @click="downloadTTS">⬇ 下载 MP3</n-button>
            </n-space>
            <audio :src="ttsAudioUrl" controls style="width:100%;height:36px;border-radius:6px;margin-top:4px;" />
          </n-space>
        </n-form-item>
        <n-button type="primary" block :loading="ttsLoading" @click="handleTTS" :disabled="!currentSessionId">
          {{ ttsLoading ? '正在生成配音...' : '🔊 开始生成配音' }}
        </n-button>
        <p style="color:var(--text-muted);font-size:12px;margin:0;">
          💡 使用微软 Edge 神经网络语音，免费无限制。自动从脚本中提取口播文案。
        </p>
      </n-space>
    </n-modal>

    <!-- Subtitle Modal -->
    <n-modal v-model:show="showSubtitleModal" preset="card" title="📝 字幕导出" style="max-width:600px;" :mask-closable="false">
      <n-space vertical>
        <n-form-item label="字幕格式">
          <n-radio-group v-model:value="subtitleFormat">
            <n-radio value="srt">SRT（通用格式）</n-radio>
            <n-radio value="ass">ASS（高级样式）</n-radio>
          </n-radio-group>
        </n-form-item>
        <n-form-item label="语速 (字/秒)">
          <n-input-number v-model:value="subtitleWPS" :min="1" :max="10" :step="0.5" style="max-width:160px;" />
          <span style="margin-left:8px;color:var(--text-muted);font-size:12px;">默认 3.5，越小越慢</span>
        </n-form-item>
        <!-- Subtitle Progress -->
        <n-form-item v-if="subtitleLoading" label="导出进度">
          <n-progress type="line" :percentage="subtitleProgress" :indicator-placement="'inside'" :status="'success'" />
        </n-form-item>
        <!-- Subtitle Preview -->
        <n-form-item v-if="subtitlePreview && !subtitleLoading" label="📺 内容预览">
          <div class="subtitle-preview-box">{{ subtitlePreview }}</div>
        </n-form-item>
        <n-form-item v-if="subtitleFileName && !subtitleLoading" label="✅ 导出完成">
          <n-space vertical>
            <n-space>
              <n-tag :type="subtitleFormat==='srt'?'info':'success'">{{ subtitleFileName }} ({{ subtitleEntryCount }} 条)</n-tag>
              <n-button size="small" type="info" @click="downloadSubtitle">⬇ 下载文件</n-button>
            </n-space>
            <n-tag v-if="subtitleAudioAligned" type="success" size="small">
              🔗 逐镜精确对齐（{{ subtitleTotalDuration }}秒，基于配音实际时长）
            </n-tag>
            <n-tag v-else-if="subtitleAlignmentMode === 'scaled'" type="warning" size="small">
              ⚠️ 粗略对齐（总时长匹配，但各镜时间可能有偏差）
            </n-tag>
            <n-tag v-else type="warning" size="small">
              ⚠️ 未检测到配音，时间轴为估算值
            </n-tag>
          </n-space>
        </n-form-item>
        <n-button type="primary" block :loading="subtitleLoading" @click="handleSubtitleExport" :disabled="!currentSessionId">
          {{ subtitleLoading ? '正在导出...' : '📤 导出字幕文件' }}
        </n-button>
        <p style="color:var(--text-muted);font-size:12px;margin:0;">
          💡 自动解析分镜表中的口播文案和时间码，生成标准字幕文件。
        </p>
      </n-space>
    </n-modal>

    <!-- Video Modal -->
    <n-modal v-model:show="showVideoModal" preset="card" title="🎬 AI视频生成" style="max-width:660px;" :mask-closable="false">
      <n-space vertical>
        <n-alert type="info" :bordered="false">
          使用智谱 CogVideoX-2 模型，根据分镜的"画面内容"描述生成短视频片段。
        </n-alert>
        <n-form-item label="模型">
          <n-select
            v-model:value="videoModel"
            :options="[{label:'CogVideoX-2（高质量）', value:'cogvideox-2'},{label:'CogVideoX-Flash（快速便宜）', value:'cogvideox-flash'}]"
          />
        </n-form-item>
        <!-- Shot selection -->
        <n-form-item v-if="availableShotList.length > 0 && videoTasks.length === 0" label="选择分镜">
          <n-space vertical style="width:100%">
            <n-space>
              <n-button size="tiny" text @click="videoSelectAll">全选</n-button>
              <n-button size="tiny" text @click="videoDeselectAll">取消</n-button>
            </n-space>
            <div class="shot-check-grid">
              <n-checkbox v-for="s in availableShotList" :key="s.index" v-model:checked="videoShotSelection[s.index]" :disabled="s.blank">
                镜{{ s.index }}
              </n-checkbox>
            </div>
            <p style="color:var(--text-muted);font-size:11px;margin:0;">
              💡 建议一次只选 1 个，避免并发超限。已选 {{ videoSelectedCount }} / {{ availableShotList.length }}
            </p>
          </n-space>
        </n-form-item>
        <!-- Video tasks with progress bars -->
        <n-form-item v-if="videoTasks.length > 0" label="生成进度">
          <n-space vertical style="width:100%">
            <div v-for="vt in videoTasks" :key="vt.task_id || vt.index" class="video-task-row">
              <div class="video-task-header">
                <n-tag :type="vt.status==='submitted'||vt.status==='PROCESSING'?'info':vt.status==='SUCCESS'||vt.status==='succeeded'?'success':vt.status==='FAIL'?'error':'warning'" size="small">
                  镜号 {{ vt.index }}: {{ vt.status === 'PROCESSING' ? '生成中…' : vt.status === 'SUCCESS' ? '已完成' : vt.status === 'FAIL' ? '失败' : vt.status }}
                </n-tag>
                <span v-if="vt.status==='PROCESSING'||vt.status==='submitted'" style="font-size:12px;color:var(--text-muted);">预计 3-8 分钟</span>
              </div>
              <n-progress
                v-if="vt.status!=='SUCCESS'&&vt.status!=='succeeded'&&vt.status!=='FAIL'&&vt.status!=='error'"
                type="line"
                :percentage="vt.status==='PROCESSING'?videoProgress:15"
                :indicator-placement="'inside'"
                :status="vt.status==='PROCESSING'?'default':'default'"
                :processing="vt.status==='PROCESSING'"
              />
              <!-- Video preview player -->
              <div v-if="vt.video_url" class="video-preview-box">
                <video :src="vt.video_url" controls style="width:100%;max-height:300px;border-radius:8px;background:#000;" />
                <n-button size="small" type="primary" @click="openVideoUrl(vt.video_url)" style="margin-top:4px;">🔗 新窗口打开</n-button>
              </div>
              <p v-if="vt.error" style="color:var(--danger, #e74c3c);font-size:12px;margin:2px 0 0;">{{ vt.error }}</p>
            </div>
          </n-space>
        </n-form-item>
        <n-space>
          <n-button type="primary" :loading="videoLoading" @click="handleVideoGen" :disabled="!currentSessionId || videoSelectedCount === 0">
            {{ videoLoading ? '正在提交任务...' : (videoSelectedCount === 0 ? '请先选择分镜' : `🚀 生成 ${videoSelectedCount} 个视频`) }}
          </n-button>
          <n-button v-if="videoTasks.some(t => t.task_id && t.status!=='SUCCESS' && t.status!=='succeeded' && t.status!=='FAIL' && t.status!=='error')"
            @click="refreshAllVideoStatus" :loading="videoRefreshing">
            🔄 刷新全部状态
          </n-button>
        </n-space>
        <p style="color:var(--text-muted);font-size:12px;margin:0;">
          ⚠️ 视频生成需 3-8 分钟。建议一次只选 1 个，避免并发超限。CogVideoX-2 约 ¥1.25/个，Flash 更便宜。
        </p>
      </n-space>
    </n-modal>

    <!-- Workflow Guide Modal -->
    <n-modal v-model:show="showGuideModal" preset="card" title="📖 搭配剪映使用指南" style="max-width:520px;" :mask-closable="false">
      <n-space vertical>
        <n-alert type="info" :bordered="false">
          四个功能的完整搭配流程：从 AI 脚本 → 配音 → 视频 → 字幕 → 剪映剪辑，一站式搞定。
        </n-alert>
        <n-divider title="🎬 完整工作流：四个功能搭配使用" />
        <div class="guide-steps">
          <div class="guide-step">
            <div class="guide-step-num">1</div>
            <div class="guide-step-text">
              <strong>AI 生成脚本</strong> — 输入产品信息，AI 输出分镜脚本 + 口播稿
            </div>
          </div>
          <div class="guide-step">
            <div class="guide-step-num">2</div>
            <div class="guide-step-text">
              <strong>生成配音</strong> <n-tag type="warning" size="small">🎙️ AI配音</n-tag> — 选语音角色，自动合成口播 MP3
            </div>
          </div>
          <div class="guide-step">
            <div class="guide-step-num">3</div>
            <div class="guide-step-text">
              <strong>AI 生成视频</strong> <n-tag type="error" size="small">🎬 AI视频</n-tag> — 按分镜生成视频片段（需智谱 API Key）
            </div>
          </div>
          <div class="guide-step">
            <div class="guide-step-num">4</div>
            <div class="guide-step-text">
              <strong>导出字幕</strong> <n-tag type="info" size="small">📝 字幕导出</n-tag> — 选 SRT 格式下载
            </div>
          </div>
          <div class="guide-step">
            <div class="guide-step-num">5</div>
            <div class="guide-step-text">
              <strong>打开剪映</strong> → 新建空白项目 → 拖入 MP3（音频轨）+ 视频片段 + SRT（字幕轨）
            </div>
          </div>
          <div class="guide-step">
            <div class="guide-step-num">6</div>
            <div class="guide-step-text">
              🎬 <strong>完成！</strong>微调转场 + 贴纸特效 → 导出发布
            </div>
          </div>
        </div>
        <n-divider />
        <n-space vertical style="font-size:11px;color:var(--text-muted);text-align:center;">
          <p style="margin:0;">💡 SRT 字幕时间轴与配音口播自动同步</p>
          <p style="margin:0;">🎬 AI 视频基于分镜「画面内容」生成，需 <strong>智谱 ZHIPU_API_KEY</strong>（注册送 50 元免费额度）</p>
          <p style="margin:0;">📹 不想用 AI 视频？也可以用分镜脚本自己拍摄，然后拖入剪映剪辑</p>
        </n-space>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import MarkdownIt from 'markdown-it'
import { chatApi, type Session } from '../api/chat'
import { generationApi, type TTSVoice } from '../api/generation'
import { useAuthStore } from '../stores/auth'
import { PLATFORM_COLORS, PLATFORM_MAP } from '../assets/styles/tokens'
import EmptyState from '../components/EmptyState.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const message = useMessage()
const authStore = useAuthStore()

function authHeaders(): Record<string, string> {
  return { Authorization: `Bearer ${authStore.token}` }
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ── Form state ─────────────────────────────────────────────────────────
const productName = ref('')
const sellingPoints = ref('')
const price = ref('')
const templateStyle = ref('带货')
const targetPlatform = ref('抖音')
const isLoading = ref(false)
const resultContent = ref('')
const streamingContent = ref('')

// ── History state ──────────────────────────────────────────────────────
const historySessions = ref<Session[]>([])
const currentSessionId = ref<string | null>(null)
const currentHistoryTitle = ref('')
const isNewScript = ref(true)
const historySearch = ref('')
const batchMode = ref(false)
const selectedIds = reactive(new Set<string>())

// ── TTS state ──────────────────────────────────────────────────────────
const showTTSModal = ref(false)
const ttsLoading = ref(false)
const ttsProgress = ref(0)
const ttsProgressText = ref('')
const ttsVoice = ref('zh-CN-XiaoxiaoNeural')
const ttsVoiceOptions = ref<Array<{ label: string; value: string }>>([])
const ttsSpeed = ref(0)
const ttsFileName = ref('')
const ttsAudioUrl = ref('')

// ── Subtitle state ─────────────────────────────────────────────────────
const showSubtitleModal = ref(false)
const subtitleLoading = ref(false)
const subtitleProgress = ref(0)
const subtitleFormat = ref<'srt' | 'ass'>('srt')
const subtitleWPS = ref(3.5)
const subtitleFileName = ref('')
const subtitleEntryCount = ref(0)
const subtitlePreview = ref('')
const subtitleAudioAligned = ref(false)
const subtitleAlignmentMode = ref('estimated')  // "per_shot" | "scaled" | "estimated"
const subtitleTotalDuration = ref(0)

// ── Video state ────────────────────────────────────────────────────────
const showVideoModal = ref(false)
const videoLoading = ref(false)
const videoRefreshing = ref(false)
const videoProgress = ref(30)
const videoModel = ref('cogvideox-2')
const videoTasks = ref<Array<{ index?: number; task_id?: string; status: string; video_url?: string; error?: string }>>([])
const videoShotSelection = ref<Record<number, boolean>>({})
const availableShotList = ref<Array<{ index: number; blank: boolean }>>([])
let videoPollTimer: ReturnType<typeof setInterval> | null = null

const videoSelectedCount = computed(() =>
  Object.values(videoShotSelection.value).filter(Boolean).length
)

function videoSelectAll() {
  availableShotList.value.forEach(s => { videoShotSelection.value[s.index] = !s.blank })
}
function videoDeselectAll() {
  availableShotList.value.forEach(s => { videoShotSelection.value[s.index] = false })
}

// Auto-populate shot list when video modal opens
watch(showVideoModal, (open) => {
  if (open && resultContent.value) {
    // Parse shots from markdown table for selection
    const lines = resultContent.value.split('\n')
    const shots: Array<{ index: number; blank: boolean }> = []
    let inTable = false
    let idxCol = -1, visualCol = -1
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed.startsWith('|')) continue
      const cells = trimmed.split('|').filter(c => c.trim())
      if (!inTable) {
        const header = cells.join(' ')
        if (header.includes('镜号') || header.includes('画面')) {
          inTable = true
          cells.forEach((c, i) => {
            const cl = c.trim()
            if (cl.includes('镜号')) idxCol = i
            if (cl.includes('画面')) visualCol = i
          })
        }
        continue
      }
      if (/^:?-+:?$/.test(cells[0].trim())) continue
      try {
        const idx = parseInt(String(cells[idxCol] || '').replace(/[^\d]/g, ''))
        if (idx > 0 && idx <= 20) shots.push({ index: idx, blank: !cells[visualCol]?.trim() })
      } catch { /* skip */ }
      if (shots.length > 15) break
    }
    availableShotList.value = shots
    // Default: select first shot only
    shots.forEach(s => { videoShotSelection.value[s.index] = s.index === 1 })
  }
  if (!open) {
    stopVideoPolling()
  }
})

// ── Guide state ───────────────────────────────────────────────────────
const showGuideModal = ref(false)

const filteredHistory = computed(() => {
  if (!historySearch.value.trim()) return historySessions.value
  const q = historySearch.value.toLowerCase()
  return historySessions.value.filter(s => (s.title || '').toLowerCase().includes(q))
})

const platformOptions = PLATFORM_MAP.map(p => p.label)

function platformColor(p: string): string {
  return PLATFORM_COLORS[p] || '#C8A951'
}

// ── Markdown renderer ──────────────────────────────────────────────────
const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
function renderMd(t: string) { return t ? md.render(t) : '' }

function formatDate(d: string): string {
  if (!d) return ''
  const dt = new Date(d)
  const now = new Date()
  const diff = now.getTime() - dt.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return dt.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

// Clean title to show product name only
function cleanTitle(title: string | null): string {
  if (!title) return '未命名脚本'
  // Title format: "产品：xxx\n核心卖点：yyy\n..."
  const m = title.match(/产品[:：]\s*(.+)/)
  if (m) return m[1].trim().replace(/[\n\r]+/g, ' ').substring(0, 30)
  // If title is just the product name + platform + style, keep it
  return title.replace(/[\n\r]+/g, ' ').substring(0, 30) || '未命名脚本'
}

function openVideoUrl(url: string) { window.open(url, '_blank') }

// ── Batch mode ──────────────────────────────────────────────────────────
function toggleBatchMode() {
  batchMode.value = !batchMode.value
  selectedIds.clear()
}

function toggleSelect(id: string) {
  if (selectedIds.has(id)) selectedIds.delete(id); else selectedIds.add(id)
}

async function batchDelete() {
  if (selectedIds.size === 0) return
  try {
    const ids = Array.from(selectedIds)
    await chatApi.batchDeleteSessions(ids)
    historySessions.value = historySessions.value.filter(s => !selectedIds.has(s.id))
    if (selectedIds.has(currentSessionId.value || '')) showNewScript()
    const count = ids.length
    selectedIds.clear()
    batchMode.value = false
    message.success(`已删除 ${count} 个会话`)
  } catch {
    message.error('批量删除失败')
  }
}

// ── Quick fill ─────────────────────────────────────────────────────────
function quickFill(name: string, points: string, p: string, style: string) {
  productName.value = name
  sellingPoints.value = points
  price.value = p
  templateStyle.value = style
}

function showNewScript() {
  isNewScript.value = true
  currentSessionId.value = null
  currentHistoryTitle.value = ''
  resultContent.value = ''
  streamingContent.value = ''
  productName.value = ''
  sellingPoints.value = ''
  price.value = ''
  templateStyle.value = '带货'
  targetPlatform.value = '抖音'
}

// ── History actions ────────────────────────────────────────────────────
async function loadHistory(session: Session) {
  isNewScript.value = false
  currentSessionId.value = session.id
  currentHistoryTitle.value = session.title || '未命名脚本'
  resultContent.value = ''

  try {
    const res = await chatApi.getMessages(session.id)
    const msgs = res.data
    const assistantMsg = [...msgs].reverse().find(m => m.role === 'assistant')
    if (assistantMsg) {
      resultContent.value = assistantMsg.content
    } else {
      resultContent.value = '（该会话暂无生成内容）'
    }
  } catch {
    message.error('加载历史记录失败')
  }
}

async function deleteHistory(sessionId: string) {
  try {
    await chatApi.deleteSession(sessionId)
    historySessions.value = historySessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) showNewScript()
    message.success('已删除')
  } catch {
    message.error('删除失败')
  }
}

async function loadHistoryList() {
  try {
    const res = await chatApi.listSessions(1, 50)
    historySessions.value = res.data
  } catch { /* silent */ }
}

// ── Generate ───────────────────────────────────────────────────────────
async function handleGenerate() {
  if (!productName.value.trim() || isLoading.value) return

  isLoading.value = true
  streamingContent.value = ''
  resultContent.value = ''

  try {
    const title = `${productName.value}_${templateStyle.value}_${targetPlatform.value}`
    const sRes = await chatApi.createSession(title)
    const sessionId = sRes.data.id
    currentSessionId.value = sessionId

    const parts = [`产品: ${productName.value}`]
    if (sellingPoints.value.trim()) parts.push(`核心卖点:\n${sellingPoints.value}`)
    if (price.value.trim()) parts.push(`价格: ${price.value}`)
    parts.push(`模板风格: ${templateStyle.value}`)
    parts.push(`目标平台: ${targetPlatform.value}`)
    const fullQuestion = parts.join('\n\n')

    const response = await chatApi.askQuestion(sessionId, fullQuestion, authStore.token)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body?.getReader()
    if (!reader) throw new Error('Response body not readable')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6)
        if (data === '[DONE]') continue
        try {
          const event = JSON.parse(data)
          if (event.type === 'token') {
            streamingContent.value += event.content || ''
          } else if (event.type === 'done') {
            resultContent.value = event.data?.full_answer || streamingContent.value
          }
        } catch { /* skip malformed */ }
      }
    }

    await loadHistoryList()
    isNewScript.value = false
  } catch (e: any) {
    message.error('生成失败: ' + (e.message || '请重试'))
    if (!resultContent.value && streamingContent.value) {
      resultContent.value = streamingContent.value
    }
    if (!resultContent.value) {
      resultContent.value = '抱歉，分镜脚本生成失败，请重试。'
    }
    isNewScript.value = false
  } finally {
    isLoading.value = false
  }
}

function copyAll() {
  if (!resultContent.value) return
  navigator.clipboard.writeText(resultContent.value).then(() => message.success('已复制'))
}

function exportMD() {
  if (!resultContent.value) return
  const name = productName.value || currentHistoryTitle.value || '未命名'
  const blob = new Blob([resultContent.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `分镜脚本_${name}_${new Date().toISOString().slice(0, 10)}.md`
  a.click()
  URL.revokeObjectURL(url)
  message.success('已导出')
}

function handleRegenerate() {
  resultContent.value = ''
  streamingContent.value = ''
  handleGenerate()
}

// ── TTS handlers ───────────────────────────────────────────────────────
async function loadVoices() {
  if (ttsVoiceOptions.value.length > 0) return
  try {
    const res = await generationApi.listVoices('zh')
    const voices = res.data.voices as TTSVoice[]
    const groups: Record<string, { label: string; value: string }[]> = {
      mandarin: [],
      cantonese: [],
      taiwanese: [],
    }
    const groupLabel: Record<string, string> = {
      mandarin: '🇨🇳 普通话',
      cantonese: '🇭🇰 粤语',
      taiwanese: '🇹🇼 台普',
    }
    for (const v of voices) {
      const tag = v.tags?.[0] || 'mandarin'
      if (!groups[tag]) groups[tag] = []
      groups[tag].push({
        label: `${v.name} · ${v.style}`,
        value: v.id,
      })
    }
    const grouped: any[] = []
    for (const [key, opts] of Object.entries(groups)) {
      if (opts.length === 0) continue
      grouped.push({ label: groupLabel[key] || key, value: `_group_${key}`, type: 'group', children: opts })
    }
    ttsVoiceOptions.value = grouped
  } catch { /* keep defaults */ }
}

async function handleTTS() {
  if (!currentSessionId.value) return
  ttsLoading.value = true
  ttsFileName.value = ''
  ttsAudioUrl.value = ''
  ttsProgress.value = 5
  ttsProgressText.value = '正在连接TTS服务…'
  try {
    const res = await generationApi.generateTTS(
      currentSessionId.value,
      ttsVoice.value,
      (ttsSpeed.value >= 0 ? '+' : '') + ttsSpeed.value + '%',
    )
    ttsProgress.value = 100
    ttsProgressText.value = `生成完成！(${(res.data as any).shot_count || 1} 个分镜配音)`
    ttsFileName.value = res.data.filename
    ttsAudioUrl.value = generationApi.getTTSDownloadUrl(res.data.filename)
    message.success('配音生成成功！')
  } catch (e: any) {
    message.error('配音生成失败: ' + (e.response?.data?.detail || e.message || '请重试'))
  } finally {
    ttsLoading.value = false
  }
}

async function downloadTTS() {
  if (!ttsFileName.value) return
  try {
    const url = generationApi.getTTSDownloadUrl(ttsFileName.value)
    const res = await fetch(url, { headers: authHeaders() })
    if (!res.ok) throw new Error('下载失败')
    const blob = await res.blob()
    triggerDownload(blob, ttsFileName.value)
  } catch { message.error('下载失败') }
}

// ── Subtitle handlers ──────────────────────────────────────────────────
async function handleSubtitleExport() {
  if (!currentSessionId.value) return
  subtitleLoading.value = true
  subtitleFileName.value = ''
  subtitlePreview.value = ''
  subtitleEntryCount.value = 0
  subtitleProgress.value = 0
  const progressTimer = setInterval(() => {
    if (subtitleProgress.value < 88) subtitleProgress.value += Math.random() * 15 + 5
  }, 200)
  try {
    const res = await generationApi.exportSubtitles(
      currentSessionId.value,
      subtitleFormat.value,
      subtitleWPS.value,
    )
    subtitleProgress.value = 100
    subtitleFileName.value = res.data.filename
    subtitleEntryCount.value = res.data.entry_count
    subtitlePreview.value = (res.data as any).preview || ''
    subtitleAudioAligned.value = res.data.audio_aligned || false
    subtitleAlignmentMode.value = (res.data as any).alignment_mode || (res.data.audio_aligned ? 'scaled' : 'estimated')
    subtitleTotalDuration.value = res.data.total_duration_sec || 0
    const alignedMsg = res.data.audio_aligned ? '，已逐镜精确对齐配音' : ''
    message.success(`${subtitleFormat.value.toUpperCase()} 字幕导出成功！(${res.data.entry_count} 条)${alignedMsg}`)
  } catch (e: any) {
    message.error('字幕导出失败: ' + (e.response?.data?.detail || e.message || '请重试'))
  } finally {
    clearInterval(progressTimer)
    subtitleLoading.value = false
  }
}

async function downloadSubtitle() {
  if (!subtitleFileName.value) return
  try {
    const url = generationApi.getSubtitleDownloadUrl(subtitleFileName.value)
    const res = await fetch(url, { headers: authHeaders() })
    if (!res.ok) throw new Error('下载失败')
    const blob = await res.blob()
    triggerDownload(blob, subtitleFileName.value)
  } catch { message.error('下载失败') }
}

// ── Video handlers ─────────────────────────────────────────────────────
async function handleVideoGen() {
  if (!currentSessionId.value) return
  videoLoading.value = true
  videoTasks.value = []
  // Build selected shot indexes
  const selectedIndexes = Object.entries(videoShotSelection.value)
    .filter(([_, v]) => v)
    .map(([k, _]) => parseInt(k))
  if (selectedIndexes.length === 0) {
    message.warning('请至少选择一个分镜')
    videoLoading.value = false
    return
  }
  try {
    const res = await generationApi.submitVideo(currentSessionId.value, videoModel.value, selectedIndexes)
    videoTasks.value = res.data.tasks.map((t: any) => ({ ...t, status: t.status }))
    message.success(`已提交 ${res.data.count} 个视频生成任务`)
    startVideoPolling()
  } catch (e: any) {
    message.error('视频生成提交失败: ' + (e.response?.data?.detail || e.message || '请重试'))
  } finally {
    videoLoading.value = false
  }
}

function startVideoPolling() {
  stopVideoPolling()
  videoPollTimer = setInterval(async () => {
    const pending = videoTasks.value.filter(
      t => t.task_id && t.status !== 'SUCCESS' && t.status !== 'succeeded' && t.status !== 'FAIL' && t.status !== 'error'
    )
    if (pending.length === 0) { stopVideoPolling(); return }
    for (const vt of pending) {
      try {
        const res = await generationApi.getVideoStatus(vt.task_id!)
        const idx = videoTasks.value.findIndex(t => t.task_id === vt.task_id)
        if (idx >= 0) {
          videoTasks.value[idx] = { ...videoTasks.value[idx], ...res.data }
          if (res.data.status === 'SUCCESS' || res.data.status === 'succeeded') {
            message.success(`镜号 ${vt.index} 视频生成完成！`)
          }
        }
        // Animate progress
        if (res.data.status === 'PROCESSING') videoProgress.value = Math.min(videoProgress.value + 5, 88)
      } catch { /* ignore poll errors */ }
    }
  }, 20000)
}

function stopVideoPolling() {
  if (videoPollTimer) { clearInterval(videoPollTimer); videoPollTimer = null }
}

async function checkVideoStatus(vt: any) {
  if (!vt.task_id) return
  try {
    const res = await generationApi.getVideoStatus(vt.task_id)
    const idx = videoTasks.value.findIndex(t => t.task_id === vt.task_id)
    if (idx >= 0) {
      videoTasks.value[idx] = { ...videoTasks.value[idx], ...res.data }
    }
    if (res.data.status === 'SUCCESS' || res.data.status === 'succeeded') {
      message.success(`镜号 ${vt.index} 视频生成完成！`)
    }
  } catch (e: any) {
    message.error('状态查询失败')
  }
}

async function refreshAllVideoStatus() {
  videoRefreshing.value = true
  const pending = videoTasks.value.filter(t => t.task_id)
  for (const vt of pending) {
    await checkVideoStatus(vt)
  }
  videoRefreshing.value = false
}

// Cleanup on unmount
onBeforeUnmount(() => { stopVideoPolling() })

onMounted(() => {
  loadHistoryList()
  loadVoices()
})
</script>

<style scoped>
.studio-page { display: flex; height: 100%; }

/* ═══ Sidebar ═══ */
.studio-sidebar {
  width: 340px; min-width: 340px; padding: 20px;
  background: var(--bg-surface, #F0EEE6);
  border-right: 1px solid var(--border, #E8E4D8);
  display: flex; flex-direction: column; gap: 6px;
  overflow-y: auto;
}

/* Section header */
.section-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px;
}
.history-section { margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
.history-search { margin-bottom: 8px; }
.history-list { max-height: 240px; overflow-y: auto; }
.history-item {
  display: flex; align-items: center; gap: 6px;
  padding: 9px 12px; border-radius: 8px; cursor: pointer;
  transition: all .15s; margin-bottom: 2px; position: relative;
}
.history-item:hover { background: rgba(200,169,81,.08); }
.history-item.active { background: var(--primary-light, #F5E6C8); border-left: 3px solid var(--primary); }
.hi-title {
  flex: 1; font-size: 13px; font-weight: 500; color: var(--text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.hi-date { font-size: 11px; color: var(--text-muted); white-space: nowrap; }
.hi-delete { opacity: 0; transition: opacity .15s; }
.history-item:hover .hi-delete { opacity: 1; }

.sidebar-header { margin-bottom: 6px; }
.sidebar-header h2 { margin: 0; font-size: 18px; font-weight: 700; color: var(--text-primary); }
.sidebar-header p { margin: 4px 0 0; font-size: 13px; color: var(--text-secondary); }

.history-mode-header {
  margin-top: 12px; display: flex; flex-direction: column; gap: 8px; align-items: flex-start;
}
.history-mode-header p { margin: 0; color: var(--text-secondary); font-size: 13px; }

.input-section { margin-top: 14px; }
.input-label {
  display: block; font-size: 13px; font-weight: 600;
  color: var(--text-primary); margin-bottom: 6px;
}
.required { color: #E50914; }

/* Platform chips */
.platform-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.plat-chip {
  padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;
  border: 1.5px solid var(--pc); color: var(--pc);
  cursor: pointer; transition: all .15s;
}
.plat-chip:hover { opacity: .8; }
.plat-chip.active { background: var(--pc); color: #fff; }

.radio-label { font-weight: 600; }
.radio-desc { font-size: 12px; color: var(--text-secondary); }

.gen-btn { margin-top: 20px; height: 48px; font-size: 16px; font-weight: 700; border-radius: 12px; }

.quick-templates { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border); }
.quick-btn { font-size: 13px; padding: 4px 0; }

/* ═══ Main area ═══ */
.studio-main { flex: 1; display: flex; flex-direction: column; min-width: 0; background: var(--bg-body); }

/* Feature cards */
.feature-cards { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
.feature-card {
  padding: 16px 18px; background: var(--bg-card);
  border-radius: 12px; text-align: center; min-width: 110px;
  border-left: 3px solid var(--primary);
  box-shadow: var(--shadow-sm);
  transition: all .2s;
}
.feature-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow);
}
.feature-card:nth-child(1) .fc-icon { color: #C8A951; }
.feature-card:nth-child(2) .fc-icon { color: #E8A840; }
.feature-card:nth-child(3) .fc-icon { color: #D4956B; }
.feature-card:nth-child(4) .fc-icon { color: #A0C4A0; }
.fc-icon { font-size: 28px; margin-bottom: 4px; }
.fc-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.fc-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

/* Result */
.studio-result { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.result-toolbar {
  padding: 14px 24px; border-bottom: 2px solid var(--primary-light);
  display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;
  background: var(--bg-card);
}
.result-toolbar h3 { margin: 0; font-size: 16px; font-weight: 600; color: var(--text-primary); }
.result-scroll { flex: 1; overflow-y: auto; padding: 28px 36px; }

/* ═══ Markdown Content ═══ */
.md-content { max-width: 860px; margin: 0 auto; font-size: 15px; line-height: 1.85; color: var(--text-primary); }

/* Headings */
.md-content :deep(h1) { margin: 24px 0 12px; font-size: 1.5em; font-weight: 700; }
.md-content :deep(h2) {
  margin: 20px 0 10px; font-size: 1.25em; font-weight: 700;
  background: linear-gradient(90deg, var(--primary) 0%, var(--primary) 40px, var(--border) 40px, var(--border) 100%);
  background-position: bottom;
  background-size: 100% 2px;
  background-repeat: no-repeat;
  padding-bottom: 8px;
}
.md-content :deep(h3) { margin: 16px 0 8px; font-size: 1.1em; font-weight: 600; }
.md-content :deep(p) { margin: 0 0 10px; }
.md-content :deep(strong) { font-weight: 700; color: var(--primary); }
.md-content :deep(ul), .md-content :deep(ol) { margin: 6px 0; padding-left: 22px; }
.md-content :deep(li) { margin: 3px 0; }

/* Tables */
.md-content :deep(table) {
  border-collapse: collapse; width: 100%; margin: 14px 0;
  font-size: 14px; border-radius: 8px; overflow: hidden;
}
.md-content :deep(th) {
  background: var(--primary); color: #fff;
  padding: 10px 14px; text-align: left; font-weight: 600;
}
.md-content :deep(td) {
  padding: 9px 14px; border-bottom: 1px solid var(--border);
}
.md-content :deep(tr:nth-child(even) td) { background: var(--bg-surface); }
.md-content :deep(tr:hover td) { background: var(--primary-light); }

/* Code */
.md-content :deep(code) {
  background: var(--bg-surface); padding: 2px 6px;
  border-radius: 4px; font-size: 13px; font-family: "Cascadia Code","Fira Code",Consolas,monospace;
}
.md-content :deep(pre) {
  background: #1A1A24; color: #e0d0c0;
  padding: 16px; border-radius: 10px; overflow-x: auto; margin: 12px 0;
  border: 1px solid var(--border);
}
.md-content :deep(pre code) { background: transparent; padding: 0; color: inherit; }

/* Blockquote */
.md-content :deep(blockquote) {
  border-left: 3px solid var(--primary); padding: 8px 16px;
  margin: 12px 0; background: var(--bg-surface); border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
}

/* Links */
.md-content :deep(a) { color: var(--primary); }

/* ═══ Scrollbar ═══ */
.result-scroll::-webkit-scrollbar,
.history-list::-webkit-scrollbar,
.studio-sidebar::-webkit-scrollbar { width: 5px; }
.result-scroll::-webkit-scrollbar-thumb,
.history-list::-webkit-scrollbar-thumb,
.studio-sidebar::-webkit-scrollbar-thumb { background: #c8b880; border-radius: 5px; }

/* ═══ Dark Mode ═══ */
[data-theme="dark"] .studio-sidebar { background: #15151E; border-right-color: var(--border); }
[data-theme="dark"] .sidebar-header h2 { color: #E8E8F0; }
[data-theme="dark"] .history-item:hover { background: rgba(200,169,81,.06); }
[data-theme="dark"] .history-item.active { background: rgba(200,169,81,.12); border-left-color: var(--primary); }
[data-theme="dark"] .hi-title { color: #CCC; }
[data-theme="dark"] .studio-main { background: #0D0D14; }
[data-theme="dark"] .feature-card { background: #1A1A25; }
[data-theme="dark"] .feature-card:hover { background: #22222E; }
[data-theme="dark"] .fc-title { color: #DDD; }
[data-theme="dark"] .result-toolbar { background: #14141E; border-bottom-color: rgba(200,169,81,.15); }
[data-theme="dark"] .result-toolbar h3 { color: #E8E8F0; }
[data-theme="dark"] .md-content { color: #D8D8E8; }
[data-theme="dark"] .md-content :deep(h2) { color: #E8E8F0; }
[data-theme="dark"] .md-content :deep(h3) { color: #DDD; }
[data-theme="dark"] .md-content :deep(th) { background: #3A3020; }
[data-theme="dark"] .md-content :deep(tr:nth-child(even) td) { background: #15151E; }
[data-theme="dark"] .md-content :deep(tr:hover td) { background: #1E1A12; }
[data-theme="dark"] .md-content :deep(code) { background: #1A1A25; }
[data-theme="dark"] .md-content :deep(pre) { background: #0A0A12; border-color: #2A2A35; }
[data-theme="dark"] .md-content :deep(blockquote) { background: #141418; }
[data-theme="dark"] .md-content :deep(td) { border-bottom-color: #2A2A35; }
[data-theme="dark"] .quick-templates { border-top-color: #2A2A35; }
[data-theme="dark"] .result-scroll::-webkit-scrollbar-thumb { background: #4A4A5A; }
[data-theme="dark"] .history-list::-webkit-scrollbar-thumb { background: #4A4A5A; }
[data-theme="dark"] .studio-sidebar::-webkit-scrollbar-thumb { background: #4A4A5A; }
[data-theme="dark"] .history-section { border-bottom-color: #2A2A35; }
[data-theme="dark"] .input-label { color: #ccc; }

/* ═══ Preview boxes ═══ */
.subtitle-preview-box {
  background: #1A1A24; color: #e0d0c0; border: 1px solid var(--border);
  border-radius: 8px; padding: 12px 16px; font-family: "Cascadia Code","Fira Code",Consolas,monospace;
  font-size: 12px; line-height: 1.6; max-height: 220px; overflow-y: auto; white-space: pre-wrap;
  width: 100%;
}
.video-task-row {
  background: var(--bg-surface); border-radius: 8px; padding: 10px 14px;
  border: 1px solid var(--border); display: flex; flex-direction: column; gap: 6px;
}
.video-task-header {
  display: flex; justify-content: space-between; align-items: center;
}
.video-preview-box {
  margin-top: 4px; border-radius: 8px; overflow: hidden;
}
.shot-check-grid {
  display: flex; flex-wrap: wrap; gap: 10px 16px;
}
[data-theme="dark"] .subtitle-preview-box { background: #0A0A12; }
[data-theme="dark"] .video-task-row { background: #14141E; }

/* ═══ Guide Steps ═══ */
.guide-steps { display: flex; flex-direction: column; gap: 10px; }
.guide-step {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; background: var(--bg-surface); border-radius: 8px;
  border-left: 3px solid var(--primary);
}
.guide-step-num {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.guide-step-text { font-size: 13px; color: var(--text-primary); line-height: 1.5; }
.guide-step-text strong { color: var(--primary); }
[data-theme="dark"] .guide-step { background: #1A1A25; }
</style>
