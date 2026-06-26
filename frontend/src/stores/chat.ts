import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sendStreamRequest } from '@/services/request'
import { useUiStore } from '@/stores/ui'
import type { ChatMessage, TraceEntry } from '@/types/chat'

export type { ChatMessage, TraceEntry }

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const threadId = ref<string | null>(null)
  const traceEnabled = ref(false)
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
    let traceIdCounter = 0

    if (traceEnabled.value) {
      const idx = messages.value.findIndex((m) => m.id === assistantId)
      if (idx !== -1) {
        messages.value[idx] = { ...messages.value[idx], traces: [] }
      }
    }

    try {
      await sendStreamRequest(text.trim(), {
        threadId: threadId.value,
        traceEnabled: traceEnabled.value,
        onToken(token: string) {
          const idx = messages.value.findIndex((m) => m.id === assistantId)
          if (idx !== -1) {
            messages.value[idx] = {
              ...messages.value[idx],
              content: messages.value[idx].content + token,
            }
          }
        },
        onReasoning(token: string) {
          const idx = messages.value.findIndex((m) => m.id === assistantId)
          if (idx !== -1) {
            const msg = messages.value[idx]
            messages.value[idx] = { ...msg, reasoning: (msg.reasoning || '') + token }
          }
        },
        onTrace(entry: Omit<TraceEntry, 'id'>) {
          const idx = messages.value.findIndex((m) => m.id === assistantId)
          if (idx !== -1 && messages.value[idx].traces) {
            const traces = [...messages.value[idx].traces!, { ...entry, id: ++traceIdCounter }]
            messages.value[idx] = { ...messages.value[idx], traces }
          }
        },
        onThreadId(id: string) {
          threadId.value = id
        },
        onDone() {
          const idx = messages.value.findIndex((m) => m.id === assistantId)
          if (idx !== -1) {
            messages.value[idx] = { ...messages.value[idx], streaming: false }
          }
          loading.value = false

          const uiStore = useUiStore()
          uiStore.activeThreadId = threadId.value
          uiStore.fetchHistories()
        },
        onError(err: Error) {
          const idx = messages.value.findIndex((m) => m.id === assistantId)
          if (idx !== -1) {
            const msg = messages.value[idx]
            const sep = msg.content ? '\n\n' : ''
            messages.value[idx] = {
              ...msg,
              content: msg.content + `${sep}${err.message}`,
              streaming: false,
            }
          }
          loading.value = false
        },
      })
    } catch (err) {
      const idx = messages.value.findIndex((m) => m.id === assistantId)
      if (idx !== -1) {
        const msg = messages.value[idx]
        const sep = msg.content ? '\n\n' : ''
        messages.value[idx] = {
          ...msg,
          content: msg.content + `${sep}抱歉，网络连接失败，请检查网络后重试。`,
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
          streaming: false,
        }))
      nextId = messages.value.length + 1
    } catch {}

    loading.value = false
  }

  return { messages, loading, threadId, traceEnabled, sendMessage, clearMessages, loadConversation }
})
