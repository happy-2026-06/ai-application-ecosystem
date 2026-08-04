<template>
  <n-config-provider :theme="theme" :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-dialog-provider>
      <n-notification-provider>
        <n-message-provider>
          <router-view />
        </n-message-provider>
      </n-notification-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { darkTheme, zhCN, dateZhCN } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
const theme = computed(() => authStore.isDarkMode ? darkTheme : null)

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#FF6B35',
    primaryColorHover: '#FF7F52',
    primaryColorPressed: '#E55A2B',
    primaryColorSuppl: '#FF6B35',
  },
}

watch(() => authStore.isDarkMode, (dark) => {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
}, { immediate: true })
</script>

<style>
html, body, #app { height: 100%; margin: 0; padding: 0; scroll-behavior: smooth; }
body {
  font-family: "Inter", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
  background: #FFFBF8; transition: background .3s;
  font-size: 15px; line-height: 1.6;
}
h1 { font-size: 2rem; font-weight: 800; }
h2 { font-size: 1.5rem; font-weight: 700; }
h3 { font-size: 1.25rem; font-weight: 600; }
[data-theme="dark"] body { background: #0F0A14; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #FFB088; border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: #FF6B35; }
[data-theme="dark"] ::-webkit-scrollbar-thumb { background: #3a2a3a; }
[data-theme="dark"] ::-webkit-scrollbar-thumb:hover { background: #5a3a5a; }
</style>
