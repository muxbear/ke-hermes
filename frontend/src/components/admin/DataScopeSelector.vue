<script setup lang="ts">
import { Database } from 'lucide-vue-next'
import type { DataScope } from '@/types/admin'
import { DATA_SCOPE_OPTIONS } from '@/types/admin'

const props = defineProps<{
  resourceId: string
  resourceLabel: string
  currentScope: DataScope
  disabled: boolean
}>()

const emit = defineEmits<{
  change: [resourceId: string, scope: DataScope]
}>()
</script>

<template>
  <div class="scope-row">
    <div class="scope-info">
      <div class="scope-icon">
        <Database :size="16" />
      </div>
      <div>
        <div class="scope-label">{{ resourceLabel }}</div>
      </div>
    </div>
    <div class="scope-options">
      <button
        v-for="opt in DATA_SCOPE_OPTIONS"
        :key="opt.value"
        class="scope-btn"
        :class="{
          active: currentScope === opt.value,
          'cursor-not-allowed': disabled,
        }"
        :disabled="disabled"
        :title="opt.desc"
        @click="emit('change', resourceId, opt.value)"
      >
        {{ opt.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.scope-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}
.scope-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.scope-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-lg);
  background: rgba(30, 41, 59, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--foreground-muted);
}
.scope-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-secondary);
}
.scope-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.scope-btn {
  padding: 4px 10px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--surface-card);
  color: var(--foreground-muted);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.scope-btn:hover:not(:disabled) {
  opacity: 0.8;
}
.scope-btn.active {
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
}
.scope-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}
</style>
