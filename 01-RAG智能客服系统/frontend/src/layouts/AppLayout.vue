<template>
  <div class="app-shell">
    <!-- Sidebar (200px) -->
    <nav class="app-sidebar">
      <div class="sb-brand" @click="$router.push('/chat')">
        <span class="sb-logo">💬</span>
        <span class="sb-name">智能客服</span>
      </div>

      <!-- Mini stat cards -->
      <div class="sb-stats">
        <div class="stat-card">
          <span class="stat-icon">📊</span>
          <div class="stat-body">
            <div class="stat-value">{{ stats.todaySessions }}</div>
            <div class="stat-label">今日</div>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">😊</span>
          <div class="stat-body">
            <div class="stat-value">{{ stats.satisfaction }}%</div>
            <div class="stat-label">满意率</div>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">🟢</span>
          <div class="stat-body">
            <div class="stat-value">{{ stats.onlineCount }}</div>
            <div class="stat-label">在线</div>
          </div>
        </div>
      </div>

      <div class="sb-divider" />

      <!-- Navigation -->
      <div class="sb-nav">
        <div
          v-for="item in navItems"
          :key="item.key"
          class="sb-item"
          :class="{ active: currentRoute === item.key }"
          @click="item.action()"
          :title="item.label"
        >
          <span class="sb-icon">{{ item.icon }}</span>
          <span class="sb-label">{{ item.label }}</span>
        </div>
        <div class="sb-item" @click="authStore.toggleDarkMode()">
          <span class="sb-icon">{{ authStore.isDarkMode ? '☀️' : '🌙' }}</span>
          <span class="sb-label">{{ authStore.isDarkMode ? '浅色模式' : '深色模式' }}</span>
        </div>
        <div class="sb-item" @click="handleLogout">
          <span class="sb-icon">🚪</span>
          <span class="sb-label">退出</span>
        </div>
      </div>

      <div class="sb-spacer" />

      <!-- User info -->
      <div class="sb-user" @click="go('settings')">
        <span class="sb-avatar">{{ authStore.avatar }}</span>
        <div class="sb-user-info">
          <div class="sb-username">{{ authStore.user?.display_name || authStore.user?.username }}</div>
          <div class="sb-role">{{ authStore.isAdmin ? '管理员' : '用户' }}</div>
        </div>
      </div>
    </nav>

    <!-- Session List Panel (260px) — only on chat routes -->
    <aside v-if="showSessionPanel" class="session-panel">
      <div class="sp-header">
        <span class="sp-title">会话列表</span>
        <n-button size="tiny" type="primary" @click="handleNewSession" :loading="creating">
          ＋ 新对话
        </n-button>
      </div>
      <n-input
        v-if="chatStore.sessions.length > 0"
        v-model:value="searchText"
        placeholder="搜索会话…"
        clearable
        size="small"
        class="sp-search"
      />
      <div class="sp-scroll">
        <div v-if="filteredSessions.length === 0 && !searchText" class="sp-empty">
          <div class="sp-empty-icon">💬</div>
          <p>暂无会话</p>
        </div>
        <div
          v-for="s in filteredSessions"
          :key="s.id"
          class="sp-row"
          :class="{ active: currentSessionId === s.id }"
          @click="selectSession(s.id)"
        >
          <div class="sp-main">
            <div class="sp-sess-title">{{ s.title || '新对话' }}</div>
            <div class="sp-meta">{{ fmtDate(s.updated_at) }} · {{ s.message_count }}条</div>
          </div>
          <n-popconfirm @positive-click="handleDeleteSession(s.id)">
            <template #trigger>
              <n-button text size="tiny" class="sp-del" @click.stop>🗑</n-button>
            </template>
            删除该会话？
          </n-popconfirm>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useChatStore } from '../stores/chat'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const searchText = ref('')
const creating = ref(false)
const stats = ref({ todaySessions: 12, satisfaction: 98, onlineCount: 3 })

