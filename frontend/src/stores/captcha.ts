import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CaptchaResult, PendingAction } from '@/types/components'

export const useCaptchaStore = defineStore('captcha', () => {
  // ---- State ----
  const modalVisible = ref(false)
  const captchaType = ref<'slide' | 'image'>('slide')
  const pendingAction = ref<PendingAction | null>(null)
  const smsCountdown = ref(0)
  const smsErrorCount = ref(0)
  const dailySmsCount = ref(0)

  // ---- Getters ----
  const canSendSms = computed(
    () => smsCountdown.value === 0 && dailySmsCount.value < 5,
  )

  let countdownTimer: ReturnType<typeof setInterval> | null = null

  // ---- Actions ----
  function showCaptcha(action: PendingAction) {
    pendingAction.value = action
    captchaType.value = 'slide'
    modalVisible.value = true
  }

  function hideCaptcha() {
    modalVisible.value = false
    pendingAction.value = null
  }

  function onCaptchaSuccess(result: CaptchaResult) {
    modalVisible.value = false
    // pendingAction 由调用方在验证通过后使用
    // result.ticket 和 result.randstr 供短信发送等后续操作
  }

  function startSmsCountdown(seconds = 60) {
    smsCountdown.value = seconds
    dailySmsCount.value++
    countdownTimer = setInterval(() => {
      smsCountdown.value--
      if (smsCountdown.value <= 0) {
        smsCountdown.value = 0
        if (countdownTimer) {
          clearInterval(countdownTimer)
          countdownTimer = null
        }
      }
    }, 1000)
  }

  function resetSmsCount() {
    smsCountdown.value = 0
    smsErrorCount.value = 0
    if (countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }

  return {
    modalVisible,
    captchaType,
    pendingAction,
    smsCountdown,
    smsErrorCount,
    dailySmsCount,
    canSendSms,
    showCaptcha,
    hideCaptcha,
    onCaptchaSuccess,
    startSmsCountdown,
    resetSmsCount,
  }
})
