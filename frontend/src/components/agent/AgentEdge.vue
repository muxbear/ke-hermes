<script setup lang="ts">
import { computed } from 'vue'
import { BaseEdge, getBezierPath } from '@vue-flow/core'
import type { EdgeProps } from '@vue-flow/core'

const props = defineProps<EdgeProps & { data: { status: string } }>()

const status = computed(() => props.data?.status ?? 'inactive')
const isActive = computed(() => status.value === 'active')

const edgePath = computed(() => {
  const [path] = getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition,
  })
  return path
})

const gradientId = computed(() => `edge-grad-${props.id}`)

const pathStyle = computed(() => ({
  stroke: `url(#${gradientId.value})`,
  strokeWidth: 2,
  strokeDasharray: isActive.value ? 'none' : '6,4',
  animation: isActive.value ? 'dashdraw 0.5s ease-in-out, dashmove 1s linear infinite' : 'none',
}))
</script>

<template>
  <svg width="0" height="0">
    <defs>
      <linearGradient :id="gradientId" x1="0%" y1="0%" x2="0%" y2="100%">
        <template v-if="isActive">
          <stop offset="0%" stop-color="#3b82f6" />
          <stop offset="100%" stop-color="#8b5cf6" />
        </template>
        <template v-else>
          <stop offset="0%" stop-color="#6b7280" />
          <stop offset="100%" stop-color="#4b5563" />
        </template>
      </linearGradient>
    </defs>
  </svg>
  <BaseEdge
    :id="id"
    :path="edgePath"
    :style="pathStyle"
    :marker-end="isActive ? 'url(#arrowActive)' : 'url(#arrowInactive)'"
  />
</template>

<style scoped>
@keyframes dashdraw {
  from { stroke-dashoffset: 24; }
  to { stroke-dashoffset: 0; }
}
@keyframes dashmove {
  to { stroke-dashoffset: -24; }
}
</style>
