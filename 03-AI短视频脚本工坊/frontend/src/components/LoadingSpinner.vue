<template>
  <div class="loading-spinner">
    <div class="ls-spinner" />
    <h3 class="ls-title">AI 正在编排分镜…</h3>
    <p class="ls-hint">{{ currentHint }}</p>
    <div class="ls-platforms" v-if="platforms && platforms.length">
      <span
        v-for="p in platforms"
        :key="p"
        class="ls-tag"
        :style="{ background: platformColor(p), borderColor: platformColor(p) }"
      >{{ p }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { PLATFORM_COLORS } from '../assets/styles/tokens'

const props = defineProps<{
  hints?: string[]
  platforms?: string[]
}>()

const hints = props.hints || [
  '正在分析产品卖点…',
  '匹配最佳分镜模板中…',
  '编排镜头顺序…',
  '撰写口播文案…',
  '优化拍摄建议…',
  '生成平台适配方案…',
]
const currentHint = ref(hints[0])
let idx = 0
let timer: ReturnType<typeof setInterval> | null = null

function platformColor(p: string): string {
  return PLATFORM_COLORS[p] || '#C8A951'
}

onMounted(() => {
  timer = setInterval(() => {
    idx = (idx + 1) % hints.length
    currentHint.value = hints[idx]
  }, 2000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.loading-spinner {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 60px 40px; text-align: center;
  height: 100%;
}
.ls-spinner {
  width: 48px; height: 48px;
  border: 3px solid #f0e8d0;
  border-top-color: var(--primary, #C8A951);
  border-radius: 50%;
  animation: spin .8s linear infinite;
  margin-bottom: 20px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.ls-title { font-size: 18px; font-weight: 600; color: var(--text-primary); margin: 0 0 8px; }
.ls-hint { font-size: 14px; color: var(--text-secondary); margin: 0 0 16px; }
.ls-platforms { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
.ls-tag {
  padding: 4px 14px; border-radius: 20px;
  font-size: 12px; font-weight: 600; color: #fff;
  border: 1px solid transparent;
  opacity: .9; animation: pulse-tag 1.5s ease-in-out infinite;
}
.ls-tag:nth-child(2) { animation-delay: .3s; }
.ls-tag:nth-child(3) { animation-delay: .6s; }
.ls-tag:nth-child(4) { animation-delay: .9s; }
.ls-tag:nth-child(5) { animation-delay: 1.2s; }

@keyframes pulse-tag {
  0%, 100% { opacity: .85; }
  50% { opacity: 1; }
}

[data-theme="dark"] .ls-spinner { border-color: #2a2a2a; }
[data-theme="dark"] .ls-title { color: #E8E8F0; }
[data-theme="dark"] .ls-hint { color: #9999A8; }
</style>
