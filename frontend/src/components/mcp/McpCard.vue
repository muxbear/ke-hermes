<script setup lang="ts">
import { computed } from 'vue'
import { Download, Star } from 'lucide-vue-next'
import type { McpTool } from '@/types/mcp'

const props = defineProps<{ tool: McpTool }>()

const emit = defineEmits<{
  (e: 'install', tool: McpTool): void
  (e: 'click', tool: McpTool): void
}>()

const installCount = computed(() => {
  if (props.tool.installs >= 1000) {
    return `${(props.tool.installs / 1000).toFixed(1)}K`
  }
  return String(props.tool.installs)
})

function handleInstall() {
  emit('install', props.tool)
}

function handleClick() {
  emit('click', props.tool)
}
</script>

<template>
  <div class="mcp-card" @click="handleClick">
    <div class="card-header">
      <div class="icon-box">
        <span class="icon-text">{{ tool.icon }}</span>
      </div>
      <div class="name-col">
        <div class="name-row">
          <span class="tool-name">{{ tool.name }}</span>
          <span v-if="tool.official" class="official-badge">官方</span>
        </div>
        <span class="tool-author">{{ tool.author }}</span>
      </div>
    </div>

    <p class="card-desc">{{ tool.description }}</p>

    <div class="card-tags">
      <span v-for="tag in tool.tags" :key="tag" class="tag">{{ tag }}</span>
    </div>

    <div class="card-footer">
      <div class="stats">
        <span class="stat-item">
          <Download :size="13" />
          {{ installCount }}
        </span>
        <span class="stat-item rating">
          <Star :size="13" />
          {{ tool.rating }}
        </span>
      </div>
      <button
        class="install-btn"
        :class="{ installed: tool.installed }"
        @click.stop="handleInstall"
      >
        {{ tool.installed ? '已安装' : '安装' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.mcp-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  cursor: pointer;
  transition: border-color var(--transition-fast), transform var(--transition-fast);
}

.mcp-card:hover {
  border-color: rgba(59, 130, 246, 0.25);
  transform: translateY(-1px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-box {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-text {
  font-size: 22px;
  line-height: 1;
}

.name-col {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.official-badge {
  font-size: 10px;
  font-weight: var(--font-weight-medium);
  color: var(--accent-primary);
  background: rgba(59, 130, 246, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.tool-author {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

.card-desc {
  font-size: var(--font-size-base);
  color: var(--foreground-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
  line-height: 1.5;
}

.card-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
  background: rgba(38, 51, 89, 0.2);
  padding: 4px 10px;
  border-radius: 6px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-item.rating {
  color: #f59e0b;
}

.install-btn {
  display: flex;
  align-items: center;
  padding: 6px 16px;
  border-radius: 8px;
  border: none;
  background: rgba(59, 130, 246, 0.15);
  color: var(--accent-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.install-btn:hover {
  background: rgba(59, 130, 246, 0.25);
}

.install-btn.installed {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}
</style>
