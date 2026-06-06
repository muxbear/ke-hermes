<script setup lang="ts">
import { computed } from 'vue'
import { X } from 'lucide-vue-next'
import type { Tool } from '@/types/tool'
import { CATEGORY_META, STATUS_META } from '@/types/tool'
import { getToolIcon } from './iconMap'

const props = defineProps<{ tool: Tool }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const cm = computed(() => CATEGORY_META[props.tool.category])
const sm = computed(() => STATUS_META[props.tool.status])
const CatIcon = computed(() => getToolIcon(cm.value.icon))
</script>

<template>
  <Teleport to="body">
    <div class="drawer-overlay" @click="emit('close')">
      <div class="drawer-panel" @click.stop>
        <!-- Header -->
        <div class="drawer-header">
          <div class="drawer-header__left">
            <div class="drawer-icon" :style="{ background: cm.bg, borderColor: cm.border }">
              <component :is="CatIcon" :size="16" :style="{ color: cm.color }" />
            </div>
            <div>
              <h3 class="drawer-title">{{ tool.displayName }}</h3>
              <p class="drawer-sub">{{ tool.name }}</p>
            </div>
          </div>
          <button class="drawer-close" @click="emit('close')">
            <X :size="16" />
          </button>
        </div>

        <!-- Body -->
        <div class="drawer-body">
          <!-- Metadata -->
          <div class="meta-grid">
            <div v-for="[k, v] in [
              ['来源', tool.source === 'builtin' ? '内置工具' : '第三方工具'],
              ['分类', cm.label],
              ['版本', tool.version],
              ['作者', tool.author],
              ['状态', sm.label],
            ]" :key="k" class="meta-row">
              <span class="meta-key">{{ k }}</span>
              <span class="meta-value">{{ v }}</span>
            </div>
          </div>

          <!-- Description -->
          <div class="section">
            <p class="section-label">描述</p>
            <p class="section-text">{{ tool.description }}</p>
          </div>

          <!-- Parameters -->
          <div v-if="tool.params && tool.params.length > 0" class="section">
            <p class="section-label">参数列表</p>
            <div class="param-list">
              <div v-for="p in tool.params" :key="p.key" class="param-row">
                <div class="param-left">
                  <span class="param-key">{{ p.key }}</span>
                  <span class="param-label">{{ p.label }}</span>
                </div>
                <div class="param-right">
                  <span class="param-type">{{ p.type }}</span>
                  <span v-if="p.required" class="param-required">必填</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Agents -->
          <div v-if="tool.usedByAgents.length > 0" class="section">
            <p class="section-label">使用中的代理</p>
            <div class="chip-list">
              <span v-for="a in tool.usedByAgents" :key="a" class="chip chip--agent">{{ a }}</span>
            </div>
          </div>

          <!-- Tags -->
          <div v-if="tool.tags.length > 0" class="section">
            <p class="section-label">标签</p>
            <div class="chip-list">
              <span v-for="t in tool.tags" :key="t" class="chip chip--tag">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  display: flex;
  justify-content: flex-end;
  background: rgba(0, 0, 0, 0.4);
}

.drawer-panel {
  width: 380px;
  max-width: 90vw;
  height: 100%;
  overflow-y: auto;
  background: var(--color-bg-form-area);
  border-left: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
}

.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

.drawer-header__left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.drawer-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.drawer-title {
  font-size: 16px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.drawer-sub {
  margin: 2px 0 0;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 11px;
  color: var(--foreground-muted);
}

.drawer-close {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.drawer-close:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-primary);
}

.drawer-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
}

/* Metadata */
.meta-grid {
  background: rgba(15, 23, 46, 0.4);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--font-size-sm);
}

.meta-key { color: var(--foreground-secondary); }
.meta-value { color: var(--color-text-primary); }

/* Sections */
.section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-size: 11px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.section-text {
  font-size: var(--font-size-base);
  color: var(--foreground-primary);
  line-height: 1.6;
  margin: 0;
}

/* Parameters */
.param-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.param-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(15, 23, 46, 0.4);
  border-radius: 8px;
}

.param-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-key {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  color: #818cf8;
}

.param-label {
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
}

.param-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.param-type {
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.1);
  font-size: 11px;
  color: var(--foreground-secondary);
}

.param-required {
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.2);
  font-size: 10px;
  color: #f87171;
}

/* Chips */
.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.chip--agent {
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.chip--tag {
  background: rgba(148, 163, 184, 0.08);
  color: var(--foreground-secondary);
}
</style>
