import { ref } from 'vue'

export function useAgreement() {
  const checked = ref(false)
  const shake = ref(false)

  function validate(): boolean {
    if (!checked.value) {
      shake.value = true
      setTimeout(() => {
        shake.value = false
      }, 2000)
      return false
    }
    return true
  }

  function showAgreement(type: 'user' | 'privacy') {
    // 由调用方组件通过 ElMessageBox 或自定义 Modal 展示协议全文
    // 返回用于对接 UI 层的信号
    return type
  }

  return { checked, shake, validate, showAgreement }
}
