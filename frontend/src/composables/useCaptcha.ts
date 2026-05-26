import { storeToRefs } from 'pinia'
import { useCaptchaStore } from '@/stores/captcha'
import type { PendingAction } from '@/types/components'

export function useCaptcha() {
  const captchaStore = useCaptchaStore()
  const { modalVisible, captchaType, pendingAction } = storeToRefs(captchaStore)

  function requestCaptcha(action: PendingAction) {
    captchaStore.showCaptcha(action)
  }

  function onCaptchaVerified(ticket: string, randstr: string) {
    captchaStore.onCaptchaSuccess({ ticket, randstr })
  }

  function closeCaptcha() {
    captchaStore.hideCaptcha()
  }

  return {
    modalVisible,
    captchaType,
    pendingAction,
    requestCaptcha,
    onCaptchaVerified,
    closeCaptcha,
  }
}
