import { ref, computed, onUnmounted } from 'vue'

export function useCountdown() {
  const countdown = ref(0)
  const isActive = computed(() => countdown.value > 0)

  let timer: ReturnType<typeof setInterval> | null = null

  function start(seconds = 60) {
    stop()
    countdown.value = seconds
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        stop()
      }
    }, 1000)
  }

  function stop() {
    countdown.value = 0
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  onUnmounted(() => {
    stop()
  })

  return { countdown, isActive, start, stop }
}
