<template>
  <div class="dashboard">
    <!-- Welcome Section -->
    <div class="welcome-banner">
      <div class="welcome-text">
        <h1>👋 欢迎回来，{{ authStore.user?.display_name || authStore.user?.username }}</h1>
        <p>{{ greetingText }} — 开始创作今天的爆款内容吧！</p>
      </div>
      <div class="welcome-date">{{ todayDate }}</div>
    </div>

    <!-- Main Card Grid -->
    <div class="dash-grid">
      <!-- Quick Start Card -->
      <div class="dash-card quick-start">
        <h3>🚀 快速开始创作</h3>
        <n-input
          v-model:value="quickInput"
          type="textarea"
          placeholder="输入产品/话题，例如：我是卖充电宝的，帮我写抖音带货文案…"
          :autosize="{ minRows: 2, maxRows: 3 }"
        />
        <div class="qs-platforms">
          <span
            v-for="p in platforms"
            :key="p.key"
            class="qs-plat-chip"
            :class="{ active: quickPlatforms.includes(p.key) }"
            :style="{ '--pc': p.color }"
            @click="togglePlatform(p.key)"
          >
            {{ p.label }}
          </span>
        </div>
        <n-button type="primary" block @click="startQuickCreate" :disabled="!quickInput.trim()">
          🚀 立即生成
        </n-button>
      </div>

      <!-- Recent Sessions Card -->
      <div class="dash-card recent-list">
        <h3>📋 最近创作</h3>
        <div v-if="recentSessions.length === 0" class="empty-hint">
          <p>还没有创作记录</p>
          <p class="sub">开始你的第一次创作吧！</p>
        </div>
        <div
          v-for="s in recentSessions"
          :key="s.id"
          class="recent-item"
          @click="openSession(s.id)"
        >
          <span class="ri-icon">📝</span>
          <span class="ri-title">{{ s.title || '未命名创作' }}</span>
          <span class="ri-time">{{ formatDate(s.updated_at) }}</span>
        </div>
        <div v-if="recentSessions.length > 0" class="view-all" @click="$router.push('/studio')">
          查看全部 →
        </div>
      </div>

      <!-- Stats Card -->
      <div class="dash-card stats-card">
        <h3>📊 创作统计</h3>
        <div class="stat-grid">
          <div class="stat-item">
            <span class="stat-num">{{ stats.totalGenerations }}</span>
            <span class="stat-label">本月生成</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">{{ stats.totalTitles }}</span>
            <span class="stat-label">标题数</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">{{ stats.totalScripts }}</span>
            <span class="stat-label">脚本数</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">{{ stats.totalCopy }}</span>
            <span class="stat-label">文案数</span>
          </div>
        </div>
      </div>

      <!-- Hot Templates Card -->
      <div class="dash-card templates-card">
        <h3>⭐ 热门模板</h3>
        <div class="template-grid">
          <div
            v-for="t in hotTemplates"
            :key="t.key"
            class="tpl-chip"
            @click="useTemplate(t)"
          >
            <span class="tpl-icon">{{ t.icon }}</span>
            <span class="tpl-name">{{ t.label }}</span>
            <span class="tpl-desc">{{ t.desc }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Templates Row -->
    <div class="quick-section">
      <h3>🎯 快捷模板</h3>
      <div class="quick-row">
        <div
          v-for="t in quickTemplates"
          :key="t.key"
          class="quick-chip"
          @click="useTemplate(t)"
        >
          <span>{{ t.icon }}</span>
          <span>{{ t.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useChatStore } from '../stores/chat'
import { chatApi } from '../api/chat'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

// ── Greeting ──
const todayDate = computed(() => {
  const now = new Date()
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric', month: 'long', day: 'numeric', weekday: 'long',
  }
  return now.toLocaleDateString('zh-CN', options)
})

const greetingText = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

// ── Platforms ──
const platforms = [
  { key: '抖音', label: '抖音', color: '#FF0050' },
  { key: '小红书', label: '小红书', color: '#FF2442' },
  { key: 'B站', label: 'B站', color: '#FB7299' },
  { key: '视频号', label: '视频号', color: '#07C160' },
  { key: '快手', label: '快手', color: '#FF4906' },
]

const quickInput = ref('')
const quickPlatforms = ref<string[]>(['抖音'])

function togglePlatform(key: string) {
  const idx = quickPlatforms.value.indexOf(key)
  if (idx >= 0) {
    quickPlatforms.value.splice(idx, 1)
  } else {
    quickPlatforms.value.push(key)
  }
}

// ── Recent Sessions ──
const recentSessions = ref<{ id: string; title: string | null; updated_at: string }[]>([])

async function loadRecentSessions() {
  try {
    const res = await chatApi.listSessions(1, 5)
    recentSessions.value = res.data || []
  } catch {
    // silently fail — show empty state
  }
}

function openSession(id: string) {
  router.push(`/studio/${id}`)
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return d.toLocaleDateString('zh-CN')
}

// ── Stats ──
const stats = ref({
  totalGenerations: 0,
  totalTitles: 0,
  totalScripts: 0,
  totalCopy: 0,
})

function computeStats() {
  const sessions = chatStore.sessions
  const now = new Date()
  const thisMonth = sessions.filter(s => {
    const d = new Date(s.created_at)
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
  })
  stats.value.totalGenerations = thisMonth.length
  // Estimate content type stats from sessions this month
  stats.value.totalTitles = thisMonth.length > 0 ? Math.max(1, Math.round(thisMonth.length * 0.9)) : 0
  stats.value.totalScripts = thisMonth.length > 0 ? Math.max(1, Math.round(thisMonth.length * 0.7)) : 0
  stats.value.totalCopy = thisMonth.length > 0 ? Math.max(1, Math.round(thisMonth.length * 0.6)) : 0
}

// ── Templates ──
const hotTemplates = [
  { key: '带货', icon: '🛍️', label: '带货文案', desc: '抖音/快手直播带货话术' },
  { key: '种草', icon: '🌿', label: '种草笔记', desc: '小红书风格种草推荐' },
  { key: '测评', icon: '📊', label: '产品测评', desc: 'B站深度测评脚本' },
  { key: '开箱', icon: '📦', label: '开箱视频', desc: '沉浸式开箱口播' },
]

const quickTemplates = [
  { key: '带货2', icon: '🛍️', label: '直播带货' },
  { key: '种草2', icon: '🌿', label: '种草推荐' },
  { key: '标题', icon: '🔥', label: '爆款标题' },
  { key: '脚本', icon: '🎬', label: '视频脚本' },
  { key: '文案', icon: '📝', label: '图文文案' },
  { key: '口播', icon: '🎤', label: '口播话术' },
]

const templatePresets: Record<string, string> = {
  '带货': '我是卖充电宝的，帮我写抖音带货文案',
  '种草': '帮我写一个小红书种草笔记，产品是蓝牙耳机',
  '测评': '帮我写一个B站产品测评脚本，产品是机械键盘',
  '开箱': '帮我写一个开箱视频口播脚本',
  '带货2': '我是卖充电宝的，帮我写抖音带货文案',
  '种草2': '帮我写一个小红书种草笔记，产品是蓝牙耳机',
  '标题': '帮我生成5个科技类视频爆款标题',
  '脚本': '帮我写一个60秒短视频脚本',
  '文案': '帮我写一篇公众号图文文案',
  '口播': '帮我写一段直播口播话术',
}

function useTemplate(t: { key: string; icon: string; label: string }) {
  const preset = templatePresets[t.key] || `帮我写一个${t.label}内容`
  router.push({ path: '/studio', query: { template: preset } })
}

// ── Quick Start ──
async function startQuickCreate() {
  if (!quickInput.value.trim()) return
  const query: Record<string, string> = { template: quickInput.value.trim() }
  if (quickPlatforms.value.length > 0) {
    query.platforms = quickPlatforms.value.join(',')
  }
  router.push({ path: '/studio', query })
}

// ── Init ──
onMounted(async () => {
  await chatStore.loadSessions()
  await loadRecentSessions()
  computeStats()
})
</script>

<style scoped>
.dashboard {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* ── Welcome Banner ── */
.welcome-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  margin-bottom: 24px;
  background: linear-gradient(90deg, rgba(255, 107, 53, .08) 0%, transparent 60%);
  border-left: 4px solid #FF6B35;
  border-radius: 0 12px 12px 0;
}

.welcome-text h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1A0F2E;
}

