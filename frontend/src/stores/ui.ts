import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchConversations, deleteConversation as deleteConversationApi } from '@/services/conversationApi'

export interface HistoryItem {
  thread_id: string
  title: string
}

export const useUiStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)
  const rightPanelCollapsed = ref(false)
  const plusMenuOpen = ref(false)
  const searchQuery = ref('')
  const selectedModel = ref('DeepSeek V4')
  const histories = ref<HistoryItem[]>([])
  const activeThreadId = ref<string | null>(null)

  async function fetchHistories() {
    try {
      const data = await fetchConversations()
      histories.value = data.map((c) => (
        {
          thread_id: c.thread_id,
          title: c.title,
        }
      ))
    } catch {
      // 静默失败, 列表保持现状
    }
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toggleRightPanel() {
    rightPanelCollapsed.value = !rightPanelCollapsed.value
  }

  function togglePlusMenu() {
    plusMenuOpen.value = !plusMenuOpen.value
  }

  function closePlusMenu() {
    plusMenuOpen.value = false
  }

  async function deleteHistory(thread_id: string) {
    try {
      await deleteConversationApi(thread_id)
      histories.value = histories.value.filter((h) => h.thread_id != thread_id)
      if (activeThreadId.value == thread_id) {
        activeThreadId.value = null
      }
    } catch {
      // 静默失败
    }
  }

  function newConversation() {
    activeThreadId.value = null
    plusMenuOpen.value = false
  }

  return {
      sidebarCollapsed,
      rightPanelCollapsed,
      plusMenuOpen,
      searchQuery,
      selectedModel,
      histories,
      activeThreadId,
      fetchHistories,
      deleteHistory,
      toggleSidebar,
      toggleRightPanel,
      togglePlusMenu,
      closePlusMenu,
      newConversation,
  }
})
