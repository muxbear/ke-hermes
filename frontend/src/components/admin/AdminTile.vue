<script setup lang="ts">
import { ChevronRight } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import type { Component } from 'vue'

const props = defineProps<{
  icon: Component
  title: string
  description: string
  gradient: string
  route?: string
}>()

const router = useRouter()

function handleClick() {
  if (props.route) {
    router.push(props.route)
  }
}
</script>

<template>
  <div
    class="admin-tile"
    :class="{ 'is-clickable': !!route }"
    @click="handleClick"
  >
    <div class="tile-inner">
      <div
        class="tile-icon"
        :style="{ backgroundImage: gradient }"
      >
        <component :is="icon" :size="20" />
      </div>
      <div class="tile-body">
        <div class="tile-header">
          <span class="tile-title">{{ title }}</span>
          <ChevronRight
            :size="16"
            :class="route ? 'arrow-active' : 'arrow-hidden'"
          />
        </div>
        <p class="tile-desc">{{ description }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-tile {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 16px;
  transition: border-color var(--transition-duration), background var(--transition-duration);
}
.admin-tile.is-clickable {
  cursor: pointer;
}
.admin-tile.is-clickable:hover {
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(20, 29, 56, 0.6);
}
.tile-inner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.tile-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--accent-primary);
}
.tile-body {
  flex: 1;
  min-width: 0;
}
.tile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.tile-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
}
.arrow-active {
  color: var(--foreground-muted);
  transition: transform var(--transition-fast), color var(--transition-fast);
  flex-shrink: 0;
}
.admin-tile.is-clickable:hover .arrow-active {
  color: var(--accent-primary);
  transform: translateX(2px);
}
.arrow-hidden {
  color: transparent;
  flex-shrink: 0;
}
.tile-desc {
  margin-top: 4px;
  font-size: var(--font-size-xs);
  line-height: 1.6;
  color: var(--foreground-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
