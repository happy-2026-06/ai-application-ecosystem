<template>
  <n-config-provider :theme="theme" :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-dialog-provider>
      <n-notification-provider>
        <n-message-provider>
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </n-message-provider>
      </n-notification-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { darkTheme, zhCN, dateZhCN, type GlobalThemeOverrides } from 'naive-ui'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const theme = computed(() => authStore.isDarkMode ? darkTheme : null)

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#2563EB',
    primaryColorHover: '#1D4ED8',
    primaryColorPressed: '#1E40AF',
    primaryColorSuppl: '#2563EB',
    borderRadius: '8px',
  },
}

watch(() => authStore.isDarkMode, (dark) => {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
}, { immediate: true })
</script>

<style>
html, body, #app { height: 100%; margin: 0; padding: 0; }
body {
  font-family: "Inter", "PingFang SC", "Microsoft YaHei", "Noto Sans SC",
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #F8FAFC;
  transition: background .3s;
}
[data-theme="dark"] body { background: #0F172A; }
</style>
