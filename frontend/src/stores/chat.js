import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sendStreamRequest } from '@/services/chatApi'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const loading = ref(false)
  let nextId = 1

  function addMessage(role, content = '', streaming = false) {
    messages.value.push({ id: nextId++, role, content, streaming })
    return messages.value[messages.value.length - 1]
  }

  async function sendMessage(text) {
    if (loading.value || !text.trim()) return

    loading.value = true
    addMessage('user', text.trim())
    const assistantMsg = addMessage('assistant', '', true)

    try {
      await sendStreamRequest(text.trim(), {
        onToken(token) {
          assistantMsg.content += token
        },
        onDone() {
          assistantMsg.streaming = false
          loading.value = false
        },
        onError(err) {
          assistantMsg.content += `\n\n[Error: ${err}]`
          assistantMsg.streaming = false
          loading.value = false
        }
      })
    } catch (err) {
      assistantMsg.content += `\n\n[Connection failed: ${err.message}]`
      assistantMsg.streaming = false
      loading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    loading.value = false
  }

  return { messages, loading, sendMessage, clearMessages }
})