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
    primaryColor: '#FF6B35',
    primaryColorHover: '#E55A2B',
    primaryColorPressed: '#CC4A20',
    primaryColorSuppl: '#FF6B35',
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
  background: #FFFBF8;
  transition: background .3s;
}
[data-theme="dark"] body { background: #0F0A14; }
</style>
