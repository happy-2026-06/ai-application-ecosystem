
<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <nav class="app-sidebar">
      <div class="sb-brand" @click="$router.push('/assets')">
        <span class="sb-logo">🗂️</span>
        <span class="sb-name">图库管家</span>
      </div>

      <!-- Stats Mini -->
      <div class="sb-stats">
        <div class="sb-stat-item">
          <span class="sb-stat-num">{{ stats.totalAssets }}</span>
          <span class="sb-stat-label">总素材</span>
        </div>
        <div class="sb-stat-item">
          <span class="sb-stat-num">{{ stats.taggedAssets }}</span>
          <span class="sb-stat-label">已标签</span>
        </div>
        <div class="sb-stat-item">
          <span class="sb-stat-num">{{ stats.onlineUsers }}</span>
          <span class="sb-stat-label">在线</span>
        </div>
      </div>

      <div class="sb-nav">
        <div
          v-for="item in navItems"
          :key="item.key"
          class="sb-item"
          :class="{ active: currentRoute === item.key }"
          @click="go(item.key)"
          :title="item.label"
        >
          <span class="sb-icon">{{ item.icon }}</span>
          <span class="sb-label">{{ item.label }}</span>
          <div v-if="currentRoute === item.key" class="sb-active-dot" />
        </div>
      </div>

      <div class="sb-spacer" />

      <div class="sb-bottom-nav">
        <div class="sb-item" @click="authStore.toggleDarkMode()">
          <span class="sb-icon">{{ authStore.isDarkMode ? '☀️' : '🌙' }}</span>
          <span class="sb-label">{{ authStore.isDarkMode ? '浅色模式' : '深色模式' }}</span>
        </div>
        <div class="sb-item" :class="{ active: currentRoute === 'settings' }" @click="go('settings')">
          <span class="sb-icon">👤</span>
          <span class="sb-label">个人中心</span>
        </div>
        <div class="sb-item" @click="handleLogout">
          <span class="sb-icon">🚪</span>
          <span class="sb-label">退出</span>
        </div>
      </div>

      <div class="sb-user" @click="go('settings')">
        <span class="sb-avatar">{{ authStore.avatar }}</span>
        <div class="sb-user-info">
          <div class="sb-username">{{ authStore.user?.display_name || authStore.user?.username }}</div>
          <div class="sb-role">
            <span class="online-dot" />
            {{ authStore.isAdmin ? '管理员' : '用户' }}
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { assetApi } from '../api/assets'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentRoute = computed(() => {
  const name = String(route.name || '')
  if (name === 'AssetGrid') return 'assets'
  if (name.startsWith('Admin')) return 'admin'
  return name === 'Settings' ? 'settings' : 'chat'
})

const navItems = computed(() => {
  const items: { key: string; icon: string; label: string }[] = [
    { key: 'assets', icon: '🗂️', label: '图库管理' },
  ]
  if (authStore.isAdmin) {
    items.push({ key: 'admin', icon: '📊', label: '管理后台' })
  }
  return items
})

const stats = reactive({ totalAssets: 0, taggedAssets: 0, onlineUsers: 1 })

async function fetchSidebarStats() {
  try {
    const res = await assetApi.getStats()
    stats.totalAssets = res.data.total
    stats.taggedAssets = res.data.tagged
  } catch { /* keep defaults */ }
}

// Fetch on mount and on route change
onMounted(() => fetchSidebarStats())
watch(() => route.fullPath, () => fetchSidebarStats())

function go(key: string) {
  if (key === 'assets') router.push('/assets')
  else if (key === 'admin') router.push('/admin/dashboard')
  else if (key === 'settings') router.push('/settings')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-shell { display: flex; height: 100vh; overflow: hidden; }

/* Sidebar */
.app-sidebar {
  width: 220px; min-width: 220px; display: flex; flex-direction: column;
  background: linear-gradient(180deg, #0F0B1E 0%, #1A1230 50%, #0D0828 100%);
  color: #e0e0f0; user-select: none;
}
.sb-brand { display: flex; align-items: center; gap: 10px; padding: 20px 18px; cursor: pointer; }
.sb-logo { font-size: 28px; }
.sb-name { font-size: 16px; font-weight: 700; letter-spacing: 0.5px; color: #fff; }

/* Stats Mini */
.sb-stats {
  display: flex; gap: 6px; padding: 4px 10px; margin-bottom: 8px;
}
.sb-stat-item {
  flex: 1; text-align: center; padding: 8px 4px;
  background: rgba(99,102,241,.08); border-radius: 8px;
  border: 1px solid rgba(99,102,241,.06);
}
.sb-stat-num { display: block; font-size: 16px; font-weight: 700; color: #818CF8; }
.sb-stat-label { display: block; font-size: 10px; color: #6B6580; margin-top: 2px; }

.sb-nav { padding: 8px 10px; flex-shrink: 0; }
.sb-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 10px;
  cursor: pointer; transition: all .15s; margin-bottom: 2px; color: #b0b0d0;
  position: relative;
}
.sb-item:hover { background: rgba(99,102,241,.08); color: #e8e8ff; }
.sb-item.active { background: rgba(99,102,241,.15); color: #fff; border-left: 3px solid #818CF8; }
.sb-icon { font-size: 20px; width: 28px; text-align: center; flex-shrink: 0; }
.sb-label { font-size: 14px; font-weight: 500; white-space: nowrap; }

.sb-active-dot {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  width: 6px; height: 6px; border-radius: 50%;
  background: #818CF8; box-shadow: 0 0 8px rgba(129,140,248,.6);
}

.sb-spacer { flex: 1; }
.sb-bottom-nav { padding: 0 10px 8px; }

.sb-user {
  display: flex; align-items: center; gap: 10px; padding: 14px 16px;
  border-top: 1px solid rgba(99,102,241,.08); cursor: pointer; margin: 0 8px;
}
.sb-avatar { font-size: 28px; }
.sb-user-info { flex: 1; min-width: 0; }
.sb-username { font-size: 13px; font-weight: 600; color: #e8e8ff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sb-role { font-size: 11px; color: #8888aa; margin-top: 1px; display: flex; align-items: center; gap: 4px; }

.online-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #10B981; box-shadow: 0 0 6px rgba(16,185,129,.5);
  animation: pulse-online 2s ease-in-out infinite;
}

/* Main */
.app-main { flex: 1; min-width: 0; background: #F8F9FC; overflow: hidden; transition: background .3s; }

/* Dark mode */
[data-theme="dark"] .app-sidebar { background: linear-gradient(180deg, #080510 0%, #0F0B1E 50%, #0A0812 100%); }
[data-theme="dark"] .sb-item:hover { background: rgba(99,102,241,.06); }
[data-theme="dark"] .sb-item.active { background: rgba(99,102,241,.12); border-left-color: #6366F1; }
[data-theme="dark"] .sb-user { border-top-color: rgba(99,102,241,.06); }
[data-theme="dark"] .sb-stat-item { background: rgba(99,102,241,.04); border-color: rgba(99,102,241,.04); }
[data-theme="dark"] .app-main { background: #0A0812; }

@keyframes pulse-online {
  0%, 100% { opacity: 1; }
  50% { opacity: .5; }
}
</style>
