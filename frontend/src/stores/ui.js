import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)
  const rightPanelCollapsed = ref(false)
  const plusMenuOpen = ref(false)
  const searchQuery = ref('')
  const selectedModel = ref('DeepSeek V4')
  const histories = ref([
    { id: 1, title: '关于 AI 的发展趋势' },
    { id: 2, title: 'Python 代码优化建议' },
    { id: 3, title: '旅行规划方案' },
    { id: 4, title: '数据可视化思路' },
    { id: 5, title: '产品需求分析' },
  ])
  const activeHistoryId = ref(1)

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

  function deleteHistory(id) {
    histories.value = histories.value.filter(h => h.id !== id)
    if (activeHistoryId.value === id) {
      activeHistoryId.value = null
    }
  }

  function newConversation() {
    activeHistoryId.value = null
    plusMenuOpen.value = false
  }

  return {
    sidebarCollapsed,
    rightPanelCollapsed,
    plusMenuOpen,
    searchQuery,
    selectedModel,
    histories,
    activeHistoryId,
    toggleSidebar,
    toggleRightPanel,
    togglePlusMenu,
    closePlusMenu,
    deleteHistory,
    newConversation,
  }
})