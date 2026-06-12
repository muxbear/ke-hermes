// 知识库相关类型定义

// 知识库状态
export type KBStatus = 'ready' | 'indexing' | 'error' | 'draft'

// 文档索引状态
export type DocStatus =
  | 'queued'
  | 'parsing'
  | 'chunking'
  | 'embedding'
  | 'bm25'
  | 'extracting'
  | 'indexed'
  | 'failed'

// 切片策略
export type ChunkStrategy = 'fixed' | 'recursive' | 'semantic' | 'markdown' | 'agentic'

// 稀疏检索算法
export type SparseAlgo = 'bm25' | 'bm25_plus' | 'tf_idf' | 'none'

// 文档类型
export type DocType = 'pdf' | 'md' | 'docx' | 'csv' | 'image' | 'html'

// 索引流水线阶段状态
export type StageStatus = 'pending' | 'running' | 'done' | 'failed'

// 索引配置
export interface IndexConfig {
  chunkStrategy: ChunkStrategy
  chunkSize: number
  chunkOverlap: number
  embeddingModel: string
  embeddingDim: number
  sparseAlgo: SparseAlgo
  bm25K1: number
  bm25B: number
  entityModel: string
  relationModel: string
  enableGraph: boolean
  rerankerModel: string
  enableReranker: boolean
  topK: number
  hybridAlpha: number
}

// 索引阶段
export interface DocStage {
  name: string
  status: StageStatus
  pct: number
}

// 知识库文档
export interface KBDoc {
  id: string
  name: string
  type: DocType
  size: string
  status: DocStatus
  progress: number
  chunks: number
  entities: number
  relations: number
  uploadedAt: string
  errorMessage: string | null
  stages: DocStage[]
}

// 知识图谱实体
export interface Entity {
  id: string
  name: string
  type: string
  mentions: number
  x: number
  y: number
}

// 知识图谱关系
export interface Relation {
  id: string
  from: string
  to: string
  label: string
}

// 知识库
export interface KB {
  id: string
  name: string
  description: string
  status: KBStatus
  docs: number
  chunks: number
  entities: number
  relations: number
  size: string
  updatedAt: string
  config: IndexConfig
  documents: KBDoc[]
  entitiesData: Entity[]
  relationsData: Relation[]
  tags: string[]
}

// 知识库状态配置
export interface KBStatusConfig {
  label: string
  cls: string
}

export const KB_STATUS_CONFIG: Record<KBStatus, KBStatusConfig> = {
  ready: { label: '就绪', cls: 'status-ready' },
  indexing: { label: '索引中', cls: 'status-indexing' },
  error: { label: '错误', cls: 'status-error' },
  draft: { label: '草稿', cls: 'status-draft' },
}

// 文档状态配置
export interface DocStatusConfig {
  label: string
  cls: string
}

export const DOC_STATUS_CONFIG: Record<DocStatus, DocStatusConfig> = {
  queued: { label: '排队', cls: 'doc-status-queued' },
  parsing: { label: '解析中', cls: 'doc-status-parsing' },
  chunking: { label: '切片中', cls: 'doc-status-chunking' },
  embedding: { label: '向量化', cls: 'doc-status-embedding' },
  bm25: { label: 'BM25 倒排', cls: 'doc-status-bm25' },
  extracting: { label: '实体抽取', cls: 'doc-status-extracting' },
  indexed: { label: '已索引', cls: 'doc-status-indexed' },
  failed: { label: '失败', cls: 'doc-status-failed' },
}

// 切片策略选项
export interface ChunkStrategyOption {
  value: ChunkStrategy
  label: string
  desc: string
}

export const CHUNK_STRATEGY_OPTIONS: ChunkStrategyOption[] = [
  { value: 'fixed', label: '固定长度', desc: '按字符数硬切，最简单' },
  { value: 'recursive', label: '递归分隔符', desc: '按段落→换行→句号递归切分' },
  { value: 'semantic', label: '语义分块', desc: '基于句子向量相似度自动切' },
  { value: 'markdown', label: 'Markdown 结构', desc: '按标题层级切分，保留结构' },
  { value: 'agentic', label: 'Agentic 智能', desc: 'LLM 判断主题边界' },
]

// Embedding 模型选项
export interface EmbeddingModelOption {
  value: string
  label: string
  dim: number
}

export const EMBEDDING_MODEL_OPTIONS: EmbeddingModelOption[] = [
  { value: 'bge-large-zh-v1.5', label: 'BGE-Large-zh v1.5', dim: 1024 },
  { value: 'bge-m3', label: 'BGE-M3 (多语言)', dim: 1024 },
  { value: 'text-embedding-3-large', label: 'OpenAI text-embedding-3-large', dim: 3072 },
  { value: 'text-embedding-3-small', label: 'OpenAI text-embedding-3-small', dim: 1536 },
  { value: 'qwen3-embedding-8b', label: 'Qwen3-Embedding-8B', dim: 4096 },
  { value: 'jina-embeddings-v3', label: 'Jina Embeddings v3', dim: 1024 },
]

export const LLM_MODEL_OPTIONS = [
  'gpt-4o',
  'gpt-4o-mini',
  'claude-opus-4-7',
  'claude-sonnet-4-6',
  'qwen3-72b',
  'deepseek-v3',
  'glm-4.5',
] as const

export const RERANKER_MODEL_OPTIONS = [
  'bge-reranker-v2-m3',
  'bge-reranker-large',
  'cohere-rerank-v3',
  'jina-reranker-v2',
] as const

// 文档类型配置
export interface DocTypeConfig {
  label: string
  icon: string
}

export const DOC_TYPE_CONFIG: Record<DocType, DocTypeConfig> = {
  pdf: { label: 'PDF', icon: 'pdf' },
  md: { label: 'Markdown', icon: 'md' },
  docx: { label: 'Word', icon: 'docx' },
  csv: { label: 'CSV', icon: 'csv' },
  image: { label: '图片', icon: 'image' },
  html: { label: 'HTML', icon: 'html' },
}

// 检索模式
export type SearchMode = 'hybrid' | 'vector' | 'bm25'

export interface SearchModeConfig {
  label: string
  desc: string
}

export const SEARCH_MODE_CONFIG: Record<SearchMode, SearchModeConfig> = {
  hybrid: { label: '混合检索', desc: '向量 + BM25 融合' },
  vector: { label: '向量检索', desc: '稠密语义' },
  bm25: { label: 'BM25', desc: '稀疏关键词' },
}

// 检索结果
export interface SearchResult {
  id: string
  doc: string
  chunk: string
  score: number
  vec: number
  bm25: number
}

// 视图模式
export type ViewMode = 'grid' | 'list'

// 文档流水线阶段名称
export const DOC_STAGE_NAMES = ['排队', '解析', '切片', '向量化', 'BM25 倒排', '实体抽取', '关系抽取', '入库']

// 创建知识库请求
export interface CreateKBRequest {
  name: string
  description: string
  tags: string[]
  config: IndexConfig
}

// 上传文档请求
export interface UploadDocRequest {
  name: string
  type: DocType
  size: string
}
