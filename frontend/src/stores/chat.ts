import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sendStreamRequest } from '@/services/request'

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  streaming: boolean
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const threadId = ref<string | null>(null)
  let nextId = 1

  function addMessage(role: 'user' | 'assistant', content = '', streaming = false): ChatMessage {
    const msg: ChatMessage = { id: nextId++, role, content, streaming }
    messages.value.push(msg)
    return msg
  }

  async function sendMessage(text: string) {
    if (loading.value || !text.trim()) return

    loading.value = true
    addMessage('user', text.trim())
    const assistantId = addMessage('assistant', '', true).id

    try {
      await sendStreamRequest(text.trim(), {
        threadId: threadId.value,
        onToken(token: string) {
          // 通过响应式数组修改，确保 Vue 跟踪变化
          const idx = messages.value.findIndex(m => m.id === assistantId)
          if (idx !== -1) {
            messages.value[idx] = { ...messages.value[idx], content: messages.value[idx].content + token }
          }
        },
        onThreadId(id: string) {
          threadId.value = id
        },
        onDone() {
          const idx = messages.value.findIndex(m => m.id === assistantId)
          if (idx !== -1) {
            messages.value[idx] = { ...messages.value[idx], streaming: false }
          }
          loading.value = false
        },
        onError(err: Error) {
          const idx = messages.value.findIndex(m => m.id === assistantId)
          if (idx !== -1) {
            messages.value[idx] = {
              ...messages.value[idx],
              content: messages.value[idx].content + `\n\n[Error: ${err.message}]`,
              streaming: false,
            }
          }
          loading.value = false
        },
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      const idx = messages.value.findIndex(m => m.id === assistantId)
      if (idx !== -1) {
        messages.value[idx] = {
          ...messages.value[idx],
          content: messages.value[idx].content + `\n\n[Connection failed: ${message}]`,
          streaming: false,
        }
      }
      loading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    loading.value = false
    threadId.value = null
  }

  return { messages, loading, threadId, sendMessage, clearMessages }
})
