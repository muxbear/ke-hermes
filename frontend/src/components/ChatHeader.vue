<script setup>
import { Sparkles, ChevronDown } from 'lucide-vue-next'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()
</script>

<template>
  <div class="chat-header">
    <div class="header-left">
      <span class="header-avatar">
        <Sparkles :size="16" />
      </span>
      <span class="header-title">Hermes 智能体</span>
    </div>
    <div class="header-right">
      <div class="model-selector">
        <span class="model-name">{{ uiStore.selectedModel }}</span>
        <ChevronDown :size="14" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-header {
  height: var(--chat-header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--surface-card);
  border-bottom: 1px solid var(--border-subtle);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--accent-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 15px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
  border: 1px solid var(--border-medium);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
  cursor: pointer;
}

.model-name {
  color: var(--foreground-primary);
}
</style>