import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCaptchaStore } from '@/stores/captcha'

describe('captchaStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('modalVisible defaults to false', () => {
    const store = useCaptchaStore()
    expect(store.modalVisible).toBe(false)
  })

  it('showCaptcha shows modal and sets pendingAction', () => {
    const store = useCaptchaStore()
    store.showCaptcha({ type: 'send-sms' })
    expect(store.modalVisible).toBe(true)
    expect(store.pendingAction?.type).toBe('send-sms')
  })

  it('hideCaptcha closes modal and clears pendingAction', () => {
    const store = useCaptchaStore()
    store.showCaptcha({ type: 'login' })
    store.hideCaptcha()
    expect(store.modalVisible).toBe(false)
    expect(store.pendingAction).toBeNull()
  })

  it('canSendSms is true when countdown is 0 and daily < 5', () => {
    const store = useCaptchaStore()
    expect(store.canSendSms).toBe(true)
  })

  it('startSmsCountdown increments daily count', () => {
    const store = useCaptchaStore()
    store.startSmsCountdown(60)
    expect(store.dailySmsCount).toBe(1)
    expect(store.smsCountdown).toBeGreaterThan(0)
  })

  it('resetSmsCount clears countdown', () => {
    const store = useCaptchaStore()
    store.startSmsCountdown(60)
    store.resetSmsCount()
    expect(store.smsCountdown).toBe(0)
  })
})
