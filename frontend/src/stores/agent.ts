import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Agent, ConfigType } from '@/types/agent'
import * as agentApi from '@/services/agentApi'

export const useAgentStore = defineStore('agent', () => {
  /* ---------- state ---------- */
  const agents = ref<Agent[]>([])
  const selectedAgentId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const searchQuery = ref('')
  const expandedIds = ref<Set<string>>(new Set(['main-agent']))

  /* ---------- computed ---------- */
  const selectedAgent = computed(() =>
    agents.value.find((a) => a.id === selectedAgentId.value) ?? null,
  )

  const mainAgent = computed(() => agents.value.find((a) => a.type === 'main') ?? null)

  const subAgents = computed(() => agents.value.filter((a) => a.type === 'sub'))

  const filteredAgents = computed(() => {
    if (!searchQuery.value) {
      // 无搜索时只返回主代理（树根）
      return agents.value.filter((a) => a.type === 'main')
    }
    // 搜索时展平，返回所有匹配项
    const q = searchQuery.value.toLowerCase()
    return agents.value.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        (a.description ?? '').toLowerCase().includes(q),
    )
  })

  const stats = computed(() => ({
    total: agents.value.length,
    active: agents.value.filter((a) => a.status === 'active').length,
    inactive: agents.value.filter((a) => a.status === 'inactive').length,
    error: agents.value.filter((a) => a.status === 'error').length,
  }))

  /* ---------- actions ---------- */
  async function fetchAgents() {
    loading.value = true
    error.value = null
    try {
      agents.value = await agentApi.fetchAgents()
      // 默认选中主代理
      if (!selectedAgentId.value && agents.value.length > 0) {
        selectedAgentId.value = agents.value.find((a) => a.type === 'main')?.id ?? agents.value[0].id
      }
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : '加载代理列表失败'
    } finally {
      loading.value = false
    }
  }

  function selectAgent(id: string) {
    selectedAgentId.value = id
  }

  function toggleExpand(id: string) {
    const s = new Set(expandedIds.value)
    if (s.has(id)) s.delete(id)
    else s.add(id)
    expandedIds.value = s
  }

  function expandAll() {
    const ids = agents.value.filter((a) => a.subAgents && a.subAgents.length > 0).map((a) => a.id)
    expandedIds.value = new Set(ids)
  }

  function collapseAll() {
    expandedIds.value = new Set()
  }

  async function toggleStatus(id: string) {
    try {
      const updated = await agentApi.toggleAgentStatus(id)
      const idx = agents.value.findIndex((a) => a.id === id)
      if (idx !== -1) agents.value[idx] = updated
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('切换状态失败')
    }
  }

  async function cloneAgent(id: string) {
    try {
      const cloned = await agentApi.cloneAgent(id)
      agents.value.push(cloned)
      // 刷新主代理（subAgents 可能变了）
      const updatedMain = await agentApi.fetchAgents()
      agents.value = updatedMain
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('克隆失败')
    }
  }

  async function deleteAgent(id: string) {
    try {
      await agentApi.deleteAgent(id)
      agents.value = agents.value.filter((a) => a.id !== id)
      // 从主代理 subAgents 中移除
      const main = agents.value.find((a) => a.type === 'main')
      if (main && main.subAgents) {
        main.subAgents = main.subAgents.filter((sid) => sid !== id)
      }
      // 如果删除的是当前选中项，切换到主代理
      if (selectedAgentId.value === id && main) {
        selectedAgentId.value = main.id
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('删除失败')
    }
  }

  async function addConfig(type: ConfigType, value: string) {
    const targetId = selectedAgentId.value
    if (!targetId) return

    try {
      const updated = await agentApi.addConfig(targetId, type, value)
      // 刷新整个列表以保持数据一致性
      agents.value = await agentApi.fetchAgents()
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('添加配置失败')
    }
  }

  async function removeConfig(type: ConfigType, value: string) {
    const targetId = selectedAgentId.value
    if (!targetId) return

    try {
      const updated = await agentApi.removeConfig(targetId, type, value)
      agents.value = await agentApi.fetchAgents()
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('移除配置失败')
    }
  }

  async function createSubAgent(name: string, description?: string) {
    try {
      const newAgent = await agentApi.createAgent({ name, description })
      agents.value = await agentApi.fetchAgents()
      // 自动展开主代理并选中新创建的子代理
      expandedIds.value = new Set([...expandedIds.value, 'main-agent'])
      selectedAgentId.value = newAgent.id
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('创建子代理失败')
    }
  }

  return {
    agents,
    selectedAgentId,
    loading,
    error,
    searchQuery,
    expandedIds,
    selectedAgent,
    mainAgent,
    subAgents,
    filteredAgents,
    stats,
    fetchAgents,
    selectAgent,
    toggleExpand,
    expandAll,
    collapseAll,
    toggleStatus,
    cloneAgent,
    deleteAgent,
    addConfig,
    removeConfig,
    createSubAgent,
  }
})
