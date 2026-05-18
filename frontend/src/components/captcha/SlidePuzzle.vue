<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import { captchaApi } from '@/services/captchaApi'
import type { CaptchaResult } from '@/types/components'

const emit = defineEmits<{
  success: [result: CaptchaResult]
  fail: []
}>()

type PuzzleStatus = 'idle' | 'dragging' | 'verifying' | 'fail'

const status = ref<PuzzleStatus>('idle')
const bgImage = ref('')
const slideImage = ref('')
const sliderPosition = ref(0)
const track: number[] = []

async function fetchPuzzle() {
  try {
    status.value = 'idle'
    sliderPosition.value = 0
    track.length = 0
    const res = await captchaApi.getSlidePuzzle()
    bgImage.value = res.data.data.bgImage
    slideImage.value = res.data.data.slideImage
  } catch {
    status.value = 'fail'
  }
}

async function verify() {
  status.value = 'verifying'
  try {
    const res = await captchaApi.verifySlide({
      distance: sliderPosition.value,
      track: [...track],
    })
    if (res.data.data.success) {
      emit('success', {
        ticket: res.data.data.ticket || '',
        randstr: res.data.data.randstr || '',
      })
    } else {
      status.value = 'fail'
      emit('fail')
    }
  } catch {
    status.value = 'fail'
    emit('fail')
  }
}

function onSliderChange(value: number) {
  sliderPosition.value = value
}

function onDragEnd() {
  if (sliderPosition.value > 0) {
    verify()
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
    <div v-if="status === 'fail'" class="puzzle-fail">
      <p>验证失败，请重试</p>
      <el-button @click="refresh">
        <RefreshCw :size="14" />
        刷新
      </el-button>
    </div>
    <div v-else class="puzzle-container">
      <div class="puzzle-bg">
        <img v-if="bgImage" :src="bgImage" alt="" />
      </div>
      <div class="puzzle-slider">
        <el-slider
          :model-value="sliderPosition"
          :max="300"
          :disabled="status === 'verifying'"
          @input="onSliderChange"
          @change="onDragEnd"
        />
        <span class="slider-hint">
          {{ status === 'verifying' ? '验证中...' : '向右拖动滑块完成拼图' }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-puzzle {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.puzzle-fail {
  text-align: center;
  color: var(--color-text-error);
}

.puzzle-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.puzzle-bg {
  width: 100%;
  aspect-ratio: 4 / 1;
  background: var(--color-bg-input);
  border-radius: var(--radius-input);
  overflow: hidden;
}

.puzzle-bg img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.puzzle-slider {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slider-hint {
  font-size: var(--font-size-agreement);
  color: var(--color-text-muted);
  text-align: center;
}
</style>
