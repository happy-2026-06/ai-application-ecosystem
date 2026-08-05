<template>
  <div class="app-shell">
    <!-- Top Navigation Bar -->
    <header class="top-nav">
      <div class="tn-left">
        <span class="tn-brand" @click="$router.push('/home')">
          <span class="tn-logo">✍️</span>
          <span class="tn-name">创作助手</span>
        </span>
        <nav class="tn-nav">
          <span v-for="item in navItems" :key="item.key"
            class="tn-item" :class="{ active: currentRoute === item.key }"
            @click="go(item.key)">
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
  if (name.startsWith('Admin')) return 'admin'
  if (name === 'Settings') return 'settings'
  if (name === 'ContentStudio' || name === 'ContentStudioSession') return 'studio'
  if (name === 'DashboardHome') return 'home'
  return 'home'
})

const navItems = computed(() => {
  const items: { key: string; icon: string; label: string }[] = [
    { key: 'home', icon: '🏠', label: '首页' },
    { key: 'studio', icon: '✍️', label: '创作' },
  ]
  if (authStore.isAdmin) {
    items.push({ key: 'admin', icon: '📚', label: '管理' })
  }
  return items
})

function go(key: string) {
  if (key === 'home') router.push('/home')
  else if (key === 'studio') router.push('/studio')
  else if (key === 'admin') router.push('/admin/users')
  else if (key === 'settings') router.push('/settings')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* ── Top Navigation Bar ── */
.top-nav {
  height: 56px;
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(255, 255, 255, .85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid #FDE8E0;
  user-select: none;
}

.tn-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tn-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 12px 4px 0;
  margin-right: 8px;
  border-right: 1px solid #FDE8E0;
}

.tn-logo {
  font-size: 22px;
}

.tn-name {
  font-size: 16px;
  font-weight: 700;
  color: #1A0F2E;
  letter-spacing: 0.5px;
}

.tn-nav {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tn-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all .15s;
  font-size: 14px;
  font-weight: 500;
  color: #555;
  white-space: nowrap;
}

.tn-item:hover {
  background: rgba(255, 107, 53, .08);
  color: #FF6B35;
}

.tn-item.active {
  background: rgba(255, 107, 53, .15);
  color: #FF6B35;
  font-weight: 700;
}

.tn-icon {
  font-size: 16px;
}

.tn-right {
  display: flex;
  align-items: center;
  gap: 2px;
}

.tn-user-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px 4px 6px;
  border-radius: 20px;
  cursor: pointer;
  transition: all .15s;
  font-size: 13px;
  font-weight: 500;
  color: #555;
  background: rgba(255, 107, 53, .06);
  margin: 0 4px;
}

.tn-user-badge:hover {
  background: rgba(255, 107, 53, .14);
  color: #FF6B35;
}

.tn-avatar {
  font-size: 22px;
}

.tn-username {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Main Content Area ── */
.app-main {
  flex: 1;
  min-height: 0;
  background: #FFFBF8;
  transition: background .3s;
  padding-top: 56px;
  overflow: auto;
}

/* ── Dark Mode ── */
[data-theme="dark"] .top-nav {
  background: rgba(13, 13, 20, .9);
  border-bottom-color: #2D2D3A;
}

[data-theme="dark"] .tn-brand {
  border-right-color: #2D2D3A;
}

[data-theme="dark"] .tn-name {
  color: #eee;
}

[data-theme="dark"] .tn-item {
  color: #999;
}

[data-theme="dark"] .tn-item:hover {
  background: rgba(255, 107, 53, .08);
  color: #d4a080;
}

[data-theme="dark"] .tn-item.active {
  background: rgba(255, 107, 53, .2);
  color: #ffa070;
}

[data-theme="dark"] .tn-user-badge {
  color: #aaa;
  background: rgba(255, 107, 53, .06);
}

[data-theme="dark"] .tn-user-badge:hover {
  background: rgba(255, 107, 53, .14);
  color: #ffa070;
}

[data-theme="dark"] .app-main {
  background: #0F0A14;
}
</style>
