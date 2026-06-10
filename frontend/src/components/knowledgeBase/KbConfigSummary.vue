<script setup lang="ts">
import { computed } from 'vue'
import {
  Scissors, Sparkle, Hash, Brain, GitBranch, Target, Gauge,
} from 'lucide-vue-next'
import type { IndexConfig } from '@/types/knowledgeBase'
import { CHUNK_STRATEGY_OPTIONS } from '@/types/knowledgeBase'

const props = defineProps<{
  config: IndexConfig
}>()

const chunkLabel = computed(() => {
  const s = CHUNK_STRATEGY_OPTIONS.find((s) => s.value === props.config.chunkStrategy)
  return `${s?.label || props.config.chunkStrategy} · ${props.config.chunkSize}/${props.config.chunkOverlap}`
})

const rows = computed(() => [
  { icon: Scissors, label: '切片', value: chunkLabel.value },
  { icon: Sparkle, label: 'Embedding', value: `${props.config.embeddingModel} · ${props.config.embeddingDim}d` },
  { icon: Hash, label: '稀疏检索', value: props.config.sparseAlgo === 'none' ? '未启用' : props.config.sparseAlgo.toUpperCase() },
  { icon: Brain, label: '实体抽取', value: props.config.entityModel },
  { icon: GitBranch, label: '关系抽取', value: props.config.relationModel },
  { icon: Target, label: 'Reranker', value: props.config.enableReranker ? props.config.rerankerModel : '未启用' },
  { icon: Gauge, label: 'Top-K / α', value: `${props.config.topK} / ${props.config.hybridAlpha}` },
])
</script>

<template>
  <div class="config-summary">
    <div v-for="(row, i) in rows" :key="i" class="config-row">
      <component :is="row.icon" :size="14" class="config-icon" />
      <span class="config-label">{{ row.label }}</span>
      <span class="config-value">{{ row.value }}</span>
    </div>
  </div>
</template>

<style scoped>
.config-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-xs);
}

.config-icon {
  color: var(--foreground-secondary);
  flex-shrink: 0;
}

.config-label {
  color: var(--foreground-secondary);
  width: 72px;
  flex-shrink: 0;
}

.config-value {
  color: var(--foreground-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
