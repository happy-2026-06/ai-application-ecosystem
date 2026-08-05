<template>
  <div class="nf-page">
    <div class="nf-inner">
      <div class="nf-icon">🎬</div>
      <h1>404 — 场景未找到</h1>
      <p>这个页面还没有写完剧本，回到工坊继续创作吧</p>
      <n-button type="primary" size="large" @click="$router.push('/studio')" :style="{marginTop:'24px'}">
        🎥 返回工坊
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.nf-page {
  height: 100%; display: flex; align-items: center; justify-content: center;
  background: var(--bg-body, #FAF9F4);
}
.nf-inner { text-align: center; }
.nf-icon { font-size: 72px; margin-bottom: 16px; animation: float 3s ease-in-out infinite; }
.nf-inner h1 { font-size: 28px; font-weight: 700; color: var(--text-primary, #2C2C3A); margin: 0 0 8px; }
.nf-inner p { font-size: 15px; color: var(--text-secondary, #888898); margin: 0; }

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

[data-theme="dark"] .nf-page { background: #0D0D14; }
[data-theme="dark"] .nf-inner h1 { color: #E8E8F0; }
[data-theme="dark"] .nf-inner p { color: #9999A8; }
</style>
