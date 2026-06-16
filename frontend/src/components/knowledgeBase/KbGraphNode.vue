<script setup lang="ts">
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'

const props = defineProps<{
  id: string
  data: {
    name: string
    type: string
    mentions: number
    color: string
    hovered: boolean
    selected: boolean
    dimmed: boolean
  }
}>()

const ENTITY_COLORS: Record<string, string> = {
  '人物': '#60a5fa',
  '组织': '#a78bfa',
  '产品': '#34d399',
  '概念': '#fbbf24',
  '算法': '#f87171',
}

const nodeColor = computed(() => ENTITY_COLORS[props.data.type] || '#94a3b8')
const circleSize = computed(() => Math.min(56, 40 + props.data.mentions * 2))
</script>

<template>
  <div
    class="kb-graph-node"
    :class="{
      'kb-graph-node--selected': data.selected,
      'kb-graph-node--dimmed': data.dimmed,
    }"
  >
    <Handle type="target" :position="Position.Top" :connectable="false" />
    <div
      class="node-sphere"
      :style="{
        background: `radial-gradient(circle at 35% 35%, ${nodeColor}66, ${nodeColor}22)`,
        borderColor: nodeColor,
        width: circleSize + 'px',
        height: circleSize + 'px',
      }"
    >
      <span class="node-sphere-text">{{ data.name.length > 3 ? data.name.slice(0, 3) : data.name }}</span>
    </div>
    <span class="node-label">{{ data.name }}</span>
    <Handle type="source" :position="Position.Bottom" :connectable="false" />
  </div>
</template>

<style scoped>
.kb-graph-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: grab;
  transition: opacity 0.2s, filter 0.2s;
}

.kb-graph-node:active {
  cursor: grabbing;
}

.kb-graph-node--dimmed {
  opacity: 0.2;
}

.node-sphere {
  border-radius: 50%;
  border: 3px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.3);
}

.kb-graph-node:hover .node-sphere {
  transform: scale(1.12);
}

.kb-graph-node--selected .node-sphere {
  transform: scale(1.08);
  box-shadow: 0 0 24px var(--node-glow, rgba(59, 130, 246, 0.5));
}

.node-sphere-text {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.node-label {
  font-size: 12px;
  font-weight: 500;
  color: #cbd5e1;
  text-align: center;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

:deep(.vue-flow__handle) {
  opacity: 0;
  pointer-events: none;
}
</style>
