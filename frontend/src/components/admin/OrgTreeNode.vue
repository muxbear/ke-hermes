<script setup lang="ts">
import { computed } from 'vue'
import { ChevronDown, ChevronRight, Plus, Edit2, Trash2, Building2, Briefcase, Layers, Users } from 'lucide-vue-next'
import type { OrgNode } from '@/types/admin'
import { ORG_TYPE_CONFIG } from '@/types/admin'
import { useOrgDeptStore } from '@/stores/orgDept'

const props = defineProps<{
  node: OrgNode
  depth: number
  selectedId: string | null
  expandedIds: Set<string>
  visibleIds: Set<string>
  searchQuery: string
}>()

const emit = defineEmits<{
  select: [id: string]
  toggle: [id: string]
  addChild: [id: string]
  edit: [node: OrgNode]
  delete: [node: OrgNode]
}>()

const store = useOrgDeptStore()

const iconMap: Record<string, any> = { Building2, Briefcase, Layers, Users }

function getIcon(name: string) {
  return iconMap[name] ?? Building2
}

const isSelected = computed(() => props.selectedId === props.node.id)
const isExpanded = computed(() => props.expandedIds.has(props.node.id))
const hasChildren = computed(() => store.getChildren(props.node.id).length > 0)
const visibleChildren = computed(() =>
  store.getChildren(props.node.id).filter((c) => props.visibleIds.has(c.id)),
)
const isMatch = computed(() =>
  props.searchQuery &&
  (props.node.name.toLowerCase().includes(props.searchQuery.toLowerCase()) ||
   props.node.code.toLowerCase().includes(props.searchQuery.toLowerCase())),
)
</script>

<template>
  <div>
    <div
      :class="['od-tree-node', { selected: isSelected }]"
      :style="{ paddingLeft: `${depth * 16 + 8}px` }"
    >
      <button
        :class="['od-tree-toggle', { invisible: !hasChildren }]"
        @click.stop="emit('toggle', node.id)"
      >
        <ChevronDown v-if="isExpanded" :size="14" />
        <ChevronRight v-else :size="14" />
      </button>
      <div class="od-tree-content" @click="emit('select', node.id)">
        <component
          :is="getIcon(ORG_TYPE_CONFIG[node.type].icon)"
          :size="14"
          :class="['od-tree-type-icon', { selected: isSelected }]"
        />
        <span :class="['od-tree-name', { selected: isSelected, match: isMatch }]">
          {{ node.name }}
        </span>
        <span v-if="node.status === 'inactive'" class="od-tree-badge">停用</span>
      </div>
      <span class="od-tree-count">{{ node.employeeCount }}</span>
      <div class="od-tree-actions">
        <button
          class="od-tree-action add"
          title="添加子节点"
          @click.stop="emit('addChild', node.id)"
        >
          <Plus :size="12" />
        </button>
        <button
          class="od-tree-action edit"
          title="编辑"
          @click.stop="emit('edit', node)"
        >
          <Edit2 :size="12" />
        </button>
        <button
          v-if="node.parentId !== null"
          class="od-tree-action del"
          title="删除"
          @click.stop="emit('delete', node)"
        >
          <Trash2 :size="12" />
        </button>
      </div>
    </div>
    <div v-if="isExpanded && visibleChildren.length > 0">
      <OrgTreeNode
        v-for="child in visibleChildren"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :selected-id="selectedId"
        :expanded-ids="expandedIds"
        :visible-ids="visibleIds"
        :search-query="searchQuery"
        @select="emit('select', $event)"
        @toggle="emit('toggle', $event)"
        @add-child="emit('addChild', $event)"
        @edit="emit('edit', $event)"
        @delete="emit('delete', $event)"
      />
    </div>
  </div>
</template>

<script lang="ts">
export default { name: 'OrgTreeNode' }
</script>

<style scoped>
.od-tree-node {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 5px 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  border: 1px solid transparent;
  transition: background var(--transition-duration);
}
.od-tree-node:hover { background: rgba(59,130,246,0.06); }
.od-tree-node.selected {
  background: rgba(59,130,246,0.12);
  border-color: rgba(59,130,246,0.25);
}
.od-tree-toggle {
  width: 16px; height: 16px;
  display: flex; align-items: center; justify-content: center;
  background: none; border: none;
  color: var(--foreground-muted);
  cursor: pointer; padding: 0;
  flex-shrink: 0;
}
.od-tree-toggle:hover { color: var(--foreground-primary); }
.od-tree-toggle.invisible { visibility: hidden; }
.od-tree-content {
  display: flex; align-items: center; gap: 6px;
  flex: 1; min-width: 0;
}
.od-tree-type-icon {
  color: var(--foreground-muted); flex-shrink: 0;
}
.od-tree-type-icon.selected { color: var(--accent-primary); }
.od-tree-name {
  font-size: var(--font-size-sm); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  color: var(--foreground-primary);
}
.od-tree-name.match { color: #fbbf24; }
.od-tree-badge {
  font-size: 9px; padding: 0 4px;
  border-radius: var(--radius-sm);
  background: rgba(100,116,139,0.15);
  color: var(--foreground-muted);
  flex-shrink: 0;
}
.od-tree-count {
  font-size: 10px; color: var(--foreground-muted);
  flex-shrink: 0; margin-right: 2px;
}
.od-tree-actions {
  display: flex; align-items: center; gap: 1px;
  opacity: 0; transition: opacity var(--transition-duration);
  flex-shrink: 0;
}
.od-tree-node:hover .od-tree-actions { opacity: 1; }
.od-tree-action {
  width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  background: none; border: none;
  border-radius: var(--radius-sm);
  cursor: pointer; padding: 0; color: var(--foreground-muted);
}
.od-tree-action.add:hover { color: var(--accent-primary); background: rgba(59,130,246,0.15); }
.od-tree-action.edit:hover { color: #22d3ee; background: rgba(6,182,212,0.15); }
.od-tree-action.del:hover { color: #fb7185; background: rgba(244,63,94,0.15); }
</style>
