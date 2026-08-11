<template>
  <div class="app-shell">
    <!-- Top Navigation Bar (毛玻璃顶栏) -->
    <header class="top-nav">
      <div class="tn-left">
        <span class="tn-brand" @click="$router.push('/training')">
          <span class="tn-logo">🎯</span>
          <span class="tn-name">话术教练</span>
        </span>
        <nav class="tn-nav">
          <span
            v-for="item in navItems"
            :key="item.key"
            class="tn-item"
            :class="{ active: currentRoute === item.key }"
            @click="go(item.key)"
          >
            <span class="tn-icon">{{ item.icon }}</span>
            {{ item.label }}
          </span>
        </nav>
      </div>
      <div class="tn-right">
        <span class="tn-item" @click="authStore.toggleDarkMode()">
          {{ authStore.isDarkMode ? '☀️' : '🌙' }}
        </span>
        <span class="tn-user-badge" @click="go('settings')">
          <span class="tn-avatar">{{ authStore.avatar }}</span>
          <span class="tn-username">{{ authStore.user?.display_name || authStore.user?.username }}</span>
        </span>
        <span class="tn-item" @click="handleLogout" title="退出">🚪</span>
      </div>
    </header>

    <!-- Main Content (full width below nav) -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentRoute = computed(() => {
  const name = String(route.name || '')
  if (name === 'TrainingRoom') return 'training'
  if (name === 'TrainingHistory') return 'history'
  if (name.startsWith('Admin')) return 'admin'
  if (name === 'Settings') return 'settings'
  return 'training'
})

const navItems = computed(() => {
  const items: { key: string; icon: string; label: string }[] = [
    { key: 'training', icon: '🎯', label: '销售对练' },
    { key: 'history', icon: '📋', label: '训练记录' },
  ]
  if (authStore.isAdmin) {
    items.push({ key: 'admin', icon: '📊', label: '管理' })
  }
  return items
})

function go(key: string) {
  if (key === 'training') router.push('/training')
  else if (key === 'history') router.push('/history')
  else if (key === 'admin') router.push('/admin/dashboard')
  else if (key === 'settings') router.push('/settings')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-shell {
  display: flex; flex-direction: column;
  height: 100vh; overflow: hidden;
}

/* ── 顶部导航 — 毛玻璃 ── */
.top-nav {
  height: 56px; min-height: 56px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px;
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  background: rgba(255, 255, 255, .82);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid #e8ecf1;
  user-select: none;
}
.tn-left { display: flex; align-items: center; gap: 4px; }
.tn-brand {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  padding: 4px 12px 4px 0; margin-right: 8px;
  border-right: 1px solid #e8ecf1;
}
.tn-logo { font-size: 22px; }
.tn-name {
  font-size: 16px; font-weight: 700; color: #0f172a; letter-spacing: 0.5px;
}
.tn-nav { display: flex; align-items: center; gap: 4px; }
.tn-item {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 8px; cursor: pointer;
  transition: all .15s; font-size: 14px; font-weight: 500; color: #475569;
  white-space: nowrap;
}
.tn-item:hover { background: rgba(59,130,246,.06); color: #3b82f6; }
.tn-item.active { background: rgba(59,130,246,.1); color: #3b82f6; font-weight: 700; }
.tn-icon { font-size: 16px; }

.tn-right { display: flex; align-items: center; gap: 2px; }
.tn-user-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px 4px 6px; border-radius: 20px; cursor: pointer;
  transition: all .15s; font-size: 13px; font-weight: 500; color: #475569;
  background: rgba(59,130,246,.04); margin: 0 4px;
}
.tn-user-badge:hover { background: rgba(59,130,246,.1); color: #3b82f6; }
.tn-avatar { font-size: 22px; }
.tn-username { max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── 主内容区 ── */
.app-main {
  flex: 1; min-height: 0;
  background: #f8fafc; transition: background .3s;
  padding-top: 56px; overflow: auto;
}

/* ── 暗色模式 ── */
[data-theme="dark"] .top-nav {
  background: rgba(15, 23, 42, .88); border-bottom-color: #1e293b;
}
[data-theme="dark"] .tn-brand { border-right-color: #1e293b; }
[data-theme="dark"] .tn-name { color: #e2e8f0; }
[data-theme="dark"] .tn-item { color: #94a3b8; }
[data-theme="dark"] .tn-item:hover { background: rgba(59,130,246,.08); color: #60a5fa; }
[data-theme="dark"] .tn-item.active { background: rgba(59,130,246,.15); color: #60a5fa; }
[data-theme="dark"] .tn-user-badge { color: #94a3b8; background: rgba(59,130,246,.04); }
[data-theme="dark"] .tn-user-badge:hover { background: rgba(59,130,246,.1); color: #60a5fa; }
[data-theme="dark"] .app-main { background: #0f172a; }
</style>
