import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useCountdown } from '@/composables/useCountdown'

describe('useCountdown', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('start sets countdown to initial value', () => {
    const { countdown, start } = useCountdown()
    start(60)
    expect(countdown.value).toBe(60)
  })

  it('countdown decrements every second', () => {
    const { countdown, start } = useCountdown()
    start(60)

    vi.advanceTimersByTime(1000)
    expect(countdown.value).toBe(59)

    vi.advanceTimersByTime(3000)
    expect(countdown.value).toBe(56)
  })

  it('isActive is false when countdown is 0', () => {
    const { countdown, isActive, start } = useCountdown()
    expect(isActive.value).toBe(false)

    start(60)
    expect(isActive.value).toBe(true)

    vi.advanceTimersByTime(60000)
    expect(isActive.value).toBe(false)
    expect(countdown.value).toBe(0)
  })

  it('stop clears countdown', () => {
    const { countdown, start, stop } = useCountdown()
    start(60)
    stop()
    expect(countdown.value).toBe(0)
  })

  it('countdown does not go below 0', () => {
    const { countdown, start } = useCountdown()
    start(2)
    vi.advanceTimersByTime(5000)
    expect(countdown.value).toBe(0)
  })
})
