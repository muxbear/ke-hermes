<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RefreshCw, ArrowRight, Check, AlertCircle } from 'lucide-vue-next'
import { captchaApi } from '@/services/captchaApi'
import type { CaptchaResult } from '@/types/components'

const emit = defineEmits<{
  success: [result: CaptchaResult]
  fail: []
}>()

type PuzzleStatus = 'loading' | 'idle' | 'dragging' | 'verifying' | 'fail' | 'success'

const status = ref<PuzzleStatus>('loading')
const bgImage = ref('')
const slideImage = ref('')
const sliderY = ref(0)
const sliderX = ref(0)
const sessionId = ref('')
const maxSlider = 250

let dragStartX = 0
let dragStartLeft = 0

const isDragging = computed(() => status.value === 'dragging')
const isVerifying = computed(() => status.value === 'verifying')

function toDataUrl(b64: string) {
  return `data:image/png;base64,${b64}`
}

async function fetchPuzzle() {
  try {
    status.value = 'loading'
    sliderX.value = 0
    const res = await captchaApi.getSlidePuzzle()
    bgImage.value = toDataUrl(res.data.data.bgImage)
    slideImage.value = toDataUrl(res.data.data.slideImage)
    sliderY.value = res.data.data.y
    sessionId.value = res.data.data.sessionId
    status.value = 'idle'
  } catch (err) {
    console.error('Failed to fetch captcha:', err)
    status.value = 'fail'
  }
}

async function verify() {
  status.value = 'verifying'
  try {
    const res = await captchaApi.verifySlide({
      sessionId: sessionId.value,
      distance: sliderX.value,
      track: [],
    })
    if (res.data.data.success) {
      status.value = 'success'
      setTimeout(() => {
        emit('success', {
          ticket: res.data.data.ticket || '',
          randstr: res.data.data.randstr || '',
        })
      }, 500)
    } else {
      status.value = 'fail'
    }
  } catch (err) {
    console.error('Captcha verify failed:', err)
    status.value = 'fail'
  }
}

function onPointerDown(e: PointerEvent) {
  if (status.value !== 'idle') return
  status.value = 'dragging'
  dragStartX = e.clientX
  dragStartLeft = sliderX.value
  ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (status.value !== 'dragging') return
  const delta = e.clientX - dragStartX
  sliderX.value = Math.max(0, Math.min(maxSlider, dragStartLeft + delta))
}

function onPointerUp(_e: PointerEvent) {
  if (status.value !== 'dragging') return
  if (sliderX.value > 2) {
    verify()
  } else {
    status.value = 'idle'
  }
}

function refresh() {
  fetchPuzzle()
}

onMounted(() => {
  fetchPuzzle()
})
</script>

<template>
  <div class="slide-puzzle">
    <!-- fail -->
    <div v-if="status === 'fail'" class="puzzle-state">
      <div class="state-icon fail">
        <AlertCircle :size="32" />
      </div>
      <p class="state-text">验证未通过，请重试</p>
      <button class="retry-btn" @click="refresh">
        <RefreshCw :size="14" />
        <span>刷新验证码</span>
      </button>
    </div>

    <!-- loading -->
    <div v-else-if="status === 'loading'" class="puzzle-state">
      <div class="puzzle-canvas loading-canvas">
        <div class="loading-shimmer" />
      </div>
    </div>

    <!-- success -->
    <div v-else-if="status === 'success'" class="puzzle-state">
      <div class="state-icon success">
        <Check :size="32" />
      </div>
      <p class="state-text">验证通过</p>
    </div>

    <!-- active -->
    <div v-else class="puzzle-container">
      <div class="puzzle-header">
        <span class="puzzle-label">请拖动滑块，使拼图与缺口对齐</span>
        <button class="refresh-btn" title="刷新验证码" @click="refresh">
          <RefreshCw :size="14" />
        </button>
      </div>
      <div
        class="puzzle-canvas"
        :class="{ 'is-dragging': isDragging, 'is-verifying': isVerifying }"
      >
        <img v-if="bgImage" :src="bgImage" class="puzzle-bg-img" alt="" />
        <img
          v-if="slideImage"
          :src="slideImage"
          class="puzzle-slide-img"
          :class="{ 'is-dragging': isDragging }"
          :style="{ left: sliderX + 'px', top: sliderY + 'px' }"
          alt=""
        />
      </div>
      <div class="slider-track">
        <div class="slider-bar" :class="{ dragging: isDragging, verifying: isVerifying }">
          <div class="slider-fill" :style="{ width: sliderX + 'px' }" />
          <div
            class="slider-thumb"
            :class="{ dragging: isDragging, verifying: isVerifying }"
            :style="{ left: sliderX + 'px' }"
            @pointerdown="onPointerDown"
            @pointermove="onPointerMove"
            @pointerup="onPointerUp"
          >
            <ArrowRight v-if="!isVerifying" :size="16" class="thumb-arrow" />
            <span v-else class="thumb-spinner" />
          </div>
        </div>
        <span class="slider-hint">
          <template v-if="isVerifying">验证中...</template>
          <template v-else-if="isDragging">松开滑块完成验证</template>
          <template v-else>向右拖动滑块完成验证</template>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-puzzle {
  display: flex;
  flex-direction: column;
  user-select: none;
}