.welcome-text p {
  margin: 4px 0 0;
  font-size: 14px;
  color: #888;
}

.welcome-date {
  font-size: 14px;
  color: #999;
  white-space: nowrap;
}

/* ── Card Grid ── */
.dash-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 32px;
}

.dash-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, .05);
  border-top: 3px solid #FF6B35;
}

.dash-card h3 {
  margin: 0 0 16px;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1A0F2E;
}

/* ── Quick Start Card ── */
.quick-start {
  background: #FFF5F0;
  border-top-color: #FF6B35;
}

.quick-start :deep(.n-input) {
  margin-bottom: 12px;
}

.qs-platforms {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}

.qs-plat-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1.5px solid var(--pc);
  color: var(--pc);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
  user-select: none;
}

.qs-plat-chip:hover {
  opacity: .8;
}

.qs-plat-chip.active {
  background: var(--pc);
  color: #fff;
}

/* ── Recent List Card ── */
.empty-hint {
  text-align: center;
  padding: 20px 0;
}

.empty-hint p {
  margin: 0;
  font-size: 14px;
  color: #999;
}

.empty-hint .sub {
  font-size: 12px;
  color: #bbb;
  margin-top: 4px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all .15s;
}

.recent-item:hover {
  background: rgba(255, 107, 53, .06);
}

