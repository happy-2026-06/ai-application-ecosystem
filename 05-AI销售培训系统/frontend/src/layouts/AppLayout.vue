
<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <nav class="app-sidebar">
      <div class="sb-brand" @click="$router.push('/training')">
        <span class="sb-logo">🎯</span>
        <span class="sb-name">销售培训</span>
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
          <div class="sb-role">{{ authStore.isAdmin ? '管理员' : '用户' }}</div>
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
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentRoute = computed(() => {
  const name = String(route.name || '')
  if (name === 'TrainingRoom') return 'training'
  if (name.startsWith('Admin')) return 'admin'
  return name === 'Settings' ? 'settings' : 'chat'
})

const navItems = computed(() => {
  const items: { key: string; icon: string; label: string }[] = [
    { key: 'training', icon: '🎯', label: '销售对练' },
  ]
  if (authStore.isAdmin) {
    items.push({ key: 'admin', icon: '📚', label: '知识库管理' })
  }
  return items
})

function go(key: string) {
  if (key === 'chat') router.push('/chat')
  if (key === 'training') router.push('/training')
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
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: #e0e0f0; user-select: none;
}
.sb-brand { display: flex; align-items: center; gap: 10px; padding: 20px 18px; cursor: pointer; }
.sb-logo { font-size: 28px; }
.sb-name { font-size: 16px; font-weight: 700; letter-spacing: 0.5px; color: #fff; }

.sb-nav { padding: 8px 10px; flex-shrink: 0; }
.sb-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 10px;
  cursor: pointer; transition: all .15s; margin-bottom: 2px; color: #b0b0d0;
}
.sb-item:hover { background: rgba(255,255,255,.08); color: #e8e8ff; }
.sb-item.active { background: rgba(102,126,234,.25); color: #fff; }
.sb-icon { font-size: 20px; width: 28px; text-align: center; flex-shrink: 0; }
.sb-label { font-size: 14px; font-weight: 500; white-space: nowrap; }

.sb-spacer { flex: 1; }
.sb-bottom-nav { padding: 0 10px 8px; }

.sb-user {
  display: flex; align-items: center; gap: 10px; padding: 14px 16px;
  border-top: 1px solid rgba(255,255,255,.08); cursor: pointer; margin: 0 8px;
}
.sb-avatar { font-size: 28px; }
.sb-user-info { flex: 1; min-width: 0; }
.sb-username { font-size: 13px; font-weight: 600; color: #e8e8ff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sb-role { font-size: 11px; color: #8888aa; margin-top: 1px; }

/* Main */
.app-main { flex: 1; min-width: 0; background: #fafbfd; overflow: hidden; transition: background .3s; }

/* Dark mode */
[data-theme="dark"] .app-sidebar { background: linear-gradient(180deg, #0d0d14 0%, #0f0f1a 100%); }
[data-theme="dark"] .sb-item:hover { background: rgba(255,255,255,.05); }
[data-theme="dark"] .sb-item.active { background: rgba(102,126,234,.2); }
[data-theme="dark"] .sb-user { border-top-color: rgba(255,255,255,.05); }
[data-theme="dark"] .app-main { background: #101014; }
</style>