/* ---- States ---- */
.puzzle-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px 20px;
  min-height: 230px;
}

.state-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.state-icon.fail {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.state-icon.success {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.state-text {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.retry-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  background: var(--color-bg-input);
  color: var(--color-text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

/* ---- Header ---- */
.puzzle-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.puzzle-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: var(--color-bg-input);
  color: var(--color-text-primary);
}

/* ---- Canvas ---- */
.puzzle-canvas {
  position: relative;
  width: 300px;
  height: 160px;
  margin: 0 auto;
  background: #e8ecf2;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.3s;
}

.puzzle-canvas.is-dragging {
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08), 0 0 0 3px rgba(66, 133, 244, 0.12);
}

.puzzle-canvas.is-verifying {
  opacity: 0.7;
}

.loading-canvas {
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-shimmer {
  width: 60%;
  height: 6px;
  background: linear-gradient(90deg, #e0e5ec 25%, #f0f3f6 50%, #e0e5ec 75%);
  background-size: 200% 100%;
  border-radius: 3px;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.puzzle-bg-img {
  width: 100%;
  height: 100%;
  display: block;
}

.puzzle-slide-img {
  position: absolute;
  width: 50px;
  height: 40px;
  pointer-events: none;
  border-radius: 3px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25), 0 0 0 2px rgba(255, 255, 255, 0.7);
  transition: box-shadow 0.2s;
  z-index: 3;
}

.puzzle-slide-img.is-dragging {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35), 0 0 0 3px rgba(255, 255, 255, 0.9);
}

/* ---- Slider ---- */
.slider-track {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}

.slider-bar {
  position: relative;
  width: 300px;
  height: 44px;
  margin: 0 auto;
  background: #f1f3f6;
  border-radius: 22px;
  overflow: visible;
  box-shadow: inset 0 0 0 1px #e2e6eb;
  transition: box-shadow 0.2s;
}

.slider-bar.dragging {
  box-shadow: inset 0 0 0 2px #4285f4;
}

.slider-bar.verifying {
  box-shadow: inset 0 0 0 1px #c4c9d0;
}

.slider-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, rgba(66, 133, 244, 0.06), rgba(66, 133, 244, 0.12));
  border-radius: 22px 0 0 22px;
}

.slider-thumb {
  position: absolute;
  top: 0;
  width: 50px;
  height: 44px;
  background: #fff;
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  touch-action: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1), 0 0 0 1px #d0d5db;
  transition: box-shadow 0.2s, transform 0.15s;
  z-index: 2;
}

.slider-thumb:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1), 0 0 0 2px #4285f4;
}

.slider-thumb.dragging {
  cursor: grabbing;
  box-shadow: 0 4px 18px rgba(66, 133, 244, 0.3), 0 0 0 2px #3367d6;
  transform: scale(1.05);
}

.slider-thumb.verifying {
  cursor: default;
  opacity: 0.7;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1), 0 0 0 1px #c4c9d0;
}

.thumb-arrow {
  color: #4285f4;
  transition: color 0.2s;
}

.slider-thumb.dragging .thumb-arrow {
  color: #3367d6;
}

.thumb-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e2e6eb;
  border-top-color: #4285f4;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.slider-hint {
  font-size: 11px;
  color: var(--color-text-muted);
  text-align: center;
  letter-spacing: 0.02em;
}

.puzzle-container {
  display: flex;
  flex-direction: column;
}
</style>
