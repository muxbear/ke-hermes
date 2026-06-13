<script setup lang="ts">
import { ref, computed } from 'vue'
import { Bot, Wrench, ChevronDown, ChevronRight, Loader } from 'lucide-vue-next'
import type { TraceEntry } from '@/types/chat'

const props = defineProps<{
  traces: TraceEntry[]
  streaming: boolean
}>()

const collapsed = ref(false)

const toolCount = computed(() => props.traces.filter((t) => t.type === 'tool_start').length)
const agentNames = computed(() => {
  const names = new Set<string>()
  for (const t of props.traces) {
    if (t.agent) names.add(t.agent)
  }
  return [...names]
})

// Track which tool names have been ended
const endedTools = computed(() => {
  const ended = new Set<string>()
  for (const t of props.traces) {
    if (t.type === 'tool_end') ended.add(t.name)
  }
  return ended
})

function typeLabel(entry: TraceEntry): string {
  switch (entry.type) {
    case 'agent_start': return '开始处理'
    case 'agent_end': return '处理完成'
    case 'tool_start':
      if (!props.streaming && !endedTools.value.has(entry.name)) return '执行失败'
      return '调用中...'
    case 'tool_end': return '已完成'
    default: return entry.type
  }
}

function isToolActive(entry: TraceEntry): boolean {
  return entry.type === 'tool_start' && props.streaming && !endedTools.value.has(entry.name)
}

const expandedOutputs = ref<Set<number>>(new Set())

function toggleOutput(id: number) {
  const s = new Set(expandedOutputs.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  expandedOutputs.value = s
}

function truncate(s: string, maxLen = 200): string {
  if (s.length <= maxLen) return s
  return s.slice(0, maxLen) + '...'
}
</script>

<template>
  <div class="trace-panel">
    <div class="trace-header" @click="collapsed = !collapsed">
      <Wrench :size="14" />
      <span class="trace-summary">
        <template v-if="agentNames.length">{{ agentNames.join(', ') }} · </template>
        {{ toolCount }} 个工具调用
      </span>
      <ChevronDown v-if="!collapsed" :size="14" class="chevron" />
      <ChevronRight v-else :size="14" class="chevron" />
    </div>

    <div v-if="!collapsed" class="trace-entries">
      <div
        v-for="entry in traces"
        :key="entry.id"
        class="trace-entry"
        :class="entry.type"
      >
        <div class="trace-entry-row">
          <Bot v-if="entry.type === 'agent_start' || entry.type === 'agent_end'" :size="12" class="trace-icon agent-icon" />
          <Wrench v-else :size="12" class="trace-icon tool-icon" />
          <span class="trace-name">{{ entry.type.startsWith('agent') ? entry.name : `${entry.name}` }}</span>
          <span class="trace-status" :class="entry.type">{{ typeLabel(entry) }}</span>
          <Loader v-if="isToolActive(entry)" :size="10" class="spin" />
        </div>

        <div v-if="entry.input" class="trace-detail" @click="toggleOutput(entry.id)">
          <span class="trace-detail-label">Input:</span>
          <code>{{ expandedOutputs.has(entry.id) ? entry.input : truncate(entry.input) }}</code>
        </div>
        <div v-if="entry.output" class="trace-detail" @click="toggleOutput(entry.id)">
          <span class="trace-detail-label">Output:</span>
          <code>{{ expandedOutputs.has(entry.id) ? entry.output : truncate(entry.output) }}</code>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.trace-panel {
  margin-bottom: 10px;
  border-left: 3px solid #f59e0b;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: rgba(245, 158, 11, 0.06);
  font-size: var(--font-size-xs);
  overflow: hidden;
}

.trace-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  color: #b45309;
  user-select: none;
}

.trace-header:hover {
  background: rgba(245, 158, 11, 0.1);
}

.trace-summary {
  flex: 1;
  font-weight: var(--font-weight-medium);
}

.chevron {
  flex-shrink: 0;
  color: #b45309;
}

.trace-entries {
  padding: 0 6px 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.trace-entry {
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  background: rgba(245, 158, 11, 0.04);
}

.trace-entry-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.trace-icon {
  flex-shrink: 0;
}

.agent-icon {
  color: #7c3aed;
}

.tool-icon {
  color: #d97706;
}

.trace-name {
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
}

.trace-status {
  margin-left: auto;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: rgba(245, 158, 11, 0.15);
  color: #92400e;
}

.trace-status.agent_start,
.trace-status.agent_end {
  background: rgba(124, 58, 237, 0.12);
  color: #6d28d9;
}

.trace-detail {
  margin-top: 2px;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.03);
  cursor: pointer;
  word-break: break-all;
}

.trace-detail-label {
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-muted);
  margin-right: 4px;
}

.trace-detail code {
  font-size: 11px;
  color: var(--foreground-secondary);
  font-family: 'Consolas', 'Monaco', monospace;
}

.spin {
  animation: spin 1s linear infinite;
  color: #d97706;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
