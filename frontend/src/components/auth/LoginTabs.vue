<script setup lang="ts">
defineProps<{
  modelValue: 'account' | 'phone'
}>()

const emit = defineEmits<{
  'update:modelValue': [value: 'account' | 'phone']
}>()

const tabs: { key: 'account' | 'phone'; label: string }[] = [
  { key: 'account', label: '账号登录' },
  { key: 'phone', label: '手机登录' },
]
</script>

<template>
  <div class="login-tabs">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="tab-item"
      :class="{ active: modelValue === tab.key }"
      @click="emit('update:modelValue', tab.key)"
    >
      <span class="tab-label">{{ tab.label }}</span>
      <span class="tab-indicator" />
    </button>
  </div>
</template>

<style scoped>
.login-tabs {
  display: flex;
  justify-content: center;
  gap: 32px;
}

.tab-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  border: none;
  background: none;
  cursor: pointer;
  min-width: 80px;
}

.tab-label {
  font-size: var(--font-size-login-tab);
  font-weight: var(--font-weight-normal);
  color: var(--color-text-muted);
  transition: color var(--transition-fast), font-weight var(--transition-fast);
}

.tab-item.active .tab-label {
  color: var(--color-accent);
  font-weight: var(--font-weight-semibold);
}

.tab-indicator {
  display: block;
  width: var(--size-login-tab-indicator-width);
  height: var(--size-login-tab-indicator-height);
  border-radius: 2px;
  background: transparent;
  transition: background var(--transition-fast);
}

.tab-item.active .tab-indicator {
  background: var(--color-accent);
}
</style>
