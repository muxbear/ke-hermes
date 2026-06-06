<script setup lang="ts">
import { computed } from 'vue'
import {
  ChevronRight,
  ChevronDown,
  MoreVertical,
  Play,
  Pause,
  Copy,
  Trash2,
  Activity,
  Zap,
  Sparkles,
  GitBranch,
  Edit,
  Edit3,
  UserPlus,
} from 'lucide-vue-next'
import type { Agent } from '@/types/agent'
import { STATUS_LABELS } from '@/types/agent'

const props = withDefaults(
  defineProps<{
    agent: Agent
    agents: Agent[]
    selectedId: string | null
    expandedIds: Set<string>
    searchQuery: string
    level?: number
  }>(),
  { level: 0 },
)

const emit = defineEmits<{
  (e: 'select', agent: Agent): void
  (e: 'toggle-expand', id: string): void
  (e: 'toggle-status', id: string): void
  (e: 'clone', agent: Agent): void
  (e: 'delete', id: string): void
  (e: 'new-sub-agent'): void
  (e: 'edit', agent: Agent): void
}>()

const isSelected = computed(() => props.selectedId === props.agent.id)
const isExpanded = computed(() => props.expandedIds.has(props.agent.id))
const hasChildren = computed(
  () => props.agent.subAgents && props.agent.subAgents.length > 0,
)

const childAgents = computed(() => {
  if (!hasChildren.value) return []
  return props.agents.filter((a) => props.agent.subAgents?.includes(a.id))
})

function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
      return 'status--active'
    case 'error':
      return 'status--error'
    default:
      return 'status--inactive'
  }
}

function getStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status
}
</script>

<template>
  <div class="agent-tree-item">
    <div
      class="agent-item"
      :class="{ selected: isSelected }"
      :style="{ paddingLeft: `${level * 16 + 12}px` }"
      @click="emit('select', agent)"
    >
      <!-- 展开/折叠按钮 -->
      <button
        v-if="hasChildren && !searchQuery"
        class="expand-btn"
        @click.stop="emit('toggle-expand', agent.id)"
      >
        <ChevronDown v-if="isExpanded" :size="14" />
        <ChevronRight v-else :size="14" />
      </button>
      <span v-else class="expand-placeholder" />

      <!-- 主信息 -->
      <div class="item-main">
        <div class="item-top-row">
          <span class="agent-name">{{ agent.name }}</span>
          <span class="status-badge" :class="getStatusColor(agent.status)">
            <Activity v-if="agent.status === 'active'" :size="10" />
            <Pause v-else-if="agent.status === 'inactive'" :size="10" />
            <Zap v-else :size="10" />
            {{ getStatusLabel(agent.status) }}
          </span>
          <span v-if="agent.type === 'main'" class="type-badge type-badge--main">
            主智能体
          </span>
        </div>
        <p class="item-desc">{{ agent.description }}</p>
        <div class="item-stats">
          <span class="stat-item">
            <Activity :size="11" />
            {{ agent.callCount ?? 0 }}
          </span>
          <span class="stat-item">
            <Zap :size="11" />
            {{ agent.tools?.length ?? 0 }}
          </span>
          <span class="stat-item">
            <Sparkles :size="11" />
            {{ agent.skills?.length ?? 0 }}
          </span>
          <span v-if="hasChildren" class="stat-item stat-item--sub">
            <GitBranch :size="11" />
            {{ agent.subAgents?.length ?? 0 }}
          </span>
          <span v-if="isSelected" class="editing-label">
            <Edit :size="10" />
            编辑中
          </span>
        </div>
      </div>

      <!-- 操作菜单 -->
      <el-dropdown trigger="click" @click.stop @command="(cmd: string) => {
        if (cmd === 'newSubAgent') emit('new-sub-agent')
        else if (cmd === 'edit') emit('edit', agent)
        else if (cmd === 'toggle') emit('toggle-status', agent.id)
        else if (cmd === 'clone') emit('clone', agent)
        else if (cmd === 'delete') emit('delete', agent.id)
      }">
        <button class="more-btn" @click.stop>
          <MoreVertical :size="14" />
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="newSubAgent">
              <UserPlus :size="14" />
              <span style="margin-left: 8px">新建</span>
            </el-dropdown-item>
            <el-dropdown-item command="edit">
              <Edit3 :size="14" />
              <span style="margin-left: 8px">编辑</span>
            </el-dropdown-item>
            <el-dropdown-item divided command="toggle">
              <Pause v-if="agent.status === 'active'" :size="14" />
              <Play v-else :size="14" />
              <span style="margin-left: 8px">
                {{ agent.status === 'active' ? '停止' : '启动' }}
              </span>
            </el-dropdown-item>
            <el-dropdown-item command="clone">
              <Copy :size="14" />
              <span style="margin-left: 8px">克隆</span>
            </el-dropdown-item>
            <el-dropdown-item v-if="!agent.undeletable" divided command="delete" style="color: #ef4444">
              <Trash2 :size="14" />
              <span style="margin-left: 8px">删除</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 子智能体（递归） -->
    <div v-if="hasChildren && (isExpanded || searchQuery)" class="children">
      <div
        v-if="!searchQuery"
        class="tree-line"
        :style="{ left: `${level * 16 + 19}px` }"
      />
      <AgentListItem
        v-for="child in childAgents"
        :key="child.id"
        :agent="child"
        :agents="agents"
        :selected-id="selectedId"
        :expanded-ids="expandedIds"
        :search-query="searchQuery"
        :level="level + 1"
        @select="(a) => emit('select', a)"
        @toggle-expand="(id) => emit('toggle-expand', id)"
        @toggle-status="(id) => emit('toggle-status', id)"
        @clone="(a) => emit('clone', a)"
        @delete="(id) => emit('delete', id)"
        @new-sub-agent="() => emit('new-sub-agent')"
        @edit="(a) => emit('edit', a)"
      />
    </div>
  </div>
</template>

<style scoped>
.agent-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.agent-item:hover {
  background: var(--surface-secondary);
  border-color: var(--border-subtle);
}

.agent-item.selected {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.3);
}

.expand-btn {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: var(--foreground-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  margin-top: 2px;
}

.expand-btn:hover {
  background: var(--border-subtle);
  color: var(--foreground-primary);
}

.expand-placeholder {
  width: 18px;
  flex-shrink: 0;
}

.item-main {
  flex: 1;
  min-width: 0;
}

.item-top-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.agent-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: var(--font-size-xs);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  line-height: 1.4;
}

.status--active {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.status--inactive {
  background: rgba(107, 114, 128, 0.15);
  color: #9ca3af;
}

.status--error {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.type-badge {
  font-size: var(--font-size-xs);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  line-height: 1.4;
}

.type-badge--main {
  background: rgba(59, 130, 246, 0.15);
  color: var(--color-accent);
}

.item-desc {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin: 4px 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.stat-item--sub {
  color: #f97316;
}

.editing-label {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: var(--color-accent);
}

.more-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.agent-item:hover .more-btn {
  opacity: 1;
}

.more-btn:hover {
  background: var(--border-subtle);
  color: var(--foreground-primary);
}

.children {
  position: relative;
}

.tree-line {
  position: absolute;
  top: 0;
  bottom: 8px;
  width: 1px;
  background: var(--border-subtle);
}
</style>
