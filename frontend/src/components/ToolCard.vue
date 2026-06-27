<script setup lang="ts">
import { ref } from 'vue'
import { Wrench, ChevronDown, ChevronRight, Loader, CheckCircle } from 'lucide-vue-next'
import type { ToolCallInfo } from '@/types/chat'

const props = defineProps<{
  tool: ToolCallInfo
}>()

const collapsed = ref(true)
const expandedInput = ref(false)
const expandedOutput = ref(false)

function truncate(s: string, maxLen = 300): string {
  if (!s) return ''
  if (s.length <= maxLen) return s
  return s.slice(0, maxLen) + '...'
}

function statusLabel(status: string): string {
  switch (status) {
    case 'running': return '调用中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    default: return status
  }
}
</script>

<template>
  <div class="tool-card" :class="tool.status">
    <div class="tool-header" @click="collapsed = !collapsed">
      <Wrench :size="14" class="tool-icon" />
      <span class="tool-name">{{ tool.name }}</span>
      <span class="tool-status" :class="tool.status">{{ statusLabel(tool.status) }}</span>
      <Loader v-if="tool.status === 'running'" :size="12" class="spin" />
      <CheckCircle v-else-if="tool.status === 'completed'" :size="12" class="done-icon" />
      <ChevronDown v-if="!collapsed" :size="14" class="chevron" />
      <ChevronRight v-else :size="14" class="chevron" />
    </div>
    <div v-if="!collapsed" class="tool-body">
      <div class="tool-section" v-if="tool.input">
        <div class="tool-section-label" @click="expandedInput = !expandedInput">
          Input
          <ChevronDown v-if="!expandedInput" :size="10" />
          <ChevronRight v-else :size="10" />
        </div>
        <code v-if="expandedInput" class="tool-code">{{ tool.input }}</code>
        <code v-else class="tool-code truncated">{{ truncate(tool.input) }}</code>
      </div>
      <div class="tool-section" v-if="tool.output">
        <div class="tool-section-label" @click="expandedOutput = !expandedOutput">
          Output
          <ChevronDown v-if="!expandedOutput" :size="10" />
          <ChevronRight v-else :size="10" />
        </div>
        <code v-if="expandedOutput" class="tool-code">{{ tool.output }}</code>
        <code v-else class="tool-code truncated">{{ truncate(tool.output) }}</code>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tool-card {
  border-left: 3px solid #d97706;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: rgba(245, 158, 11, 0.05);
  font-size: var(--font-size-xs);
  overflow: hidden;
}

.tool-card.failed {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  user-select: none;
  color: #b45309;
}

.tool-card.failed .tool-header {
  color: #b91c1c;
}

.tool-header:hover {
  background: rgba(245, 158, 11, 0.08);
}

.tool-card.failed .tool-header:hover {
  background: rgba(239, 68, 68, 0.08);
}

.tool-icon {
  flex-shrink: 0;
}

.tool-name {
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
}

.tool-status {
  margin-left: auto;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: rgba(245, 158, 11, 0.12);
  color: #92400e;
}

.tool-status.completed {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
}

.tool-status.failed {
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

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.tool-body {
  padding: 4px 8px 8px;
}

.tool-section {
  margin-top: 4px;
}

.tool-section-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-muted);
  cursor: pointer;
  margin-bottom: 2px;
}

.tool-code {
  display: block;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.03);
  font-size: 11px;
  color: var(--foreground-secondary);
  font-family: 'Consolas', 'Monaco', monospace;
  word-break: break-all;
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
}

.tool-code.truncated {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
