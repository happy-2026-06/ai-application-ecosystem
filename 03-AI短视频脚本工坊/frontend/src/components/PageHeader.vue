<template>
  <div class="page-header">
    <div class="ph-left">
      <h2 class="ph-title">{{ title }}</h2>
      <p class="ph-sub" v-if="subtitle">{{ subtitle }}</p>
    </div>
    <div class="ph-actions" v-if="$slots.actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<style scoped>
.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 24px;
}
.ph-left {
  border-left: 4px solid var(--primary, #C8A951);
  padding-left: 14px;
}
.ph-title { font-size: 22px; font-weight: 700; margin: 0; color: var(--text-primary); }
.ph-sub { font-size: 13px; color: var(--text-secondary); margin: 4px 0 0; }
.ph-actions { display: flex; align-items: center; gap: 8px; }

[data-theme="dark"] .ph-title { color: #E8E8F0; }
[data-theme="dark"] .ph-sub { color: #9999A8; }
</style>
