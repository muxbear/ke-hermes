<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    countdown: number
    disabled?: boolean
  }>(),
  {
    disabled: false,
  },
)

const emit = defineEmits<{
  click: []
}>()

const label = computed(() => {
  if (props.countdown > 0) return `${props.countdown}s`
  return '获取验证码'
})
</script>

<template>
  <el-button
    :disabled="disabled || countdown > 0"
    class="countdown-btn"
    @click="emit('click')"
  >
    {{ label }}
  </el-button>
</template>

<style scoped>
.countdown-btn {
  height: var(--size-input-height);
  border-radius: var(--radius-input);
  font-size: var(--font-size-agreement);
  flex-shrink: 0;
  min-width: 110px;
}
</style>
