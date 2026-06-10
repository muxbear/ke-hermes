<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  icon: Component
  color: string
  label: string
  value: number | string
  sub?: string
  pulse?: boolean
}>()
</script>

<template>
  <div class="stat-card">
    <div class="stat-top">
      <div :class="['stat-icon-box', color]">
        <component :is="icon" :size="16" :class="{ 'pulse-icon': pulse }" />
      </div>
      <span class="stat-label">{{ label }}</span>
    </div>
    <div class="stat-bottom">
      <span class="stat-value">{{ value }}</span>
      <span v-if="sub" class="stat-sub">{{ sub }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  padding: 16px 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
}

.stat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.stat-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
}

.stat-icon-box.blue-cyan { background: linear-gradient(135deg, #3b82f6, #06b6d4); }
.stat-icon-box.purple-pink { background: linear-gradient(135deg, #8b5cf6, #ec4899); }
.stat-icon-box.emerald-teal { background: linear-gradient(135deg, #10b981, #14b8a6); }
.stat-icon-box.amber-orange { background: linear-gradient(135deg, #f59e0b, #f97316); }
.stat-icon-box.rose-red { background: linear-gradient(135deg, #f43f5e, #ef4444); }

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

.stat-bottom {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
}

.stat-sub {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.pulse-icon {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
