import { useCaptchaStore } from '@/stores/captcha'
import type { PendingAction } from '@/types/components'

export function useCaptcha() {
  const captchaStore = useCaptchaStore()

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
    modalVisible: captchaStore.modalVisible,
    captchaType: captchaStore.captchaType,
    pendingAction: captchaStore.pendingAction,
    requestCaptcha,
    onCaptchaVerified,
    closeCaptcha,
  }
}