const currentRoute = computed(() => {
  const name = String(route.name || '')
  if (name.startsWith('Admin')) return 'admin'
  return name === 'Settings' ? 'settings' : 'chat'
})

const showSessionPanel = computed(() => {
  const name = String(route.name || '')
  return name === 'Chat' || name === 'ChatSession'
})

const currentSessionId = computed(() => {
  return (route.params.sessionId as string) || null
})

const navItems = computed(() => {
  const items: { key: string; icon: string; label: string; action: () => void }[] = [
    { key: 'chat', icon: '💬', label: '对话', action: () => go('chat') },
  ]
  if (authStore.isAdmin) {
    items.push({ key: 'admin', icon: '📚', label: '知识库', action: () => go('admin') })
  }
  items.push({ key: 'settings', icon: '👤', label: '设置', action: () => go('settings') })
  return items
})

const filteredSessions = computed(() => {
  if (!searchText.value) return chatStore.sessions
  const q = searchText.value.toLowerCase()
  return chatStore.sessions.filter((s) => s.title?.toLowerCase().includes(q))
})

function go(key: string) {
  if (key === 'chat') router.push('/chat')
  else if (key === 'admin') router.push('/admin/kb')
  else if (key === 'settings') router.push('/settings')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function selectSession(id: string) {
  router.push(`/chat/${id}`)
}

async function handleNewSession() {
  creating.value = true
  const s = await chatStore.createSession()
  creating.value = false
  if (s) router.push(`/chat/${s.id}`)
}

async function handleDeleteSession(id: string) {
  await chatStore.deleteSession(id)
  if (currentSessionId.value === id) {
    if (chatStore.sessions.length > 0) {
      router.push(`/chat/${chatStore.sessions[0].id}`)
    } else {
      router.push('/chat')
      chatStore.currentSession = null
      chatStore.messages = []
    }
  }
}

function fmtDate(d: string) {
  if (!d) return ''
  const dt = new Date(d)
  const n = new Date()
  const df = n.getTime() - dt.getTime()
  if (df < 864e5) return dt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  if (df < 6048e5) return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dt.getDay()]
  return dt.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(async () => {
  await chatStore.loadSessions()
  try {
    const res = await fetch('/api/admin/dashboard')
    if (res.ok) {
      const data = await res.json()
      stats.value = {
        todaySessions: data.today_sessions ?? 12,
        satisfaction: data.satisfaction ?? 98,
        onlineCount: data.online_count ?? 3,
      }
    }
  } catch {
    // Fall back to hardcoded defaults
  }
})
</script>

<style scoped>
.app-shell { display: flex; height: 100vh; overflow: hidden; }

/* ── Sidebar (200px) ──────────────────────────────────────────── */
.app-sidebar {
  width: 200px; min-width: 200px; display: flex; flex-direction: column;
  background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
  color: #e0e0f0; user-select: none;
}
.sb-brand { display: flex; align-items: center; gap: 10px; padding: 20px 16px; cursor: pointer; }
.sb-logo { font-size: 24px; }
.sb-name { font-size: 15px; font-weight: 700; letter-spacing: 0.5px; color: #fff; }

/* Stats */
.sb-stats { padding: 8px 10px; display: flex; flex-direction: column; gap: 5px; flex-shrink: 0; }
.stat-card {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  background: rgba(255,255,255,0.05); border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.06); transition: background .15s;
}
.stat-card:hover { background: rgba(255,255,255,0.09); }
.stat-icon { font-size: 20px; flex-shrink: 0; }
.stat-body { flex: 1; min-width: 0; }
.stat-value { font-size: 16px; font-weight: 700; color: #fff; line-height: 1.2; }
.stat-label { font-size: 11px; color: #8888aa; margin-top: 1px; }

.sb-divider { height: 1px; background: rgba(255,255,255,0.08); margin: 6px 14px; flex-shrink: 0; }

/* Nav */
.sb-nav { padding: 6px 10px; flex-shrink: 0; }
.sb-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 10px;
  cursor: pointer; transition: all .15s; margin-bottom: 2px; color: #b0b0d0;
}
.sb-item:hover { background: rgba(255,255,255,.08); color: #e8e8ff; }
.sb-item.active { background: rgba(37,99,235,.25); color: #fff; border-left: 3px solid #2563EB; }
.sb-icon { font-size: 18px; width: 24px; text-align: center; flex-shrink: 0; }
.sb-label { font-size: 14px; font-weight: 500; white-space: nowrap; }

.sb-spacer { flex: 1; }

.sb-user {
  display: flex; align-items: center; gap: 10px; padding: 14px 16px;
  border-top: 1px solid rgba(255,255,255,.08); cursor: pointer; margin: 0 8px;
}
.sb-avatar { font-size: 28px; }
.sb-user-info { flex: 1; min-width: 0; }
.sb-username { font-size: 13px; font-weight: 600; color: #e8e8ff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sb-role { font-size: 11px; color: #8888aa; margin-top: 1px; }

/* ── Session Panel (260px) ─────────────────────────────────────── */
.session-panel {
  width: 260px; min-width: 260px; display: flex; flex-direction: column;
  background: #F1F5F9; border-right: 1px solid #E2E8F0;
}
.sp-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px; border-bottom: 1px solid #E2E8F0; flex-shrink: 0;
}
.sp-title { font-size: 15px; font-weight: 600; color: #0F172A; }
.sp-search { padding: 8px 12px; flex-shrink: 0; }

.sp-scroll { flex: 1; overflow-y: auto; padding: 4px 8px 8px; }
.sp-scroll::-webkit-scrollbar { width: 4px; }
.sp-scroll::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }

.sp-empty { text-align: center; padding: 40px 10px; color: #aaa; font-size: 13px; }
.sp-empty-icon { font-size: 40px; margin-bottom: 8px; }
.sp-empty p { margin: 0; }

.sp-row {
  display: flex; align-items: center; padding: 10px 12px; border-radius: 10px;
  cursor: pointer; margin-bottom: 2px; transition: all .15s; gap: 4px;
}
.sp-row:hover { background: #E2E8F0; }
.sp-row.active { background: #BFDBFE; border-left: 3px solid #2563EB; }
.sp-main { flex: 1; min-width: 0; }
.sp-sess-title { font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #0F172A; }
.sp-meta { font-size: 11px; color: #aaa; margin-top: 2px; }
.sp-del { opacity: 0; transition: opacity .15s; }
.sp-row:hover .sp-del { opacity: 1; }

/* ── Main ──────────────────────────────────────────────────────── */
.app-main { flex: 1; min-width: 0; background: #F8FAFC; overflow: hidden; transition: background .3s; }

/* ── Dark mode ─────────────────────────────────────────────────── */
[data-theme="dark"] .app-sidebar { background: linear-gradient(180deg, #0A0A14 0%, #0F0F1E 100%); }
[data-theme="dark"] .stat-card { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.04); }
[data-theme="dark"] .stat-card:hover { background: rgba(255,255,255,0.07); }
[data-theme="dark"] .sb-item:hover { background: rgba(255,255,255,.05); }
[data-theme="dark"] .sb-item.active { background: rgba(37,99,235,.25); }
[data-theme="dark"] .sb-user { border-top-color: rgba(255,255,255,.05); }
[data-theme="dark"] .app-main { background: #0F172A; }

[data-theme="dark"] .session-panel { background: #18181D; border-right-color: #222; }
[data-theme="dark"] .sp-header { border-bottom-color: #222; }
[data-theme="dark"] .sp-title { color: #eee; }
[data-theme="dark"] .sp-row:hover { background: rgba(255,255,255,.04); }
[data-theme="dark"] .sp-row.active { background: rgba(37,99,235,.2); }
[data-theme="dark"] .sp-sess-title { color: #ddd; }
[data-theme="dark"] .sp-empty { color: #666; }
[data-theme="dark"] .sp-scroll::-webkit-scrollbar-thumb { background: #444; }
</style>
