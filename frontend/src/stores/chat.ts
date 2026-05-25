import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sendStreamRequest } from '@/services/request'
import { useUiStore } from '@/stores/ui'

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

          const uiStore = useUiStore()
          uiStore.activeThreadId = threadId.value
          uiStore.fetchHistories()
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

  async function loadConversation(tid: string) {
    const { fetchConversationMessages } = await import('@/services/conversationApi')
    threadId.value = tid
    loading.value = true
    try {
      const detail = await fetchConversationMessages(tid)
      
      messages.value = detail.messages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .map((m, idx) => ({
          id: idx + 1,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          streaming: false
        }))
        nextId = messages.value.length + 1
    } catch {
    }

    loading.value = false
  }

  return { messages, loading, threadId, sendMessage, clearMessages, loadConversation }
})
