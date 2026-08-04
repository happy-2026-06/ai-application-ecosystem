<template>
  <n-config-provider :theme="theme" :locale="zhCN" :date-locale="dateZhCN">
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
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
const theme = computed(() => authStore.isDarkMode ? darkTheme : null)

watch(() => authStore.isDarkMode, (dark) => {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
}, { immediate: true })
</script>

<style>
html, body, #app { height: 100%; margin: 0; padding: 0; }
body {
  font-family: "Inter", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
  background: #F8FAFC; transition: background .3s;
}
[data-theme="dark"] body { background: #0F172A; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: #c0c0c0; border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: #a0a0a0; }
::-webkit-scrollbar-track { background: transparent; }
[data-theme="dark"] ::-webkit-scrollbar-thumb { background: #4a4a5a; }
[data-theme="dark"] ::-webkit-scrollbar-thumb:hover { background: #5a5a6a; }
</style>
