<script setup lang="ts">
import { ChevronRight, ChevronDown, Building2 } from 'lucide-vue-next'
import type { Department } from '@/types/admin'

const props = defineProps<{
  department: Department
  depth: number
  selectedId: string | null
  expandedIds: Set<string>
}>()

const emit = defineEmits<{
  select: [id: string]
  toggle: [id: string]
}>()

function isExpanded(): boolean {
  return props.expandedIds.has(props.department.id)
}

function isSelected(): boolean {
  return props.selectedId === props.department.id
}
</script>

<template>
  <div>
    <div
      class="dept-node"
      :class="{ 'is-selected': isSelected() }"
      :style="{ paddingLeft: `${depth * 16 + 8}px` }"
      @click="emit('select', department.id)"
    >
      <button
        v-if="department.children.length > 0"
        class="expand-btn"
        @click.stop="emit('toggle', department.id)"
      >
        <ChevronDown v-if="isExpanded()" :size="14" />
        <ChevronRight v-else :size="14" />
      </button>
      <span v-else class="expand-spacer" />
      <Building2 :size="16" class="dept-icon" />
      <span class="dept-name">{{ department.name }}</span>
      <span class="dept-count">{{ department.memberCount }}</span>
    </div>
    <template v-if="isExpanded() && department.children.length > 0">
      <DepartmentTreeNode
        v-for="child in department.children"
        :key="child.id"
        :department="child"
        :depth="depth + 1"
        :selected-id="selectedId"
        :expanded-ids="expandedIds"
        @select="emit('select', $event)"
        @toggle="emit('toggle', $event)"
      />
    </template>
  </div>
</template>

<script lang="ts">
// 自引用组件
export default { name: 'DepartmentTreeNode' }
</script>

<style scoped>
.dept-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
  border: 1px solid transparent;
}
.dept-node:hover {
  background: rgba(30, 41, 59, 0.4);
}
.dept-node.is-selected {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
}
.expand-btn {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--foreground-muted);
  cursor: pointer;
  flex-shrink: 0;
  padding: 0;
}
.expand-btn:hover {
  color: var(--foreground-secondary);
}
.expand-spacer {
  width: 20px;
  flex-shrink: 0;
}
.dept-icon {
  color: var(--foreground-muted);
  flex-shrink: 0;
}
.dept-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dept-count {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  background: rgba(30, 41, 59, 0.6);
  padding: 1px 6px;
  border-radius: var(--radius-full);
}
</style>
