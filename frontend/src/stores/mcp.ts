import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { McpTool } from '@/types/mcp'
import { fetchMcpTools, fetchMcpToolById, installMcpTool, uninstallMcpTool } from '@/services/mcpApi'

export const useMcpStore = defineStore('mcp', () => {
  const tools = ref<McpTool[]>([])
  const currentTool = ref<McpTool | null>(null)
  const loading = ref(false)
  const detailLoading = ref(false)
  const error = ref<string | null>(null)

  const installedTools = computed(() => tools.value.filter((t) => t.installed))
  const officialTools = computed(() => tools.value.filter((t) => t.official))

  async function fetchTools(params?: { category?: string; search?: string; sort?: string }) {
    loading.value = true
    error.value = null
    try {
      const res = await fetchMcpTools(params)
      tools.value = res.data
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载 MCP 工具列表失败'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function fetchToolById(id: string) {
    detailLoading.value = true
    error.value = null
    try {
      const res = await fetchMcpToolById(id)
      currentTool.value = res.data
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载 MCP 工具详情失败'
      error.value = msg
      currentTool.value = null
    } finally {
      detailLoading.value = false
    }
  }

  async function installTool(id: string) {
    error.value = null
    try {
      await installMcpTool({ mcp_id: id })
      const idx = tools.value.findIndex((t) => t.id === id)
      if (idx !== -1) tools.value[idx].installed = true
      if (currentTool.value?.id === id) currentTool.value.installed = true
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '安装失败'
      error.value = msg
      throw err
    }
  }

  async function uninstallTool(id: string) {
    error.value = null
    try {
      await uninstallMcpTool(id)
      const idx = tools.value.findIndex((t) => t.id === id)
      if (idx !== -1) tools.value[idx].installed = false
      if (currentTool.value?.id === id) currentTool.value.installed = false
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '卸载失败'
      error.value = msg
      throw err
    }
  }

  return {
    tools,
    currentTool,
    loading,
    detailLoading,
    error,
    installedTools,
    officialTools,
    fetchTools,
    fetchToolById,
    installTool,
    uninstallTool,
  }
})
