<script setup lang="ts">
import {
  X, CheckCircle2, CircleAlert, Loader2, Minus, Workflow,
  Pause, FileText, Scissors, Sparkle, Hash, Brain, GitBranch, Database,
} from 'lucide-vue-next'
import type { KBDoc } from '@/types/knowledgeBase'

defineProps<{
  doc: KBDoc
}>()

defineEmits<{
  close: []
}>()

const stageIcons = [Pause, FileText, Scissors, Sparkle, Hash, Brain, GitBranch, Database]

function stageClass(status: string) {
  if (status === 'done') return 'stage-done'
  if (status === 'running') return 'stage-running'
  if (status === 'failed') return 'stage-failed'
  return 'stage-pending'
}

function stageStatusIcon(status: string) {
  if (status === 'done') return CheckCircle2
  if (status === 'running') return Loader2
  if (status === 'failed') return CircleAlert
  return Minus
}
</script>

<template>
  <div class="pipeline-panel">
    <div class="pipeline-header">
      <div class="pipeline-info">
        <div class="pipeline-name">{{ doc.name }}</div>
        <div class="pipeline-meta">{{ doc.size }} · {{ doc.uploadedAt }}</div>
      </div>
      <el-button text size="small" class="pipeline-close" @click="$emit('close')">
        <X :size="14" />
      </el-button>
    </div>

    <!-- 总进度 -->
    <div class="pipeline-overall">
      <div class="progress-header">
        <span class="progress-label">总进度</span>
        <span class="progress-value">{{ Math.round(doc.progress) }}%</span>
      </div>
      <el-progress
        :percentage="Math.round(doc.progress)"
        :stroke-width="6"
        :show-text="false"
      />
      <div class="progress-metrics">
        <div class="metric-item">
          <span class="metric-value">{{ doc.chunks }}</span>
          <span class="metric-label">分片</span>
        </div>
        <div class="metric-item">
          <span class="metric-value">{{ doc.entities }}</span>
          <span class="metric-label">实体</span>
        </div>
        <div class="metric-item">
          <span class="metric-value">{{ doc.relations }}</span>
          <span class="metric-label">关系</span>
        </div>
      </div>
    </div>

    <!-- 流水线阶段 -->
    <h4 class="pipeline-title"><Workflow :size="16" class="pipeline-title-icon" />索引流水线</h4>
    <div class="stage-list">
      <div
        v-for="(stage, i) in doc.stages"
        :key="i"
        :class="['stage-item', stageClass(stage.status)]"
      >
        <div class="stage-row">
          <component :is="stageIcons[i]" :size="14" class="stage-type-icon" />
          <span class="stage-name">{{ stage.name }}</span>
          <component
            :is="stageStatusIcon(stage.status)"
            :size="14"
            :class="{ 'spin-icon': stage.status === 'running' }"
          />
        </div>
        <el-progress
          v-if="stage.status === 'running'"
          :percentage="Math.round(stage.pct)"
          :stroke-width="3"
          :show-text="false"
          class="stage-progress"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.pipeline-panel {
  position: sticky;
  top: 100px;
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
}

.pipeline-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.pipeline-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.pipeline-meta {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-top: 2px;
}

.pipeline-close {
  color: var(--foreground-muted);
  padding: 2px;
}

.pipeline-overall {
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.progress-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
}

.progress-value {
  font-size: var(--font-size-xs);
  color: var(--foreground-primary);
}

.progress-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  text-align: center;
  margin-top: 10px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric-value {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
}

.metric-label {
  font-size: 10px;
  color: var(--foreground-muted);
}

.pipeline-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0 0 12px;
}

.pipeline-title-icon {
  color: #93c5fd;
}

.stage-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stage-item {
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid transparent;
}

.stage-done {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: #6ee7b7;
}

.stage-running {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
  color: #93c5fd;
}

.stage-failed {
  background: rgba(244, 63, 94, 0.1);
  border-color: rgba(244, 63, 94, 0.3);
  color: #fda4af;
}

.stage-pending {
  background: rgba(0, 0, 0, 0.15);
  border-color: var(--border-subtle);
  color: var(--foreground-muted);
}

.stage-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stage-type-icon {
  flex-shrink: 0;
}

.stage-name {
  flex: 1;
  font-size: var(--font-size-xs);
}

.stage-progress {
  margin-top: 8px;
}

.spin-icon {
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
