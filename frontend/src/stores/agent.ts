import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Agent, AgentFileContent, AgentUpdateRequest, ConfigType, CronJobBrief, MemoryScope, SkillBrief } from '@/types/agent'
import * as agentApi from '@/services/agentApi'

export const useAgentStore = defineStore('agent', () => {
  /* ---------- state ---------- */
  const agents = ref<Agent[]>([])
  const selectedAgentId = ref<string | null>(null)
  const cronJobs = ref<CronJobBrief[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const searchQuery = ref('')
  const expandedIds = ref<Set<string>>(new Set())

  // File content state
  const currentFileContent = ref<AgentFileContent | null>(null)
  const fileLoading = ref(false)
  const selectedFilename = ref<string | null>(null)
  const fileDescriptions = ref<Record<string, string>>({})

  /* ---------- computed ---------- */
  const selectedAgent = computed(() =>
    agents.value.find((a) => a.id === selectedAgentId.value) ?? null,
  )

  const mainAgent = computed(() => agents.value.find((a) => a.type === 'main') ?? null)

  const subAgents = computed(() => agents.value.filter((a) => a.type === 'sub'))

  const filteredAgents = computed(() => {
    if (!searchQuery.value) {
      // 无搜索时只返回主智能体（树根）
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
      // 默认选中主智能体
      if (!selectedAgentId.value && agents.value.length > 0) {
        selectedAgentId.value = agents.value.find((a) => a.type === 'main')?.id ?? agents.value[0].id
      }
      // 默认展开主智能体（使其子智能体可见）
      const mainId = agents.value.find((a) => a.type === 'main')?.id
      if (mainId && !expandedIds.value.has(mainId)) {
        expandedIds.value = new Set([...expandedIds.value, mainId])
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

  async function fetchCronJobs(agentId: string) {
    try {
      cronJobs.value = await agentApi.fetchAgentCronJobs(agentId)
    } catch {
      cronJobs.value = []
    }
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
      // 刷新主智能体（subAgents 可能变了）
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
      // 从主智能体 subAgents 中移除
      const main = agents.value.find((a) => a.type === 'main')
      if (main && main.subAgents) {
        main.subAgents = main.subAgents.filter((sid) => sid !== id)
      }
      // 如果删除的是当前选中项，切换到主智能体
      if (selectedAgentId.value === id && main) {
        selectedAgentId.value = main.id
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('删除失败')
    }
  }

  async function addConfig(type: ConfigType, value: string, description: string = '', scope?: MemoryScope) {
    const targetId = selectedAgentId.value
    if (!targetId) throw new Error('未选中代理')

    try {
      await agentApi.addConfig(targetId, type, value, description, scope)
      // 刷新整个列表以保持数据一致性
      agents.value = await agentApi.fetchAgents()
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('添加配置失败')
    }
  }

  async function updateConfig(type: ConfigType, value: string, newValue: string = '', description: string = '', scope?: MemoryScope) {
    const targetId = selectedAgentId.value
    if (!targetId) throw new Error('未选中代理')

    try {
      await agentApi.updateConfig(targetId, type, value, newValue, description, scope)
      agents.value = await agentApi.fetchAgents()
      // If file was renamed, update selectedFilename
      if (type === 'file' && newValue && newValue !== value && selectedFilename.value === value) {
        selectedFilename.value = newValue
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('更新配置失败')
    }
  }

  async function removeConfig(type: ConfigType, value: string, scope?: MemoryScope) {
    const targetId = selectedAgentId.value
    if (!targetId) throw new Error('未选中代理')

    try {
      await agentApi.removeConfig(targetId, type, value, scope)
      agents.value = await agentApi.fetchAgents()
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('移除配置失败')
    }
  }

  async function addSkill(skillId: string) {
    const targetId = selectedAgentId.value
    if (!targetId) throw new Error('未选中代理')

    try {
      const updatedSkills = await agentApi.addAgentSkill(targetId, skillId)
      // Patch skills in-place
      const agent = agents.value.find((a) => a.id === targetId)
      if (agent) {
        agent.skills = updatedSkills
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('添加技能失败')
    }
  }

  async function removeSkill(skillId: string) {
    const targetId = selectedAgentId.value
    if (!targetId) throw new Error('未选中代理')

    try {
      await agentApi.removeAgentSkill(targetId, skillId)
      const agent = agents.value.find((a) => a.id === targetId)
      if (agent) {
        agent.skills = agent.skills.filter((s: SkillBrief) => s.id !== skillId)
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('移除技能失败')
    }
  }

  async function createSubAgent(name: string, description?: string, systemPrompt?: string, providerId?: string, modelId?: string) {
    const main = mainAgent.value
    if (!main) throw new Error('主智能体不存在，无法创建子智能体')
    try {
      const newAgent = await agentApi.createAgent({ name, description, systemPrompt, parentId: main.id, providerId, modelId })
      agents.value = await agentApi.fetchAgents()
      // 自动展开主智能体并选中新创建的子智能体
      expandedIds.value = new Set([...expandedIds.value, main.id])
      selectedAgentId.value = newAgent.id
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('创建子智能体失败')
    }
  }

  async function updateAgent(id: string, data: AgentUpdateRequest) {
    try {
      const updated = await agentApi.updateAgent(id, data)
      const idx = agents.value.findIndex((a) => a.id === id)
      if (idx !== -1) agents.value[idx] = updated
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('更新智能体失败')
    }
  }

  /* ---------- file content actions ---------- */
  async function fetchFileContent(agentId: string, filename: string, scope?: MemoryScope) {
    fileLoading.value = true
    selectedFilename.value = filename
    try {
      currentFileContent.value = await agentApi.fetchFileContent(agentId, filename, scope)
    } catch (err: unknown) {
      currentFileContent.value = null
      throw err instanceof Error ? err : new Error('获取文件内容失败')
    } finally {
      fileLoading.value = false
    }
  }

  async function saveFileContent(agentId: string, filename: string, content: string, scope?: MemoryScope) {
    try {
      currentFileContent.value = await agentApi.saveFileContent(agentId, filename, content, scope)
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('保存文件内容失败')
    }
  }

  function clearFileContent() {
    currentFileContent.value = null
    selectedFilename.value = null
  }

  async function fetchFileDescriptionsAction(agentId: string) {
    try {
      fileDescriptions.value = await agentApi.fetchFileDescriptions(agentId)
    } catch {
      fileDescriptions.value = {}
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
    addSkill,
    removeSkill,
    createSubAgent,
    updateAgent,
    updateConfig,
    // file content
    currentFileContent,
    fileLoading,
    selectedFilename,
    fetchFileContent,
    saveFileContent,
    clearFileContent,
    fileDescriptions,
    fetchFileDescriptions: fetchFileDescriptionsAction,
    cronJobs,
    fetchCronJobs,
  }
})
