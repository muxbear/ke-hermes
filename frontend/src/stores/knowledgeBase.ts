import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  KB,
  KBDoc,
  IndexConfig,
  DocType,
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

  // 搜索
  const searchQuery = ref('')

  // 索引动画定时器
  let indexTimer: ReturnType<typeof setInterval> | null = null

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

  const stats = computed(() => {
    const totalDocs = kbs.value.reduce((s, k) => s + k.docs, 0)
    const totalChunks = kbs.value.reduce((s, k) => s + k.chunks, 0)
    const totalEntities = kbs.value.reduce((s, k) => s + k.entities, 0)
    const indexing = kbs.value.filter((k) => k.status === 'indexing').length
    return {
      totalKbs: kbs.value.length,
      totalDocs,
      totalChunks,
      totalEntities,
      indexing,
    }
  })

  // ─── Actions ───────────────────────────────────────────────────────────

  async function fetchKbs() {
    loading.value = true
    error.value = null
    try {
      kbs.value = await kbApi.fetchKnowledgeBases()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载知识库失败'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function selectKb(id: string) {
    const kb = await kbApi.fetchKnowledgeBase(id)
    if (kb) {
      selectedKb.value = kb
      selectedDoc.value = null
      startIndexAnimation()
    }
  }

  function clearSelection() {
    stopIndexAnimation()
    selectedKb.value = null
    selectedDoc.value = null
  }

  async function createKb(data: CreateKBRequest) {
    loading.value = true
    try {
      const kb = await kbApi.createKnowledgeBase(data)
      kbs.value.unshift(kb)
      selectedKb.value = kb
      return kb
    } finally {
      loading.value = false
    }
  }

  async function updateKb(id: string, patch: Partial<KB>) {
    const updated = await kbApi.updateKnowledgeBase(id, patch)
    if (updated) {
      const idx = kbs.value.findIndex((k) => k.id === id)
      if (idx !== -1) kbs.value[idx] = updated
      if (selectedKb.value?.id === id) selectedKb.value = updated
    }
  }

  async function deleteKb(id: string) {
    await kbApi.deleteKnowledgeBase(id)
    kbs.value = kbs.value.filter((k) => k.id !== id)
    if (selectedKb.value?.id === id) clearSelection()
  }

  async function uploadDocs(
    kbId: string,
    files: { name: string; type: DocType; size: string }[],
  ) {
    const newDocs = await kbApi.uploadDocuments(kbId, files)
    if (newDocs && selectedKb.value && selectedKb.value.id === kbId) {
      selectedKb.value = {
        ...selectedKb.value,
        documents: [...newDocs, ...selectedKb.value.documents],
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
    await kbApi.retryDocument(kbId, docId)
    if (selectedKb.value && selectedKb.value.id === kbId) {
      selectedKb.value = {
        ...selectedKb.value,
        documents: selectedKb.value.documents.map((d) =>
          d.id === docId
            ? { ...d, status: 'parsing' as const, progress: 5 }
            : d,
        ),
      }
    }
  }

  async function searchKb(
    kbId: string,
    query: string,
    mode: SearchMode,
  ): Promise<SearchResult[]> {
    return kbApi.searchKnowledgeBase(kbId, query, mode)
  }

  // ─── 索引动画 ──────────────────────────────────────────────────────────

  function startIndexAnimation() {
    stopIndexAnimation()
    indexTimer = setInterval(() => {
      if (!selectedKb.value) return
      selectedKb.value = {
        ...selectedKb.value,
        documents: selectedKb.value.documents.map((d) => {
          if (
            d.status === 'failed' ||
            d.status === 'indexed' ||
            d.status === 'queued'
          )
            return d
          const next = Math.min(100, d.progress + Math.random() * 5)
          let newStatus = d.status
          if (next >= 100) newStatus = 'indexed'
          else if (next < 12) newStatus = 'parsing'
          else if (next < 30) newStatus = 'chunking'
          else if (next < 50) newStatus = 'embedding'
          else if (next < 65) newStatus = 'bm25'
          else if (next < 85) newStatus = 'extracting'
          return { ...d, progress: next, status: newStatus }
        }),
      }
    }, 1200)
  }

  function stopIndexAnimation() {
    if (indexTimer) {
      clearInterval(indexTimer)
      indexTimer = null
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
    // getters
    filteredKbs,
    stats,
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
    searchKb,
    startIndexAnimation,
    stopIndexAnimation,
  }
})
