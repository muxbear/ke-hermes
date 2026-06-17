import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  KB,
  KBDoc,
  DocType,
  IndexConfig,
  SearchResult,
  SearchMode,
  ViewMode,
  CreateKBRequest,
} from '@/types/knowledgeBase'
import * as kbApi from '@/services/knowledgeBaseApi'

export const useKnowledgeBaseStore = defineStore('knowledgeBase', () => {
  // ─── 列表状态 ──────────────────────────────────────────────────────────
  const kbs = ref<KB[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 当前选中知识库
  const selectedKb = ref<KB | null>(null)
  const selectedDoc = ref<KBDoc | null>(null)

  // 视图模式
  const viewMode = ref<ViewMode>('grid')

  // 搜索（本地过滤用）
  const searchQuery = ref('')

  // 统计信息
  const stats = ref({
    totalKbs: 0,
    totalDocs: 0,
    totalChunks: 0,
    totalEntities: 0,
    indexing: 0,
  })

  // 索引进度轮询定时器
  let indexPollTimer: ReturnType<typeof setInterval> | null = null

  // ─── 计算属性 ──────────────────────────────────────────────────────────

  const filteredKbs = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    if (!q) return kbs.value
    return kbs.value.filter(
      (k) =>
        k.name.toLowerCase().includes(q) ||
        k.description.toLowerCase().includes(q) ||
        k.tags.some((t) => t.toLowerCase().includes(q)),
    )
  })

  // ─── Actions ───────────────────────────────────────────────────────────

  async function fetchKbs() {
    loading.value = true
    error.value = null
    try {
      kbs.value = await kbApi.fetchKnowledgeBases()
      // 同时拉取统计信息
      const s = await kbApi.fetchStats()
      stats.value = {
        totalKbs: s.totalKbs,
        totalDocs: s.totalDocs,
        totalChunks: s.totalChunks,
        totalEntities: s.totalEntities,
        indexing: s.indexing,
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载知识库失败'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function selectKb(id: string) {
    loading.value = true
    try {
      const kb = await kbApi.fetchKnowledgeBase(id)
      if (kb) {
        const docData = await kbApi.fetchDocuments(id, { page_size: 100 })
        const graphData = await kbApi.fetchGraphData(id)

        selectedKb.value = {
          ...kb,
          documents: docData.items,
          entitiesData: graphData.entities.map((e) => ({
            ...e,
            x: 0,
            y: 0,
          })),
          relationsData: graphData.relations,
        }
        selectedDoc.value = null
        startIndexPolling()
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载知识库详情失败'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  function clearSelection() {
    stopIndexPolling()
    selectedKb.value = null
    selectedDoc.value = null
  }

  async function createKb(data: CreateKBRequest) {
    loading.value = true
    try {
      const kb = await kbApi.createKnowledgeBase(data)
      kbs.value.unshift(kb)
      // 新创建的知识库设置空数组避免组件访问 .slice/.filter 时崩溃
      selectedKb.value = { ...kb, documents: [], entitiesData: [], relationsData: [] }
      selectedDoc.value = null
      // 刷新统计
      const s = await kbApi.fetchStats()
      stats.value = {
        totalKbs: s.totalKbs,
        totalDocs: s.totalDocs,
        totalChunks: s.totalChunks,
        totalEntities: s.totalEntities,
        indexing: s.indexing,
      }
      return kb
    } finally {
      loading.value = false
    }
  }

  async function updateKb(id: string, patch: Partial<KB>) {
    const updated = await kbApi.updateKnowledgeBase(id, patch)
    const idx = kbs.value.findIndex((k) => k.id === id)
    if (idx !== -1) kbs.value[idx] = { ...kbs.value[idx], ...updated }
    if (selectedKb.value?.id === id) {
      selectedKb.value = { ...selectedKb.value, ...updated }
    }
  }

  async function deleteKb(id: string) {
    await kbApi.deleteKnowledgeBase(id)
    kbs.value = kbs.value.filter((k) => k.id !== id)
    if (selectedKb.value?.id === id) clearSelection()
    // 刷新统计
    const s = await kbApi.fetchStats()
    stats.value = {
      totalKbs: s.totalKbs,
      totalDocs: s.totalDocs,
      totalChunks: s.totalChunks,
      totalEntities: s.totalEntities,
      indexing: s.indexing,
    }
  }

  async function uploadDocs(kbId: string, files: File[]) {
    if (!files.length) return
    const newDocs = await kbApi.uploadDocuments(kbId, files)
    if (selectedKb.value && selectedKb.value.id === kbId) {
      selectedKb.value = {
        ...selectedKb.value,
        documents: [...newDocs, ...selectedKb.value.documents],
        docs: selectedKb.value.docs + newDocs.length,
      }
    }
  }

  async function deleteDoc(kbId: string, docId: string) {
    await kbApi.deleteDocument(kbId, docId)
    if (selectedKb.value && selectedKb.value.id === kbId) {
      selectedKb.value = {
        ...selectedKb.value,
        documents: selectedKb.value.documents.filter((d) => d.id !== docId),
      }
    }
    if (selectedDoc.value?.id === docId) selectedDoc.value = null
  }

  async function retryDoc(kbId: string, docId: string) {
    const updatedDoc = await kbApi.retryDocument(kbId, docId)
    if (selectedKb.value && selectedKb.value.id === kbId) {
      selectedKb.value = {
        ...selectedKb.value,
        documents: selectedKb.value.documents.map((d) =>
          d.id === docId ? updatedDoc : d,
        ),
      }
    }
  }

  async function reindexKb(kbId: string, config: IndexConfig) {
    const result = await kbApi.reindexKnowledgeBase(kbId, config)
    // Refresh KB detail to get updated status
    if (selectedKb.value && selectedKb.value.id === kbId) {
      selectedKb.value = {
        ...selectedKb.value,
        status: 'indexing',
        config,
      }
    }
    // Refresh stats
    const s = await kbApi.fetchStats()
    stats.value = {
      totalKbs: s.totalKbs,
      totalDocs: s.totalDocs,
      totalChunks: s.totalChunks,
      totalEntities: s.totalEntities,
      indexing: s.indexing,
    }
    return result
  }

  async function searchKb(
    kbId: string,
    query: string,
    mode: SearchMode,
  ): Promise<SearchResult[]> {
    return kbApi.searchKnowledgeBase(kbId, query, mode)
  }

  // ─── 索引进度轮询 ──────────────────────────────────────────────────────

  function startIndexPolling() {
    stopIndexPolling()
    indexPollTimer = setInterval(async () => {
      if (!selectedKb.value) return
      const kbId = selectedKb.value.id

      // 只对有索引中文档的知识库做轮询
      const hasActive = selectedKb.value.documents.some(
        (d) => d.status !== 'indexed' && d.status !== 'failed',
      )
      if (!hasActive) return

      try {
        // 重新拉取文档列表
        const docData = await kbApi.fetchDocuments(kbId, { page_size: 100 })
        if (selectedKb.value) {
          selectedKb.value = {
            ...selectedKb.value,
            documents: docData.items,
          }
        }
      } catch {
        // 轮询失败静默忽略
      }
    }, 5000)
  }

  function stopIndexPolling() {
    if (indexPollTimer) {
      clearInterval(indexPollTimer)
      indexPollTimer = null
    }
  }

  return {
    // state
    kbs,
    loading,
    error,
    selectedKb,
    selectedDoc,
    viewMode,
    searchQuery,
    stats,
    // getters
    filteredKbs,
    // actions
    fetchKbs,
    selectKb,
    clearSelection,
    createKb,
    updateKb,
    deleteKb,
    uploadDocs,
    deleteDoc,
    retryDoc,
    reindexKb,
    searchKb,
    startIndexPolling,
    stopIndexPolling,
  }
})
