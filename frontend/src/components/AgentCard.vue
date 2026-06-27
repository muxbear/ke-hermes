<script setup lang="ts">
import { ref } from 'vue'
import { Bot, ChevronDown, ChevronRight, Loader, AlertCircle, CheckCircle } from 'lucide-vue-next'
import type { SubAgentInfo } from '@/types/chat'
import TraceTree from './TraceTree.vue'

const props = defineProps<{
  agent: SubAgentInfo
}>()

const collapsed = ref(true)

function statusLabel(status: string): string {
  switch (status) {
    case 'running': return '执行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    default: return status
  }
}
</script>

<template>
  <div class="agent-card" :class="agent.status">
    <div class="agent-header" @click="collapsed = !collapsed">
      <Bot :size="14" class="agent-icon" />
      <span class="agent-name">{{ agent.name }}</span>
      <span class="agent-status" :class="agent.status">{{ statusLabel(agent.status) }}</span>
      <Loader v-if="agent.status === 'running'" :size="12" class="spin" />
      <CheckCircle v-else-if="agent.status === 'completed'" :size="12" class="done-icon" />
      <AlertCircle v-else-if="agent.status === 'failed'" :size="12" class="error-icon" />
      <ChevronDown v-if="!collapsed" :size="14" class="chevron" />
      <ChevronRight v-else :size="14" class="chevron" />
    </div>
    <div v-if="!collapsed" class="agent-body">
      <TraceTree :blocks="agent.blocks" />
    </div>
  </div>
</template>

<style scoped>
.agent-card {
  border-left: 3px solid #7c3aed;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: rgba(124, 58, 237, 0.05);
  font-size: var(--font-size-xs);
  overflow: hidden;
}

.agent-card.failed {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  user-select: none;
  color: #6d28d9;
}

.agent-card.failed .agent-header {
  color: #b91c1c;
}

.agent-header:hover {
  background: rgba(124, 58, 237, 0.08);
}

.agent-card.failed .agent-header:hover {
  background: rgba(239, 68, 68, 0.08);
}

.agent-icon {
  flex-shrink: 0;
}

.agent-name {
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
}

.agent-status {
  margin-left: auto;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: rgba(124, 58, 237, 0.12);
  color: #6d28d9;
}

.agent-status.running {
  background: rgba(245, 158, 11, 0.12);
  color: #92400e;
}

.agent-status.completed {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
}

.agent-status.failed {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.chevron {
  flex-shrink: 0;
  opacity: 0.6;
}

.spin {
  animation: spin 1s linear infinite;
  color: #d97706;
}

.done-icon {
  color: #22c55e;
}

.error-icon {
  color: #ef4444;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.agent-body {
  padding: 4px 8px 8px;
}
</style>
