import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Tool, ToolCreateRequest, ToolCategory, ToolSource, ToolStatus } from '@/types/tool'
import * as toolApi from '@/services/toolApi'

export const useToolStore = defineStore('tool', () => {
  const tools = ref<Tool[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const page = ref(1)
  const pageSize = ref(100)

  // -- Getters --
  const builtinTools = computed(() => tools.value.filter((t) => t.source === 'builtin'))
  const thirdPartyTools = computed(() => tools.value.filter((t) => t.source === 'third-party'))
  const enabledTools = computed(() => tools.value.filter((t) => t.status === 'enabled'))
  const disabledTools = computed(() => tools.value.filter((t) => t.status === 'disabled'))
  const unavailableTools = computed(() => tools.value.filter((t) => t.status === 'unavailable'))

  const categoryStats = computed(() => {
    const map: Record<string, { total: number; enabled: number; disabled: number }> = {}
    for (const t of tools.value) {
      if (!map[t.category]) map[t.category] = { total: 0, enabled: 0, disabled: 0 }
      map[t.category].total++
      if (t.status === 'enabled') map[t.category].enabled++
      else if (t.status === 'disabled') map[t.category].disabled++
    }
    return map
  })

  const sourceCategoryCounts = computed(() => {
    const map: Partial<Record<ToolCategory, number>> = {}
    for (const t of tools.value) {
      map[t.category] = (map[t.category] ?? 0) + 1
    }
    return map
  })

  // -- Actions --
  async function fetchTools(params?: {
    source?: string
    category?: string
    status?: string
    keyword?: string
  }) {
    loading.value = true
    error.value = null
    try {
      const res = await toolApi.fetchTools({ ...params, page: 1, page_size: 100 })
      tools.value = res.items
      total.value = res.total
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : '加载工具列表失败'
    } finally {
      loading.value = false
    }
  }

  async function addTool(data: ToolCreateRequest): Promise<Tool> {
    const tool = await toolApi.createTool(data)
    tools.value.unshift(tool)
    total.value++
    return tool
  }

  async function editTool(id: string, data: Partial<ToolCreateRequest>): Promise<Tool> {
    const updated = await toolApi.updateTool(id, data)
    const idx = tools.value.findIndex((t) => t.id === id)
    if (idx !== -1) tools.value[idx] = updated
    return updated
  }

  async function removeTool(id: string) {
    await toolApi.deleteTool(id)
    tools.value = tools.value.filter((t) => t.id !== id)
    total.value--
  }

  async function toggleToolEnabled(id: string, enabled: boolean) {
    const tool = tools.value.find((t) => t.id === id)
    if (tool) {
      const previous = tool.status
      tool.status = enabled ? 'enabled' : 'disabled'
      try {
        await toolApi.toggleTool(id, enabled)
      } catch {
        tool.status = previous
        throw new Error('切换失败')
      }
    }
  }

  return {
    tools, total, loading, error, page, pageSize,
    builtinTools, thirdPartyTools, enabledTools, disabledTools, unavailableTools,
    categoryStats, sourceCategoryCounts,
    fetchTools, addTool, editTool, removeTool, toggleToolEnabled,
  }
})
