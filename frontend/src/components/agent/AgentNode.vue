<script setup lang="ts">
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { Activity, Pause, Zap } from 'lucide-vue-next'
import { useAgentStore } from '@/stores/agent'
import type { Agent } from '@/types/agent'

const props = defineProps<{
  id: string
  data: { agent: Agent; isMain: boolean }
  selected: boolean
}>()

const agentStore = useAgentStore()

const agent = computed(() => props.data.agent)
const isMain = computed(() => props.data.isMain)

function handleClick() {
  agentStore.selectAgent(agent.value.id)
}

function statusIconClass(status: string): string {
  switch (status) {
    case 'active': return 'status--active'
    case 'error': return 'status--error'
    default: return 'status--inactive'
  }
}
</script>

<template>
  <div
    class="agent-node"
    :class="{ 'agent-node--selected': selected }"
    @click="handleClick"
  >
    <Handle v-if="!isMain" type="target" :position="Position.Top" :connectable="false" class="node-handle" />
    <div class="node-card" :class="{ 'node-card--sub': !isMain }">
      <div class="node-card-top">
        <div class="node-status-icon" :class="statusIconClass(agent.status)">
          <Activity v-if="agent.status === 'active'" :size="14" />
          <Pause v-else-if="agent.status === 'inactive'" :size="14" />
          <Zap v-else :size="14" />
        </div>
        <div class="node-card-info">
          <span class="node-card-name">{{ agent.name }}</span>
          <span class="node-card-meta" :class="isMain ? 'node-card-meta--main' : 'node-card-meta--sub'">
            {{ isMain ? '主智能体' : '' }}
            {{ isMain ? ' · ' : '' }}
            {{ agent.status === 'active' ? '运行中' : agent.status === 'inactive' ? '已停止' : '错误' }}
          </span>
        </div>
      </div>
      <div class="node-card-stats">
        <div class="node-stat">
          <span class="node-stat-label">工具</span>
          <span class="node-stat-value">{{ agent.tools?.length ?? 0 }}</span>
        </div>
        <div class="node-stat">
          <span class="node-stat-label">技能</span>
          <span class="node-stat-value">{{ agent.skills?.length ?? 0 }}</span>
        </div>
        <div class="node-stat">
          <span class="node-stat-label">{{ isMain ? '子智能体' : '调用' }}</span>
          <span class="node-stat-value">{{ isMain ? (agent.subAgents?.length ?? 0) : (agent.callCount ?? 0) }}</span>
        </div>
      </div>
    </div>
    <Handle v-if="isMain" type="source" :position="Position.Bottom" :connectable="false" class="node-handle" />
  </div>
</template>

<style scoped>
.agent-node {
  cursor: grab;
  transition: filter 0.2s ease, transform 0.15s ease;
}

.agent-node:active {
  cursor: grabbing;
}

.agent-node:hover {
  filter: brightness(1.1);
}

.agent-node--selected .node-card {
  box-shadow: 0 0 28px rgba(59, 130, 246, 0.4);
}

.node-handle {
  width: 8px;
  height: 8px;
  background: #7c3aed;
  border: 2px solid rgba(255, 255, 255, 0.3);
  opacity: 0;
}

.node-card {
  width: 240px;
  padding: 16px;
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%);
  border: 2px solid rgba(34, 197, 94, 0.5);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}

.node-card--sub {
  background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 0 16px rgba(139, 92, 246, 0.25);
}

.node-card-top {
  display: flex;
  align-items: center;
  gap: 10px;
}

.node-status-icon {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.status--active {
  background: rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.status--inactive {
  background: rgba(107, 114, 128, 0.3);
  color: #9ca3af;
}

.status--error {
  background: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.node-card-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.node-card-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: white;
}

.node-card-meta {
  font-size: var(--font-size-xs);
  opacity: 0.8;
}

.node-card-meta--main {
  color: #93c5fd;
}

.node-card-meta--sub {
  color: #d8b4fe;
}

.node-card-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.node-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.node-stat-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.55);
}

.node-stat-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  color: white;
}
</style>
