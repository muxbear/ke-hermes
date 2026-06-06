<script setup lang="ts">
import { computed } from 'vue'
import { Pencil, Trash2, Lock, Package, ToggleLeft, ToggleRight } from 'lucide-vue-next'
import type { Tool } from '@/types/tool'
import { CATEGORY_META, STATUS_META, SOURCE_LABELS } from '@/types/tool'
import { getToolIcon } from './iconMap'

const props = defineProps<{ tool: Tool }>()

const emit = defineEmits<{
  (e: 'edit', tool: Tool): void
  (e: 'delete', id: string): void
  (e: 'toggle', id: string): void
  (e: 'detail', tool: Tool): void
}>()

const cm = computed(() => CATEGORY_META[props.tool.category])
const sm = computed(() => STATUS_META[props.tool.status])
const isBuiltin = computed(() => props.tool.source === 'builtin')
const isUnavailable = computed(() => props.tool.status === 'unavailable')
const iconComponent = computed(() => getToolIcon(cm.value.icon))
</script>

<template>
  <div class="tool-card" :class="{ 'tool-card--dimmed': isUnavailable }">
    <!-- Top row: icon + name + toggle -->
    <div class="card-top">
      <div class="card-top__left">
        <div class="icon-box" :style="{ background: cm.bg, borderColor: cm.border }">
          <component :is="iconComponent" :size="16" :style="{ color: cm.color }" />
        </div>
        <div class="name-area">
          <div class="name-row">
            <span class="display-name">{{ tool.displayName }}</span>
            <span v-if="isBuiltin" class="builtin-tag">
              <Lock :size="10" />
              内置
            </span>
          </div>
          <span class="tool-id">{{ tool.name }}</span>
        </div>
      </div>

      <!-- Toggle -->
      <div class="card-top__right">
        <button
          v-if="!isUnavailable && !isBuiltin"
          class="toggle-btn"
          :title="tool.status === 'enabled' ? '禁用' : '启用'"
          @click="emit('toggle', tool.id)"
        >
          <ToggleRight v-if="tool.status === 'enabled'" :size="20" class="toggle-on" />
          <ToggleLeft v-else :size="20" class="toggle-off" />
        </button>
        <div v-else-if="isBuiltin && !isUnavailable" class="toggle-disabled" title="内置工具状态不可修改">
          <ToggleRight v-if="tool.status === 'enabled'" :size="20" class="toggle-on--dimmed" />
          <ToggleLeft v-else :size="20" class="toggle-off--dimmed" />
        </div>
      </div>
    </div>

    <!-- Description -->
    <p class="card-desc">{{ tool.description }}</p>

    <!-- Tags -->
    <div v-if="tool.tags.length > 0" class="card-tags">
      <span v-for="tag in tool.tags.slice(0, 4)" :key="tag" class="tag-chip">{{ tag }}</span>
    </div>

    <!-- Footer -->
    <div class="card-footer">
      <div class="badges">
        <span class="badge" :style="{ background: sm.bg, borderColor: sm.border, color: sm.color }">
          <component :is="getToolIcon(sm.icon)" :size="12" />
          {{ sm.label }}
        </span>
        <span class="badge" :style="{ background: cm.bg, borderColor: cm.border, color: cm.color }">
          {{ cm.label }}
        </span>
      </div>
      <div class="hover-actions">
        <button class="action-btn" title="查看详情" @click="emit('detail', tool)">
          <Package :size="14" />
        </button>
        <template v-if="!isBuiltin">
          <button class="action-btn" title="编辑" @click="emit('edit', tool)">
            <Pencil :size="14" />
          </button>
          <button class="action-btn action-btn--danger" title="删除" @click="emit('delete', tool.id)">
            <Trash2 :size="14" />
          </button>
        </template>
      </div>
    </div>

    <!-- Agent usage -->
    <div v-if="tool.usedByAgents.length > 0" class="agent-usage">
      <span v-for="a in tool.usedByAgents" :key="a" class="agent-chip">{{ a }}</span>
    </div>
  </div>
</template>

<style scoped>
.tool-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: border-color var(--transition-fast), background var(--transition-fast), opacity var(--transition-fast);
}

.tool-card:hover {
  border-color: rgba(59, 130, 246, 0.2);
  background: rgba(15, 23, 46, 0.6);
}

.tool-card--dimmed {
  opacity: 0.6;
}

/* Top row */
.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.card-top__left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.icon-box {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.name-area {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.display-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.builtin-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.12);
  color: var(--foreground-muted);
  font-size: 10px;
  flex-shrink: 0;
}

.tool-id {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 11px;
  color: var(--foreground-muted);
}

/* Toggle */
.toggle-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--foreground-muted);
  transition: background var(--transition-fast);
  flex-shrink: 0;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.06);
}

.toggle-on { color: #10b981; }
.toggle-off { color: var(--foreground-muted); }
.toggle-on--dimmed { color: #10b981; opacity: 0.5; }
.toggle-off--dimmed { color: var(--foreground-muted); opacity: 0.3; }

.toggle-disabled {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* Description */
.card-desc {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
}

/* Tags */
.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag-chip {
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--surface-secondary);
  color: var(--foreground-muted);
  font-size: 11px;
}

/* Footer */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.badges {
  display: flex;
  align-items: center;
  gap: 6px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 9999px;
  border: 1px solid;
  font-size: 11px;
}

/* Hover actions */
.hover-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.tool-card:hover .hover-actions {
  opacity: 1;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--foreground-muted);
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--foreground-primary);
}

.action-btn--danger:hover {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

/* Agent usage */
.agent-usage {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.agent-chip {
  padding: 1px 8px;
  border-radius: 4px;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  font-size: 11px;
}
</style>