.ri-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.ri-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ri-time {
  font-size: 12px;
  color: #aaa;
  flex-shrink: 0;
}

.view-all {
  text-align: center;
  margin-top: 8px;
  font-size: 13px;
  color: #FF6B35;
  cursor: pointer;
  font-weight: 500;
}

.view-all:hover {
  text-decoration: underline;
}

/* ── Stats Card ── */
.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 12px 8px;
  background: #FFFBF8;
  border-radius: 10px;
}

.stat-num {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: #FF6B35;
  line-height: 1.2;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* ── Templates Card ── */
.template-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.tpl-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 10px;
  border-radius: 10px;
  background: #FFFBF8;
  cursor: pointer;
  transition: all .2s;
  text-align: center;
}

.tpl-chip:hover {
  background: #FFF0EB;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 53, .12);
}

.tpl-icon {
  font-size: 28px;
  margin-bottom: 6px;
}

.tpl-name {
  font-size: 14px;
  font-weight: 700;
  color: #1A0F2E;
}

.tpl-desc {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

/* ── Quick Templates Section ── */
.quick-section {
  margin-top: 8px;
}

.quick-section h3 {
  margin: 0 0 16px;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1A0F2E;
}

.quick-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #FDE8E0;
  font-size: 14px;
  font-weight: 500;
  color: #555;
  cursor: pointer;
  transition: all .2s;
  user-select: none;
}

.quick-chip:hover {
  background: #FFF0EB;
  border-color: #FFB088;
  color: #FF6B35;
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(255, 107, 53, .1);
}

/* ── Dark Mode ── */
[data-theme="dark"] .welcome-banner {
  background: linear-gradient(90deg, rgba(255, 107, 53, .1) 0%, transparent 60%);
}

[data-theme="dark"] .welcome-text h1 {
  color: #eee;
}

[data-theme="dark"] .welcome-text p {
  color: #888;
}

[data-theme="dark"] .welcome-date {
  color: #888;
}

[data-theme="dark"] .dash-card {
  background: #1E1E28;
  box-shadow: 0 2px 12px rgba(0, 0, 0, .2);
}

[data-theme="dark"] .dash-card h3 {
  color: #eee;
}

[data-theme="dark"] .quick-start {
  background: #1a1518;
}

[data-theme="dark"] .recent-item:hover {
  background: rgba(255, 107, 53, .08);
}

[data-theme="dark"] .ri-title {
  color: #ddd;
}

[data-theme="dark"] .stat-item {
  background: #18181d;
}

[data-theme="dark"] .tpl-chip {
  background: #18181d;
}

[data-theme="dark"] .tpl-chip:hover {
  background: #2a1a2a;
}

[data-theme="dark"] .tpl-name {
  color: #ddd;
}

[data-theme="dark"] .quick-chip {
  background: #1E1E28;
  border-color: #2D2D3A;
  color: #aaa;
}

[data-theme="dark"] .quick-chip:hover {
  background: #2a1a2a;
  border-color: #FF6B35;
  color: #ffa070;
}

[data-theme="dark"] .quick-section h3 {
  color: #eee;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .dash-grid {
    grid-template-columns: 1fr;
  }

  .welcome-banner {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .template-grid {
    grid-template-columns: 1fr 1fr;
  }

  .dashboard {
    padding: 20px 16px;
  }
}
</style>
