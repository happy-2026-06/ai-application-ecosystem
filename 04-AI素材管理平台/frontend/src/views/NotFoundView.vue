<template>
  <div class="nf-page">
    <div class="nf-card">
      <div class="nf-icon">🗂️</div>
      <h1>404</h1>
      <p>页面未找到</p>
      <p class="nf-sub">你要找的素材可能已被移动或删除</p>
      <n-button type="primary" size="large" @click="$router.push('/assets')" class="nf-btn">
        ← 返回素材库
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.nf-page {
  display: flex; align-items: center; justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #0F0B1E 0%, #1A1230 40%, #2D1B69 100%);
}
.nf-card {
  text-align: center; padding: 60px 40px;
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(20px); border-radius: 20px;
  border: 1px solid rgba(99,102,241,.10);
  box-shadow: 0 8px 32px rgba(99,102,241,.08);
}
.nf-icon { font-size: 64px; margin-bottom: 16px; }
h1 { font-size: 72px; font-weight: 800; margin: 0; color: #6366F1; }
p { font-size: 20px; color: #1A1230; margin: 8px 0; font-weight: 600; }
.nf-sub { font-size: 14px; color: #6B6580; font-weight: 400; }
.nf-btn { margin-top: 24px; height: 44px; border-radius: 12px; }

[data-theme="dark"] .nf-page { background: linear-gradient(135deg, #0A0614 0%, #12101A 40%, #1A1530 100%); }
[data-theme="dark"] .nf-card { background: rgba(18,16,26,.85); border-color: rgba(99,102,241,.08); }
[data-theme="dark"] p { color: #E8E8F0; }
[data-theme="dark"] .nf-sub { color: #A09AB5; }
</style>
