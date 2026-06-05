import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Provider, AIModel, ModelType } from '@/types/model'
import * as api from '@/services/modelApi'

type RightTab = 'models' | 'usage'

export const useModelStore = defineStore('model', () => {
  /* ---------- state ---------- */
  const providers = ref<Provider[]>([])
  const selectedProviderId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const providerSearch = ref('')
  const modelSearch = ref('')
  const modelTypeFilter = ref<ModelType | 'all'>('all')
  const rightTab = ref<RightTab>('models')

  /* ---------- computed ---------- */
  const selectedProvider = computed<Provider | null>(() => {
    if (!selectedProviderId.value && providers.value.length > 0) return providers.value[0]
    return providers.value.find((p) => p.id === selectedProviderId.value) ?? providers.value[0] ?? null
  })

  const filteredProviders = computed(() =>
    providers.value.filter((p) =>
      !providerSearch.value || p.name.toLowerCase().includes(providerSearch.value.toLowerCase()),
    ),
  )

  const filteredModels = computed(() => {
    const p = selectedProvider.value
    if (!p) return []
    return p.models.filter((m) => {
      const q = modelSearch.value.toLowerCase()
      const matchSearch = !q || m.displayName.toLowerCase().includes(q) || m.name.toLowerCase().includes(q)
      const matchType = modelTypeFilter.value === 'all' || m.type === modelTypeFilter.value
      return matchSearch && matchType
    })
  })

  const totalModels = computed(() => providers.value.reduce((s, p) => s + p.models.length, 0))

  const typeCounts = computed(() => {
    const map: Partial<Record<ModelType, number>> = {}
    providers.value.forEach((p) => p.models.forEach((m) => { map[m.type] = (map[m.type] ?? 0) + 1 }))
    return map
  })

  const providerTypeCounts = computed(() => {
    const p = selectedProvider.value
    if (!p) return {}
    const map: Partial<Record<ModelType, number>> = {}
    p.models.forEach((m) => { map[m.type] = (map[m.type] ?? 0) + 1 })
    return map
  })

  const providerStats = computed(() => {
    const p = selectedProvider.value
    if (!p) return { total: 0, totalCalls: '0', inUse: 0, deprecated: 0 }
    return {
      total: p.models.length,
      totalCalls: p.models.reduce((s, m) => s + m.callCount, 0).toLocaleString(),
      inUse: p.models.filter((m) => m.usedByAgents.length > 0).length,
      deprecated: p.models.filter((m) => m.status === 'deprecated').length,
    }
  })

  /* ---------- actions ---------- */
  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      providers.value = await api.fetchProviders()
      if (!selectedProviderId.value && providers.value.length > 0) {
        selectedProviderId.value = providers.value[0].id
      }
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : '加载模型列表失败'
    } finally {
      loading.value = false
    }
  }

  function selectProvider(id: string) {
    selectedProviderId.value = id
    modelSearch.value = ''
    modelTypeFilter.value = 'all'
  }

  async function saveProvider(data: Provider) {
    const exists = providers.value.some((p) => p.id === data.id)
    try {
      if (exists) {
        await api.updateProvider(data.id, data)
      } else {
        await api.createProvider(data)
      }
      await fetchAll()
      selectedProviderId.value = data.id
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('保存提供商失败')
    }
  }

  async function deleteProvider(id: string) {
    try {
      await api.deleteProvider(id)
      providers.value = providers.value.filter((p) => p.id !== id)
      if (selectedProviderId.value === id) {
        selectedProviderId.value = providers.value[0]?.id ?? null
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('删除提供商失败')
    }
  }

  async function saveModel(providerId: string, data: AIModel) {
    const provider = providers.value.find((p) => p.id === providerId)
    const exists = provider?.models.some((m) => m.id === data.id)
    try {
      if (exists) {
        const updated = await api.updateModel(providerId, data.id, data)
        const pIdx = providers.value.findIndex((p) => p.id === providerId)
        if (pIdx >= 0) {
          const mIdx = providers.value[pIdx].models.findIndex((m) => m.id === updated.id)
          if (mIdx >= 0) providers.value[pIdx].models[mIdx] = updated
          else providers.value[pIdx].models.push(updated)
        }
      } else {
        const created = await api.createModel(providerId, data)
        const pIdx = providers.value.findIndex((p) => p.id === providerId)
        if (pIdx >= 0) providers.value[pIdx].models.push(created)
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('保存模型失败')
    }
  }

  async function deleteModel(providerId: string, modelId: string) {
    try {
      await api.deleteModel(providerId, modelId)
      const pIdx = providers.value.findIndex((p) => p.id === providerId)
      if (pIdx >= 0) {
        providers.value[pIdx].models = providers.value[pIdx].models.filter((m) => m.id !== modelId)
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('删除模型失败')
    }
  }

  async function cloneModel(providerId: string, modelId: string) {
    try {
      const cloned = await api.cloneModel(providerId, modelId)
      const pIdx = providers.value.findIndex((p) => p.id === providerId)
      if (pIdx >= 0) providers.value[pIdx].models.push(cloned)
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('克隆模型失败')
    }
  }

  async function toggleModelStatus(providerId: string, modelId: string) {
    try {
      const updated = await api.toggleModelStatus(providerId, modelId)
      const pIdx = providers.value.findIndex((p) => p.id === providerId)
      if (pIdx >= 0) {
        const mIdx = providers.value[pIdx].models.findIndex((m) => m.id === modelId)
        if (mIdx >= 0) providers.value[pIdx].models[mIdx] = updated
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('切换状态失败')
    }
  }

  function setRightTab(tab: RightTab) {
    rightTab.value = tab
  }

  return {
    providers, selectedProviderId, loading, error,
    providerSearch, modelSearch, modelTypeFilter, rightTab,
    selectedProvider, filteredProviders, filteredModels,
    totalModels, typeCounts, providerTypeCounts, providerStats,
    fetchAll, selectProvider, saveProvider, deleteProvider,
    saveModel, deleteModel, cloneModel, toggleModelStatus, setRightTab,
  }
})
