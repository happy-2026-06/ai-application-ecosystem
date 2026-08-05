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
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
  background: #fafbfd; transition: background .3s;
}
[data-theme="dark"] body { background: #101014; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-thumb { background: #ccc; border-radius: 5px; }
[data-theme="dark"] ::-webkit-scrollbar-thumb { background: #444; }
</style>
