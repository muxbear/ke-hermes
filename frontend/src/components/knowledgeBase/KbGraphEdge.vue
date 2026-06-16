<script setup lang="ts">
import { computed } from 'vue'
import { BaseEdge, getBezierPath } from '@vue-flow/core'
import type { EdgeProps } from '@vue-flow/core'

const props = defineProps<EdgeProps & { data: { label: string; highlighted: boolean; dimmed: boolean } }>()

const highlighted = computed(() => props.data?.highlighted ?? false)
const dimmed = computed(() => props.data?.dimmed ?? false)

const edgePath = computed(() => {
  const [path, labelX, labelY] = getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition,
  })
  return { path, labelX, labelY }
})

const pathStyle = computed(() => ({
  stroke: highlighted.value ? '#60a5fa' : '#475569',
  strokeWidth: highlighted.value ? 2.5 : 1.5,
  opacity: dimmed.value ? 0.1 : 0.6,
  transition: 'all 0.2s',
}))

const labelX = computed(() => edgePath.value.labelX)
const labelY = computed(() => edgePath.value.labelY)
const labelText = computed(() => props.data?.label ?? '')
</script>

<template>
  <svg width="0" height="0">
    <defs>
      <marker id="arrowNormal" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
      </marker>
      <marker id="arrowHighlighted" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#60a5fa" />
      </marker>
    </defs>
  </svg>
  <BaseEdge
    :id="id"
    :path="edgePath.path"
    :style="pathStyle"
    :marker-end="highlighted ? 'url(#arrowHighlighted)' : 'url(#arrowNormal)'"
  />
  <text
    v-if="!dimmed && labelText"
    :x="labelX"
    :y="labelY - 6"
    fill="#94a3b8"
    font-size="11"
    text-anchor="middle"
    pointer-events="none"
  >
    {{ labelText }}
  </text>
</template>
