<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls, ControlButton } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { Lock, Unlock, Maximize2, Minimize2 } from 'lucide-vue-next'
import { useAgentGraph } from '@/composables/useAgentGraph'

const {
  nodeTypes,
  edgeTypes,
  graphNodes,
  graphEdges,
  hasAgents,
  onNodeClick,
} = useAgentGraph()

const { fitView } = useVueFlow()

const isLocked = ref(false)
const isMaximized = ref(false)

const nodesDraggable = computed(() => !isLocked.value)
const panOnDrag = computed(() => !isLocked.value)
const zoomOnScroll = computed(() => !isLocked.value)

async function toggleMaximize() {
  isMaximized.value = !isMaximized.value
  await nextTick()
  setTimeout(() => fitView({ duration: 300, padding: 0.2 }), 50)
}

function onPaneReady() {
  setTimeout(() => fitView({ duration: 500, padding: 0.2 }), 100)
}

function minimapNodeColor(node: { data?: { agent?: { status?: string } } }) {
  return node.data?.agent?.status === 'active' ? '#4ade80' : '#6b7280'
}
</script>

<template>
  <div class="agent-graph" :class="{ 'agent-graph--maximized': isMaximized }">
    <!-- Header -->
    <div class="graph-header">
      <span class="graph-title">主智能体关系图</span>
      <div class="graph-header-right">
        <span class="graph-badge">实时拓扑</span>
        <button
          class="graph-header-btn"
          :title="isLocked ? '解锁' : '锁定'"
          @click="isLocked = !isLocked"
        >
          <Unlock v-if="isLocked" :size="16" />
          <Lock v-else :size="16" />
        </button>
        <button
          class="graph-header-btn"
          :title="isMaximized ? '还原' : '最大化'"
          @click="toggleMaximize"
        >
          <Minimize2 v-if="isMaximized" :size="16" />
          <Maximize2 v-else :size="16" />
        </button>
      </div>
    </div>

    <!-- Vue Flow Canvas -->
    <div class="graph-canvas">
      <svg width="0" height="0">
        <defs>
          <marker id="arrowActive" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b5cf6" />
          </marker>
          <marker id="arrowInactive" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280" />
          </marker>
        </defs>
      </svg>

      <VueFlow
        v-if="hasAgents"
        v-model:nodes="graphNodes"
        v-model:edges="graphEdges"
        :node-types="nodeTypes"
        :edge-types="edgeTypes"
        :nodes-draggable="nodesDraggable"
        :pan-on-drag="panOnDrag"
        :zoom-on-scroll="zoomOnScroll"
        :fit-view-on-init="false"
        :default-viewport="{ x: 0, y: 0, zoom: 1 }"
        :min-zoom="0.2"
        :max-zoom="2"
        @node-click="onNodeClick"
        @pane-ready="onPaneReady"
      >
        <Background :gap="20" :size="1" pattern-color="rgba(255,255,255,0.04)" />
        <Controls position="bottom-right" />
        <MiniMap
          position="bottom-left"
          :pannable="true"
          :zoomable="true"
          :node-stroke-color="() => '#7c3aed'"
          :node-color="minimapNodeColor"
          mask-color="rgba(0,0,0,0.7)"
        />
      </VueFlow>

      <!-- Empty state -->
      <div v-else class="graph-empty">
        <p>暂无代理数据</p>
        <span>请先创建代理</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-graph {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.agent-graph--maximized {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: var(--surface-primary);
}

.agent-graph--maximized .graph-canvas {
  height: 100%;
}

.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.graph-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.graph-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.graph-badge {
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--color-accent);
}

.graph-header-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--foreground-muted);
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease, transform 0.3s ease;
}

.graph-header-btn:hover {
  color: var(--foreground-primary);
  background: var(--surface-secondary);
}

.graph-canvas {
  flex: 1;
  min-height: 0;
  position: relative;
}

.graph-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
}

/* Vue Flow overrides for dark theme */
:deep(.vue-flow__background) {
  background-color: var(--surface-card);
}

:deep(.vue-flow__controls) {
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border-subtle);
}

:deep(.vue-flow__controls-button) {
  background: var(--surface-card);
  border-bottom: 1px solid var(--border-subtle);
  width: 28px;
  height: 28px;
}

:deep(.vue-flow__controls-button svg) {
  fill: var(--foreground-secondary);
}

:deep(.vue-flow__controls-button:hover) {
  background: var(--surface-secondary);
}

:deep(.vue-flow__minimap) {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: var(--surface-card);
}
</style>
