<template>
  <div class="empty-state">
    <div class="es-icon">{{ icon }}</div>
    <h2 class="es-title">{{ title }}</h2>
    <p class="es-desc" v-if="description">{{ description }}</p>
    <div class="es-actions" v-if="$slots.actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  description?: string
}>()
</script>

<style scoped>
.empty-state {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 60px 40px; text-align: center;
  height: 100%;
}
.es-icon {
  font-size: 72px; margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}
.es-title {
  font-size: 24px; font-weight: 700;
  color: var(--text-primary, #2C2C3A);
  margin: 0 0 8px;
}
.es-desc {
  font-size: 15px; color: var(--text-secondary, #888);
  max-width: 420px; margin: 0; line-height: 1.6;
}
.es-actions { margin-top: 24px; }

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

[data-theme="dark"] .es-title { color: #E8E8F0; }
[data-theme="dark"] .es-desc { color: #9999A8; }
</style>
