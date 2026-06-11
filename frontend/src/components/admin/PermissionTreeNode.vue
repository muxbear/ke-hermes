<script setup lang="ts">
import { Check, Minus, ChevronRight, ChevronDown } from 'lucide-vue-next'
import { PERM_TYPE_CONFIG } from '@/types/admin'
import type { PermResource } from '@/types/admin'

const props = defineProps<{
  node: PermResource
  depth: number
  checkState: 'all' | 'partial' | 'none'
  expandedIds: Set<string>
  readonly: boolean
  childrenList: PermResource[]
  subCount: number
  checkedCount: number
}>()

const emit = defineEmits<{
  toggle: [id: string]
  toggleExpand: [id: string]
}>()

const typeConfig = PERM_TYPE_CONFIG[props.node.type]

function isExpanded() {
  return props.expandedIds.has(props.node.id)
}
</script>

<template>
  <div>
    <div
      class="perm-row"
      :class="{ 'depth-0': depth === 0 }"
      :style="{ paddingLeft: `${depth * 20 + 12}px` }"
    >
      <button
        class="tri-check"
        :class="checkState"
        :disabled="readonly"
        @click="emit('toggle', node.id)"
      >
        <Check v-if="checkState === 'all'" :size="10" stroke-width="3" />
        <Minus v-else-if="checkState === 'partial'" :size="10" stroke-width="3" />
      </button>

      <button
        v-if="childrenList.length > 0"
        class="expand-btn"
        @click="emit('toggleExpand', node.id)"
      >
        <ChevronDown v-if="isExpanded()" :size="14" />
        <ChevronRight v-else :size="14" />
      </button>
      <span v-else class="expand-spacer" />

      <component :is="node.icon" :size="16" class="node-icon" :class="typeConfig.color" />

      <span class="node-label">{{ node.label }}</span>

      <span class="type-badge" :class="typeConfig.bg">
        {{ typeConfig.label }}
      </span>

      <code class="perm-key">{{ node.permKey }}</code>

      <span v-if="childrenList.length > 0" class="perm-count">
        {{ checkedCount }}/{{ subCount }}
      </span>
    </div>

    <template v-if="isExpanded() && childrenList.length > 0">
      <PermissionTreeNode
        v-for="child in childrenList"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :check-state="'none'"
        :expanded-ids="expandedIds"
        :readonly="readonly"
        :children-list="[]"
        :sub-count="0"
        :checked-count="0"
        @toggle="emit('toggle', $event)"
        @toggle-expand="emit('toggleExpand', $event)"
      />
    </template>
  </div>
</template>

<script lang="ts">
export default { name: 'PermissionTreeNode' }
</script>

<style scoped>
.perm-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}
.perm-row:hover { background: rgba(30, 41, 59, 0.3); }
.perm-row.depth-0 { background: rgba(30, 41, 59, 0.2); }
.tri-check {
  width: 16px; height: 16px;
  border-radius: 3px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--foreground-muted);
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
  padding: 0;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}
.tri-check.all {
  border-color: var(--accent-primary);
  background: var(--accent-primary);
  color: #fff;
}
.tri-check.partial {
  border-color: #60a5fa;
  background: rgba(59, 130, 246, 0.3);
  color: #93c5fd;
}
.tri-check:disabled { opacity: 0.6; cursor: not-allowed; }
.expand-btn {
  width: 18px; height: 18px;
  display: flex; align-items: center; justify-content: center;
  background: none; border: none;
  color: var(--foreground-muted);
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
}
.expand-btn:hover { color: var(--foreground-secondary); }
.expand-spacer { width: 18px; flex-shrink: 0; }
.node-icon { flex-shrink: 0; }
.node-label { font-size: var(--font-size-sm); color: var(--foreground-secondary); white-space: nowrap; }
.type-badge { font-size: 10px; padding: 1px 6px; border-radius: var(--radius-sm); flex-shrink: 0; }
.perm-key {
  font-size: 10px; font-family: monospace;
  padding: 1px 6px; border-radius: var(--radius-sm);
  background: var(--surface-primary); color: var(--foreground-muted);
}
.perm-count {
  margin-left: auto;
  font-size: 11px; color: var(--foreground-muted);
  flex-shrink: 0;
}
.text-blue-400 { color: #60a5fa; }
.text-sky-300 { color: #7dd3fc; }
.text-violet-300 { color: #c4b5fd; }
.text-amber-300 { color: #fcd34d; }
.text-cyan-300 { color: #67e8f9; }
.text-cyan-400 { color: #22d3ee; }
.text-purple-400 { color: #c084fc; }
.bg-blue-500\/15 { background: rgba(59,130,246,0.15); }
.bg-sky-500\/15 { background: rgba(14,165,233,0.15); }
.bg-violet-500\/15 { background: rgba(139,92,246,0.15); }
.bg-amber-500\/15 { background: rgba(245,158,11,0.15); }
.border-blue-500\/30 { border: 1px solid rgba(59,130,246,0.3); }
.border-sky-500\/30 { border: 1px solid rgba(14,165,233,0.3); }
.border-violet-500\/30 { border: 1px solid rgba(139,92,246,0.3); }
.border-amber-500\/30 { border: 1px solid rgba(245,158,11,0.3); }
</style>
