// 知识库 API 服务
import instance from './request'
import type {
  KB,
  KBDoc,
  DocChunk,
  CreateKBRequest,
  SearchResult,
  IndexConfig,
} from '@/types/knowledgeBase'

// ─── 后端原始类型 ──────────────────────────────────────────────────────────

interface RawKB {
  id: string
  name: string
  description: string
  status: string
  docs_count: number
  chunks_count: number
  entities_count: number
  relations_count: number
  size_bytes: number
  size_display: string
  tags: string[]
  config: Record<string, unknown>
  created_at: string
  updated_at: string
}

interface RawDoc {
  id: string
  name: string
  type: string
  size_display: string
  status: string
  progress: number
  chunks_count: number
  entities_count: number
  relations_count: number
  uploaded_at: string
  indexed_at: string | null
  error_message: string | null
  stages: { name: string; status: string; pct: number }[]
}

interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ─── 字段映射 ─────────────────────────────────────────────────────────────

function mapConfig(raw: Record<string, unknown>): IndexConfig {
  return {
    chunkStrategy: ((raw.chunk_strategy as string) || 'recursive') as IndexConfig['chunkStrategy'],
    chunkSize: (raw.chunk_size as number) || 512,
    chunkOverlap: (raw.chunk_overlap as number) || 64,
    embeddingModel: (raw.embedding_model as string) || 'text-embedding-v4',
    embeddingDim: (raw.embedding_dim as number) || 1024,
    sparseAlgo: ((raw.sparse_algo as string) || 'bm25') as IndexConfig['sparseAlgo'],
    bm25K1: (raw.bm25_k1 as number) || 1.5,
    bm25B: (raw.bm25_b as number) || 0.75,
    entityModel: (raw.entity_model as string) || 'deepseek-v3',
    relationModel: (raw.relation_model as string) || 'deepseek-v3',
    enableGraph: (raw.enable_graph as boolean) ?? true,
    rerankerModel: (raw.reranker_model as string) || 'bge-reranker-v2-m3',
    enableReranker: (raw.enable_reranker as boolean) ?? false,
    topK: (raw.top_k as number) || 5,
    hybridAlpha: (raw.hybrid_alpha as number) || 0.7,
  }
}

function mapKB(raw: RawKB): KB {
  return {
    id: raw.id,
    name: raw.name,
    description: raw.description,
    status: raw.status as KB['status'],
    docs: raw.docs_count,
    chunks: raw.chunks_count,
    entities: raw.entities_count,
    relations: raw.relations_count,
    size: raw.size_display,
    updatedAt: raw.updated_at?.split('T')[0] || '',
    config: mapConfig(raw.config || {}),
    documents: [],
    entitiesData: [],
    relationsData: [],
    tags: raw.tags || [],
  }
}

function mapDoc(raw: RawDoc): KBDoc {
  return {
    id: raw.id,
    name: raw.name,
    type: raw.type as KBDoc['type'],
    size: raw.size_display,
    status: raw.status as KBDoc['status'],
    progress: raw.progress,
    chunks: raw.chunks_count,
    entities: raw.entities_count,
    relations: raw.relations_count,
    uploadedAt: raw.uploaded_at?.split('T')[0] || '',
    errorMessage: raw.error_message || null,
    stages: (raw.stages || []) as KBDoc['stages'],
  }
}

// ─── 知识库 CRUD ──────────────────────────────────────────────────────────

export async function fetchKnowledgeBases(params?: {
  page?: number
  page_size?: number
  search?: string
}): Promise<KB[]> {
  const res = await instance.get('/knowledge-bases', { params })
  const data = res.data.data as PaginatedData<RawKB>
  return data.items.map(mapKB)
}

export async function fetchKnowledgeBase(id: string): Promise<KB | null> {
  const res = await instance.get(`/knowledge-bases/${id}`)
  const raw = res.data.data as RawKB
  return raw ? mapKB(raw) : null
}

export async function createKnowledgeBase(data: CreateKBRequest): Promise<KB> {
  const payload = { ...data, config: configToSnake(data.config) }
  const res = await instance.post('/knowledge-bases', payload)
  return mapKB(res.data.data as RawKB)
}

export async function updateKnowledgeBase(
  id: string,
  patch: Partial<KB>,
): Promise<KB> {
  const payload: Record<string, unknown> = { ...patch }
  if (payload.config) {
    payload.config = configToSnake(payload.config as IndexConfig)
  }
  const res = await instance.put(`/knowledge-bases/${id}`, payload)
  return mapKB(res.data.data as RawKB)
}

export async function deleteKnowledgeBase(id: string): Promise<boolean> {
  const res = await instance.delete(`/knowledge-bases/${id}`)
  return res.data.code === 0
}

