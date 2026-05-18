<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import { captchaApi } from '@/services/captchaApi'
import type { CaptchaResult } from '@/types/components'

const emit = defineEmits<{
  success: [result: CaptchaResult]
  fail: []
}>()

const imageUrl = ref('')
const captchaKey = ref('')
const inputCode = ref('')
const loading = ref(false)

async function fetchCaptcha() {
  try {
    const res = await captchaApi.getImageCaptcha()
    imageUrl.value = res.data.data.image
    captchaKey.value = res.data.data.key
  } catch {
    emit('fail')
  }
}

async function verify() {
  if (!inputCode.value) return
  loading.value = true
  try {
    const res = await captchaApi.verifyImageCaptcha({
      key: captchaKey.value,
      code: inputCode.value,
    })
    if (res.data.data.success) {
      emit('success', { ticket: captchaKey.value, randstr: inputCode.value })
    } else {
      emit('fail')
      inputCode.value = ''
      fetchCaptcha()
    }
  } catch {
    emit('fail')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCaptcha()
})
</script>

<template>
  <div class="image-captcha">
    <div class="captcha-image" @click="fetchCaptcha">
      <img v-if="imageUrl" :src="imageUrl" alt="验证码" />
      <span v-else class="captcha-placeholder">加载中...</span>
      <span class="captcha-refresh-hint">点击刷新</span>
    </div>
    <div class="captcha-input-row">
      <el-input
        v-model="inputCode"
        placeholder="请输入验证码"
        maxlength="4"
        :disabled="loading"
        @keydown.enter="verify"
      />
      <el-button type="primary" :loading="loading" @click="verify">
        验证
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.image-captcha {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.captcha-image {
  position: relative;
  width: 100%;
  height: 60px;
  background: var(--color-bg-input);
  border-radius: var(--radius-input);
  overflow: hidden;
  cursor: pointer;
}

.captcha-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.captcha-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-muted);
  font-size: var(--font-size-agreement);
}

.captcha-refresh-hint {
  position: absolute;
  bottom: 4px;
  right: 8px;
  font-size: 10px;
  color: var(--color-text-muted);
  opacity: 0.6;
}

.captcha-input-row {
  display: flex;
  gap: 8px;
}
</style>
