<script setup lang="ts">
import { computed } from 'vue'
import {
  Database, CheckCircle2, Loader2, CircleAlert, Pause,
  Sparkle, Scissors, Hash, Network,
} from 'lucide-vue-next'
import type { KB } from '@/types/knowledgeBase'
import { KB_STATUS_CONFIG, CHUNK_STRATEGY_OPTIONS } from '@/types/knowledgeBase'

const props = defineProps<{
  kb: KB
}>()

const emit = defineEmits<{
  click: []
}>()

const statusCfg = computed(() => KB_STATUS_CONFIG[props.kb.status])

const statusIcon = computed(() => {
  switch (props.kb.status) {
    case 'ready': return CheckCircle2
    case 'indexing': return Loader2
    case 'error': return CircleAlert
    case 'draft': return Pause
    default: return CheckCircle2
  }
})

const chunkLabel = computed(() => {
  const s = CHUNK_STRATEGY_OPTIONS.find((s) => s.value === props.kb.config.chunkStrategy)
  return s?.label || props.kb.config.chunkStrategy
})

function metricFormat(val: number): string {
  return val >= 1000 ? (val / 1000).toFixed(val % 1000 === 0 ? 0 : 1) + 'k' : String(val)
}
</script>

<template>
  <div class="kb-card" @click="emit('click')">
    <!-- 头部 -->
    <div class="card-header">
      <div class="card-header-left">
        <div class="card-icon-box">
          <Database :size="20" />
        </div>
        <div class="card-title-area">
          <div class="card-title">{{ kb.name }}</div>
          <div class="card-meta">更新于 {{ kb.updatedAt }} · {{ kb.size }}</div>
        </div>
      </div>
      <el-tag :class="['status-badge', statusCfg.cls]" size="small" disable-transitions>
        <component
          :is="statusIcon"
          :size="12"
          :class="{ 'spin-icon': kb.status === 'indexing' }"
        />
        {{ statusCfg.label }}
      </el-tag>
    </div>

    <!-- 描述 -->
    <p class="card-desc">{{ kb.description }}</p>

    <!-- 标签 -->
    <div class="card-tags">
      <el-tag
        v-for="t in kb.tags"
        :key="t"
        size="small"
        class="card-tag"
      >
        {{ t }}
      </el-tag>
    </div>

    <div class="card-divider" />

    <!-- 指标 -->
    <div class="card-metrics">
      <div class="metric">
        <span class="metric-value">{{ kb.docs }}</span>
        <span class="metric-label">文档</span>
      </div>
      <div class="metric">
        <span class="metric-value">{{ metricFormat(kb.chunks) }}</span>
        <span class="metric-label">分片</span>
      </div>
      <div class="metric">
        <span class="metric-value">{{ metricFormat(kb.entities) }}</span>
        <span class="metric-label">实体</span>
      </div>
      <div class="metric">
        <span class="metric-value">{{ metricFormat(kb.relations) }}</span>
        <span class="metric-label">关系</span>
      </div>
    </div>

    <!-- 配置标记 -->
    <div class="card-configs">
      <el-tag size="small" class="config-badge config-blue">
        <Sparkle :size="10" class="config-icon" />{{ kb.config.embeddingModel }}
      </el-tag>
      <el-tag size="small" class="config-badge config-purple">
        <Scissors :size="10" class="config-icon" />{{ chunkLabel }}
      </el-tag>
      <el-tag v-if="kb.config.sparseAlgo !== 'none'" size="small" class="config-badge config-amber">
        <Hash :size="10" class="config-icon" />{{ kb.config.sparseAlgo.toUpperCase() }}
      </el-tag>
      <el-tag v-if="kb.config.enableGraph" size="small" class="config-badge config-green">
        <Network :size="10" class="config-icon" />知识图谱
      </el-tag>
    </div>
  </div>
</template>

<style scoped>
.kb-card {
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  cursor: pointer;
  transition: all 0.2s;
}

.kb-card:hover {
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(20, 29, 56, 0.8);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.card-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
  border: 1px solid rgba(59, 130, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #93c5fd;
  flex-shrink: 0;
}

.card-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.card-meta {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-top: 2px;
}

.status-badge {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.status-ready {
  background: rgba(16, 185, 129, 0.15);
  color: #6ee7b7;
  border-color: rgba(16, 185, 129, 0.3);
}

.status-indexing {
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
  border-color: rgba(59, 130, 246, 0.3);
}

.status-error {
  background: rgba(244, 63, 94, 0.15);
  color: #fda4af;
  border-color: rgba(244, 63, 94, 0.3);
}

.status-draft {
  background: rgba(100, 116, 139, 0.15);
  color: #94a3b8;
  border-color: rgba(100, 116, 139, 0.3);
}

.spin-icon {
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.card-desc {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 36px;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
}

.card-tag {
  background: rgba(100, 116, 139, 0.1);
  color: var(--foreground-primary);
  border-color: rgba(100, 116, 139, 0.3);
  font-size: 10px;
}

.card-divider {
  height: 1px;
  background: var(--border-subtle);
  margin-bottom: 12px;
}

.card-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  text-align: center;
  margin-bottom: 12px;
}

.metric {
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

.card-configs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.config-badge {
  font-size: 10px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.config-icon {
  flex-shrink: 0;
}

.config-blue {
  background: rgba(59, 130, 246, 0.1);
  color: #93c5fd;
  border-color: rgba(59, 130, 246, 0.3);
}

.config-purple {
  background: rgba(139, 92, 246, 0.1);
  color: #c4b5fd;
  border-color: rgba(139, 92, 246, 0.3);
}

.config-amber {
  background: rgba(245, 158, 11, 0.1);
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.3);
}

.config-green {
  background: rgba(16, 185, 129, 0.1);
  color: #6ee7b7;
  border-color: rgba(16, 185, 129, 0.3);
}
</style>