// ─── 统计 ─────────────────────────────────────────────────────────────────

export interface KBStatsResponse {
  totalKbs: number
  totalDocs: number
  totalChunks: number
  totalEntities: number
  indexing: number
}

export async function fetchStats(): Promise<KBStatsResponse> {
  const res = await instance.get('/knowledge-bases/stats')
  const d = res.data.data as { total_kbs: number; total_docs: number; total_chunks: number; total_entities: number; total_indexing: number }
  return {
    totalKbs: d.total_kbs,
    totalDocs: d.total_docs,
    totalChunks: d.total_chunks,
    totalEntities: d.total_entities,
    indexing: d.total_indexing,
  }
}

// ─── 文档管理 ─────────────────────────────────────────────────────────────

export async function uploadDocuments(
  kbId: string,
  files: File[],
): Promise<KBDoc[]> {
  const formData = new FormData()
  files.forEach((f) => formData.append('files', f))
  const res = await instance.post(
    `/knowledge-bases/${kbId}/documents/upload`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return (res.data.data as RawDoc[]).map(mapDoc)
}

export async function fetchDocuments(
  kbId: string,
  params?: { page?: number; page_size?: number; search?: string; status?: string },
): Promise<PaginatedData<KBDoc>> {
  const res = await instance.get(`/knowledge-bases/${kbId}/documents`, { params })
  const data = res.data.data as PaginatedData<RawDoc>
  return { ...data, items: data.items.map(mapDoc) }
}

export async function fetchDocument(
  kbId: string,
  docId: string,
): Promise<KBDoc> {
  const res = await instance.get(`/knowledge-bases/${kbId}/documents/${docId}`)
  return mapDoc(res.data.data as RawDoc)
}

export async function deleteDocument(
  kbId: string,
  docId: string,
): Promise<boolean> {
  const res = await instance.delete(`/knowledge-bases/${kbId}/documents/${docId}`)
  return res.data.code === 0
}

export async function retryDocument(
  kbId: string,
  docId: string,
): Promise<KBDoc> {
  const res = await instance.post(`/knowledge-bases/${kbId}/documents/${docId}/retry`)
  return mapDoc(res.data.data as RawDoc)
}

// ─── 知识图谱 ─────────────────────────────────────────────────────────────

export interface GraphDataResponse {
  entities: { id: string; name: string; type: string; mentions: number }[]
  relations: { id: string; from: string; to: string; label: string; weight: number; sourceEntityId?: string; targetEntityId?: string }[]
}

export async function fetchGraphData(
  kbId: string,
  entityType?: string,
): Promise<GraphDataResponse> {
  const res = await instance.get(`/knowledge-bases/${kbId}/graph`, {
    params: entityType ? { entity_type: entityType } : {},
  })
  const raw = res.data.data as {
    entities: { id: string; name: string; type: string; mentions: number }[]
    relations: { id: string; from_entity: string; to_entity: string; label: string; weight: number; source_entity_id?: string; target_entity_id?: string }[]
  }
  return {
    entities: raw.entities || [],
    relations: (raw.relations || []).map((r) => ({
      id: r.id,
      from: r.source_entity_id || r.from_entity,
      to: r.target_entity_id || r.to_entity,
      label: r.label,
      weight: r.weight,
      sourceEntityId: r.source_entity_id,
      targetEntityId: r.target_entity_id,
    })),
  }
}

export async function reExtractGraph(kbId: string): Promise<{ entities: number; relations: number; docs_processed: number }> {
  const res = await instance.post(`/knowledge-bases/${kbId}/graph/re-extract`, null, {
    timeout: 600000,  // LLM 抽取耗时较长，10 分钟超时
  })
  return res.data.data as { entities: number; relations: number; docs_processed: number }
}

// ─── 索引活动 ─────────────────────────────────────────────────────────────

export async function fetchIndexingActivity(
  kbId: string,
  limit: number = 5,
): Promise<KBDoc[]> {
  const res = await instance.get(`/knowledge-bases/${kbId}/indexing-activity`, {
    params: { limit },
  })
  return (res.data.data as RawDoc[]).map(mapDoc)
}

// ─── 可用模型 & 提供商 ───────────────────────────────────────────────────

export interface AvailableModel {
  id: string
  name: string
  display_name: string
  type: string
  provider_id?: string
}

export async function fetchAvailableModels(
  type: string = 'llm',
  providerId?: string,
): Promise<AvailableModel[]> {
  const res = await instance.get('/knowledge-bases/available-models', {
    params: { model_type: type, ...(providerId ? { provider_id: providerId } : {}) },
  })
  return res.data.data as AvailableModel[]
}

export interface AvailableProvider {
  id: string
  name: string
  logo: string
  models: AvailableModel[]
}

export async function fetchAvailableProviders(
  modelType: string = 'llm',
): Promise<AvailableProvider[]> {
  const res = await instance.get('/knowledge-bases/available-providers', {
    params: { model_type: modelType },
  })
  return res.data.data as AvailableProvider[]
}

function configToSnake(config: IndexConfig): Record<string, unknown> {
  return {
    chunk_strategy: config.chunkStrategy,
    chunk_size: config.chunkSize,
    chunk_overlap: config.chunkOverlap,
    embedding_model: config.embeddingModel,
    embedding_dim: config.embeddingDim,
    sparse_algo: config.sparseAlgo,
    bm25_k1: config.bm25K1,
    bm25_b: config.bm25B,
    entity_model: config.entityModel,
    relation_model: config.relationModel,
    enable_graph: config.enableGraph,
    reranker_model: config.rerankerModel,
    enable_reranker: config.enableReranker,
    top_k: config.topK,
    hybrid_alpha: config.hybridAlpha,
  }
}

export async function reindexKnowledgeBase(
  kbId: string,
  config: IndexConfig,
): Promise<{ kb_id: string; docs_enqueued: number; status: string }> {
  const res = await instance.post(`/knowledge-bases/${kbId}/reindex`, configToSnake(config), {
    timeout: 600000,
  })
  return res.data.data as { kb_id: string; docs_enqueued: number; status: string }
}

export async function searchKnowledgeBase(
  _kbId: string,
  _query: string,
  _mode: string,
): Promise<SearchResult[]> {
  return []
}

// ─── 切片管理 ─────────────────────────────────────────────────────────────

interface RawChunk {
  id: string
  index: number
  content: string
  token_count: number
  char_count: number
  page_ref: string
  section: string
  entities: string[]
}

function mapChunk(raw: RawChunk): DocChunk {
  return {
    id: raw.id,
    index: raw.index,
    content: raw.content,
    tokenCount: raw.token_count,
    charCount: raw.char_count,
    pageRef: raw.page_ref || '',
    section: raw.section || '',
    entities: raw.entities || [],
    edited: false,
  }
}

export async function fetchDocumentChunks(
  kbId: string,
  docId: string,
  search?: string,
): Promise<DocChunk[]> {
  const res = await instance.get(
    `/knowledge-bases/${kbId}/documents/${docId}/chunks`,
    { params: search ? { search } : {} },
  )
  return (res.data.data as RawChunk[]).map(mapChunk)
}

export async function fetchChunkDetail(
  kbId: string,
  docId: string,
  chunkId: string,
): Promise<{ chunk: DocChunk; prevChunk: DocChunk | null; nextChunk: DocChunk | null }> {
  const res = await instance.get(
    `/knowledge-bases/${kbId}/documents/${docId}/chunks/${chunkId}`,
  )
  const d = res.data.data as {
    chunk: RawChunk
    prev_chunk: RawChunk | null
    next_chunk: RawChunk | null
  }
  return {
    chunk: mapChunk(d.chunk),
    prevChunk: d.prev_chunk ? mapChunk(d.prev_chunk) : null,
    nextChunk: d.next_chunk ? mapChunk(d.next_chunk) : null,
  }
}

export async function updateChunkContent(
  kbId: string,
  docId: string,
  chunkId: string,
  content: string,
): Promise<DocChunk> {
  const res = await instance.put(
    `/knowledge-bases/${kbId}/documents/${docId}/chunks/${chunkId}`,
    { content },
  )
  return mapChunk(res.data.data as RawChunk)
}

export async function deleteChunk(
  kbId: string,
  docId: string,
  chunkId: string,
): Promise<boolean> {
  const res = await instance.delete(
    `/knowledge-bases/${kbId}/documents/${docId}/chunks/${chunkId}`,
  )
  return res.data.code === 0
}

export async function batchChunkOp(
  kbId: string,
  docId: string,
  action: 'save_all' | 'delete',
  params?: { chunks?: { id: string; content: string }[]; chunkIds?: string[] },
): Promise<{ saved: number; deleted: number }> {
  const body: Record<string, unknown> = { action }
  if (action === 'save_all' && params?.chunks) {
    body.chunks = params.chunks.map((c) => ({ id: c.id, content: c.content }))
  }
  if (action === 'delete' && params?.chunkIds) {
    body.chunk_ids = params.chunkIds
  }
  const res = await instance.post(
    `/knowledge-bases/${kbId}/documents/${docId}/chunks/batch`,
    body,
  )
  return res.data.data as { saved: number; deleted: number }
}
