<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { X } from 'lucide-vue-next'
import SlidePuzzle from './SlidePuzzle.vue'
import ImageCaptcha from './ImageCaptcha.vue'
import type { CaptchaResult } from '@/types/components'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    type?: 'slide' | 'image'
  }>(),
  {
    type: 'slide',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: [result: CaptchaResult]
  fail: []
}>()

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    close()
  }
}

function close() {
  emit('update:modelValue', false)
}

function onSuccess(result: CaptchaResult) {
  emit('success', result)
}

function onFail() {
  emit('fail')
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="captcha-overlay" @click.self="close">
        <div class="captcha-modal">
          <div class="captcha-header">
            <span class="captcha-title">安全验证</span>
            <button class="captcha-close" @click="close">
              <X :size="18" />
            </button>
          </div>
          <div class="captcha-body">
            <SlidePuzzle v-if="type === 'slide'" @success="onSuccess" @fail="onFail" />
            <ImageCaptcha v-else @success="onSuccess" @fail="onFail" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.captcha-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-overlay);
  z-index: 9999;
}

.captcha-modal {
  width: 400px;
  max-width: 90vw;
  background: var(--color-modal-bg);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-card);
  overflow: hidden;
}

.captcha-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-input);
}

.captcha-title {
  font-size: 16px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.captcha-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
}

.captcha-close:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-primary);
}

.captcha-body {
  padding: 24px;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-normal);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
