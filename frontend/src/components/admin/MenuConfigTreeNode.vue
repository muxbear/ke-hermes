<script setup lang="ts">
import { ChevronRight, ChevronDown, Plus, Edit2, Trash2, Lock } from 'lucide-vue-next'
import { PERM_TYPE_CONFIG, PERM_STATUS_CONFIG } from '@/types/admin'
import type { PermResource } from '@/types/admin'

const props = defineProps<{
  resource: PermResource
  depth: number
  selectedId: string | null
  expandedIds: Set<string>
  childrenList: PermResource[]
}>()

const emit = defineEmits<{
  select: [id: string]
  toggleExpand: [id: string]
  addChild: [resource: PermResource]
  edit: [resource: PermResource]
  delete: [resource: PermResource]
}>()
</script>

<template>
  <div>
    <div
      class="tree-node"
      :class="{ active: selectedId === resource.id }"
      :style="{ paddingLeft: `${depth * 16 + 8}px` }"
      @click="emit('select', resource.id)"
    >
      <button
        class="expand-btn"
        :class="{ invisible: childrenList.length === 0 }"
        @click.stop="emit('toggleExpand', resource.id)"
      >
        <ChevronDown v-if="expandedIds.has(resource.id)" :size="14" />
        <ChevronRight v-else :size="14" />
      </button>

      <div class="node-icon" :class="PERM_TYPE_CONFIG[resource.type].bg">
        <component :is="resource.icon" :size="14" :class="PERM_TYPE_CONFIG[resource.type].color" />
      </div>

      <div class="node-body">
        <div class="node-label-row">
          <span class="node-label">{{ resource.label }}</span>
          <span class="type-badge" :class="PERM_TYPE_CONFIG[resource.type].bg">
            {{ PERM_TYPE_CONFIG[resource.type].label }}
          </span>
          <span v-if="resource.isBuiltin" class="builtin-badge">
            <Lock :size="10" />内置
          </span>
          <span
            v-if="resource.status !== 'active'"
            class="status-badge"
            :class="PERM_STATUS_CONFIG[resource.status].color"
          >
            {{ PERM_STATUS_CONFIG[resource.status].label }}
          </span>
        </div>
        <div class="node-key">{{ resource.permKey }}</div>
      </div>

      <div class="node-actions">
        <button
          v-if="resource.type !== 'button'"
          class="action-btn"
          @click.stop="emit('addChild', resource)"
          title="添加子节点"
        >
          <Plus :size="14" />
        </button>
        <button class="action-btn" @click.stop="emit('edit', resource)" title="编辑">
          <Edit2 :size="14" />
        </button>
        <button
          v-if="!resource.isBuiltin"
          class="action-btn danger"
          @click.stop="emit('delete', resource)"
          title="删除"
        >
          <Trash2 :size="14" />
        </button>
      </div>
    </div>

    <!-- 递归子节点 -->
    <template v-if="expandedIds.has(resource.id) && childrenList.length > 0">
      <MenuConfigTreeNode
        v-for="child in childrenList"
        :key="child.id"
        :resource="child"
        :depth="depth + 1"
        :selected-id="selectedId"
        :expanded-ids="expandedIds"
        :children-list="[]"
        @select="emit('select', $event)"
        @toggle-expand="emit('toggleExpand', $event)"
        @add-child="emit('addChild', $event)"
        @edit="emit('edit', $event)"
        @delete="emit('delete', $event)"
      />
    </template>
  </div>
</template>

<script lang="ts">
export default { name: 'MenuConfigTreeNode' }
</script>

<style scoped>
.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
  border: 1px solid transparent;
}
.tree-node:hover { background: rgba(30,41,59,0.3); }
.tree-node.active {
  background: linear-gradient(90deg, rgba(59,130,246,0.12), rgba(139,92,246,0.06));
  border-color: rgba(59,130,246,0.3);
}
.expand-btn {
  width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  background: none; border: none;
  color: var(--foreground-muted);
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
}
.expand-btn.invisible { visibility: hidden; }
.expand-btn:hover { color: var(--foreground-secondary); }
.node-icon {
  width: 28px; height: 28px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.node-body { flex: 1; min-width: 0; }
.node-label-row { display: flex; align-items: center; gap: 6px; }
.node-label { font-size: var(--font-size-sm); color: var(--foreground-primary); white-space: nowrap; }
.type-badge {
  font-size: 10px; padding: 1px 6px; border-radius: var(--radius-sm);
  display: flex; align-items: center; gap: 3px;
}
.builtin-badge {
  font-size: 10px; padding: 1px 6px; border-radius: var(--radius-sm);
  background: rgba(100,116,139,0.1); color: var(--foreground-muted);
  border: 1px solid rgba(100,116,139,0.3);
  display: flex; align-items: center; gap: 3px;
}
.status-badge {
  font-size: 10px; padding: 1px 6px; border-radius: var(--radius-sm);
}
.node-key {
  font-size: var(--font-size-xs);
  font-family: monospace;
  color: var(--foreground-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.node-actions {
  display: flex; gap: 2px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.tree-node:hover .node-actions { opacity: 1; }
.action-btn {
  padding: 4px;
  background: none; border: none;
  color: var(--foreground-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  display: flex; align-items: center;
}
.action-btn:hover { background: rgba(30,41,59,0.6); color: var(--foreground-primary); }
.action-btn.danger:hover { background: rgba(239,68,68,0.15); color: #fca5a5; }
.text-amber-300 { color: #fcd34d; }
.text-sky-300 { color: #7dd3fc; }
.text-violet-300 { color: #c4b5fd; }
.bg-amber-500\/15 { background: rgba(245,158,11,0.15); }
.bg-sky-500\/15 { background: rgba(14,165,233,0.15); }
.bg-violet-500\/15 { background: rgba(139,92,246,0.15); }
.border-amber-500\/30 { border: 1px solid rgba(245,158,11,0.3); }
.border-sky-500\/30 { border: 1px solid rgba(14,165,233,0.3); }
.border-violet-500\/30 { border: 1px solid rgba(139,92,246,0.3); }
</style>
