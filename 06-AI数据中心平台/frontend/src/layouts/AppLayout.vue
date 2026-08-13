<template>
  <div class="app-shell">
    <header class="top-nav">
      <div class="tn-left">
        <span class="tn-brand" @click="$router.push('/data')">
          <span class="tn-logo">📊</span>
          <span class="tn-name">数据中心</span>
        </span>
        <nav class="tn-nav">
          <span v-for="item in navItems" :key="item.key" class="tn-item"
            :class="{ active: currentRoute === item.key }" @click="go(item.key)">
            <span class="tn-icon">{{ item.icon }}</span>{{ item.label }}
          </span>
        </nav>
      </div>
      <div class="tn-right">
        <n-dropdown trigger="hover" :options="[
          {label:'📊 数据中枢',key:'data'},
          {label:'🤖 运营引擎',key:'engine'},
          {label:'🧠 模型工厂',key:'model'},
        ]" @select="jumpToPlatform">
          <span class="tn-item">🏢 中台导航</span>
        </n-dropdown>
        <span class="tn-item" @click="authStore.toggleDarkMode()">{{ authStore.isDarkMode ? '☀️' : '🌙' }}</span>
        <span class="tn-user-badge" @click="go('settings')">
          <span class="tn-avatar">{{ authStore.avatar }}</span>
          <span class="tn-username">{{ authStore.user?.display_name || authStore.user?.username }}</span>
        </span>
        <span class="tn-item" @click="handleLogout">🚪</span>
      </div>
    </header>
    <main class="app-main"><router-view /></main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
const route = useRoute(); const router = useRouter(); const authStore = useAuthStore()
const currentRoute = computed(() => {
  const n = String(route.name || '')
  if (n.startsWith('Data')) return 'data'
  if (n.startsWith('Admin')) return 'admin'
  return n === 'Settings' ? 'settings' : 'data'
})
const navItems = computed(() => {
  const items: { key: string; icon: string; label: string }[] = [
    { key: 'data', icon: '📊', label: '数据控制台' },
    { key: 'datasets', icon: '📚', label: '数据集' },
    { key: 'quality', icon: '📈', label: '质量报告' },
  ]
  if (authStore.isAdmin) items.push({ key: 'admin', icon: '⚙️', label: '管理' })
  return items
})
function go(k: string) {
  if (k === 'data') router.push('/data')
  else if (k === 'datasets') router.push('/data/datasets')
  else if (k === 'quality') router.push('/data/quality')
  else if (k === 'admin') router.push('/admin/dashboard')
  else if (k === 'settings') router.push('/settings')
}
function jumpToPlatform(k:string){
  const urls:Record<string,string>={data:'http://localhost:3006',engine:'http://localhost:3007',model:'http://localhost:3008'}
  if(urls[k] && urls[k]!==window.location.origin) window.open(urls[k],'_blank')
}
function handleLogout() { authStore.logout(); router.push('/login') }
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
.top-nav { height: 56px; min-height: 56px; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; position: fixed; top: 0; left: 0; right: 0; z-index: 100; background: rgba(255,255,255,.82); backdrop-filter: blur(14px); border-bottom: 1px solid #e0e7ed; user-select: none; }
.tn-left { display: flex; align-items: center; gap: 4px; }
.tn-brand { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 4px 12px 4px 0; margin-right: 8px; border-right: 1px solid #e0e7ed; }
.tn-logo { font-size: 22px; }
.tn-name { font-size: 16px; font-weight: 700; color: #0c4a6e; }
.tn-nav { display: flex; align-items: center; gap: 4px; }
.tn-item { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; cursor: pointer; transition: all .15s; font-size: 14px; font-weight: 500; color: #475569; white-space: nowrap; }
.tn-item:hover { background: rgba(14,165,233,.06); color: #0ea5e9; }
.tn-item.active { background: rgba(14,165,233,.1); color: #0ea5e9; font-weight: 700; }
.tn-icon { font-size: 16px; }
.tn-right { display: flex; align-items: center; gap: 2px; }
.tn-user-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px 4px 6px; border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 500; color: #475569; background: rgba(14,165,233,.04); margin: 0 4px; }
.tn-user-badge:hover { background: rgba(14,165,233,.1); color: #0ea5e9; }
.tn-avatar { font-size: 22px; }
.tn-username { max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.app-main { flex: 1; min-height: 0; background: #f8fafc; transition: background .3s; padding-top: 56px; overflow: auto; }
[data-theme="dark"] .top-nav { background: rgba(15,23,42,.88); border-bottom-color: #1e293b; }
[data-theme="dark"] .tn-brand { border-right-color: #1e293b; }
[data-theme="dark"] .tn-name { color: #38bdf8; }
[data-theme="dark"] .tn-item { color: #94a3b8; }
[data-theme="dark"] .tn-item.active { color: #38bdf8; }
[data-theme="dark"] .app-main { background: #0f172a; }
</style>
