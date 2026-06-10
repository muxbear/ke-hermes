// 知识库 API 服务（第一阶段：Mock 数据）
import type {
  KB,
  KBDoc,
  IndexConfig,
  DocType,
  SearchResult,
  DocStage,
  DocStatus,
} from '@/types/knowledgeBase'
import { DOC_STAGE_NAMES } from '@/types/knowledgeBase'

// ─── Mock 数据工具 ──────────────────────────────────────────────────────────

function makeStages(overall: number): DocStage[] {
  return DOC_STAGE_NAMES.map((name, i) => {
    const each = 100 / DOC_STAGE_NAMES.length
    const start = i * each
    const end = (i + 1) * each
    let pct = 0
    let status: DocStage['status'] = 'pending'
    if (overall >= end) {
      pct = 100
      status = 'done'
    } else if (overall > start) {
      pct = ((overall - start) / each) * 100
      status = 'running'
    }
    return { name, status, pct }
  })
}

// ─── Mock 数据 ──────────────────────────────────────────────────────────────

const MOCK_ENTITIES = [
  { id: 'e1', name: '张三', type: '人物', mentions: 24, x: 200, y: 120 },
  { id: 'e2', name: '李四', type: '人物', mentions: 18, x: 420, y: 80 },
  { id: 'e3', name: 'ke-hermes', type: '产品', mentions: 56, x: 320, y: 220 },
  { id: 'e4', name: 'Anthropic', type: '组织', mentions: 12, x: 540, y: 200 },
  { id: 'e5', name: 'RAG', type: '概念', mentions: 41, x: 140, y: 280 },
  { id: 'e6', name: '向量检索', type: '概念', mentions: 33, x: 460, y: 340 },
  { id: 'e7', name: '知识图谱', type: '概念', mentions: 28, x: 240, y: 400 },
  { id: 'e8', name: 'BM25', type: '算法', mentions: 22, x: 600, y: 100 },
]

const MOCK_RELATIONS = [
  { id: 'r1', from: 'e1', to: 'e3', label: '负责' },
  { id: 'r2', from: 'e3', to: 'e5', label: '采用' },
  { id: 'r3', from: 'e3', to: 'e7', label: '构建' },
  { id: 'r4', from: 'e5', to: 'e6', label: '包含' },
  { id: 'r5', from: 'e5', to: 'e8', label: '结合' },
  { id: 'r6', from: 'e2', to: 'e4', label: '联系' },
  { id: 'r7', from: 'e7', to: 'e6', label: '增强' },
  { id: 'r8', from: 'e3', to: 'e4', label: '集成' },
]

const DEFAULT_CONFIG: IndexConfig = {
  chunkStrategy: 'recursive',
  chunkSize: 512,
  chunkOverlap: 64,
  embeddingModel: 'bge-large-zh-v1.5',
  embeddingDim: 1024,
  sparseAlgo: 'bm25',
  bm25K1: 1.5,
  bm25B: 0.75,
  entityModel: 'gpt-4o-mini',
  relationModel: 'gpt-4o-mini',
  enableGraph: true,
  rerankerModel: 'bge-reranker-v2-m3',
  enableReranker: true,
  topK: 10,
  hybridAlpha: 0.5,
}

const MOCK_DOCS: KBDoc[] = [
  {
    id: 'd1', name: '员工手册-2026.pdf', type: 'pdf', size: '3.2 MB',
    status: 'indexed', progress: 100, chunks: 142, entities: 38, relations: 56,
    uploadedAt: '2026-06-08', stages: makeStages(100),
  },
  {
    id: 'd2', name: 'RAG技术白皮书.md', type: 'md', size: '186 KB',
    status: 'indexed', progress: 100, chunks: 64, entities: 22, relations: 31,
    uploadedAt: '2026-06-07', stages: makeStages(100),
  },
  {
    id: 'd3', name: '产品规格说明书.docx', type: 'docx', size: '1.1 MB',
    status: 'extracting', progress: 72, chunks: 88, entities: 14, relations: 9,
    uploadedAt: '2026-06-10', stages: makeStages(72),
  },
  {
    id: 'd4', name: '客户访谈记录.csv', type: 'csv', size: '412 KB',
    status: 'embedding', progress: 45, chunks: 53, entities: 0, relations: 0,
    uploadedAt: '2026-06-10', stages: makeStages(45),
  },
  {
    id: 'd5', name: 'API 文档.html', type: 'html', size: '780 KB',
    status: 'queued', progress: 0, chunks: 0, entities: 0, relations: 0,
    uploadedAt: '2026-06-10', stages: makeStages(0),
  },
  {
    id: 'd6', name: '架构图-2025Q4.png', type: 'image', size: '2.4 MB',
    status: 'failed', progress: 30, chunks: 0, entities: 0, relations: 0,
    uploadedAt: '2026-06-09',
    stages: makeStages(30).map((s, i) =>
      i === 1 ? { ...s, status: 'failed' as const, pct: 100 } : s,
    ),
  },
]

const MOCK_KBS: KB[] = [
  {
    id: 'kb1', name: '企业内部规章制度', description: '员工手册、考勤、报销等行政制度文档',
    status: 'ready', docs: 28, chunks: 1842, entities: 312, relations: 568, size: '146 MB',
    updatedAt: '2026-06-09', config: { ...DEFAULT_CONFIG },
    documents: [...MOCK_DOCS], entitiesData: [...MOCK_ENTITIES], relationsData: [...MOCK_RELATIONS],
    tags: ['行政', '制度', 'HR'],
  },
  {
    id: 'kb2', name: '产品技术文档', description: 'ke-hermes 全套技术架构、API、SDK 文档',
    status: 'indexing', docs: 56, chunks: 4128, entities: 892, relations: 1456, size: '412 MB',
    updatedAt: '2026-06-10',
    config: { ...DEFAULT_CONFIG, chunkStrategy: 'markdown', chunkSize: 800 },
    documents: [...MOCK_DOCS.slice(0, 4)], entitiesData: [...MOCK_ENTITIES], relationsData: [...MOCK_RELATIONS],
    tags: ['产品', '技术', 'API'],
  },
  {
    id: 'kb3', name: '客户支持知识库', description: 'FAQ、工单历史、故障排查指南',
    status: 'ready', docs: 142, chunks: 8934, entities: 2341, relations: 4521, size: '892 MB',
    updatedAt: '2026-06-08',
    config: { ...DEFAULT_CONFIG, embeddingModel: 'bge-m3', embeddingDim: 1024, enableGraph: false },
    documents: [...MOCK_DOCS.slice(0, 3)], entitiesData: [...MOCK_ENTITIES], relationsData: [...MOCK_RELATIONS],
    tags: ['客户', 'FAQ', '运维'],
  },
  {
    id: 'kb4', name: '法务合同库', description: '合同模板、法律法规、合规审查要点',
    status: 'draft', docs: 0, chunks: 0, entities: 0, relations: 0, size: '0 MB',
    updatedAt: '2026-06-10',
    config: { ...DEFAULT_CONFIG, embeddingModel: 'text-embedding-3-large', embeddingDim: 3072 },
    documents: [], entitiesData: [], relationsData: [],
    tags: ['法务', '合规'],
  },
  {
    id: 'kb5', name: '研发设计沉淀', description: '技术决策、架构方案、设计评审记录',
    status: 'error', docs: 18, chunks: 612, entities: 89, relations: 134, size: '78 MB',
    updatedAt: '2026-06-07',
    config: { ...DEFAULT_CONFIG, chunkStrategy: 'agentic', entityModel: 'claude-opus-4-7' },
    documents: [...MOCK_DOCS.slice(0, 2)], entitiesData: [...MOCK_ENTITIES], relationsData: [...MOCK_RELATIONS],
    tags: ['研发', '架构'],
  },
]

// ─── Mock API 函数 ──────────────────────────────────────────────────────────

let kbs = [...MOCK_KBS]

/** 获取知识库列表 */
export async function fetchKnowledgeBases(): Promise<KB[]> {
  await delay(300)
  return [...kbs]
}

/** 获取知识库详情 */
export async function fetchKnowledgeBase(id: string): Promise<KB | null> {
  await delay(200)
  return kbs.find((k) => k.id === id) || null
}

/** 创建知识库 */
export async function createKnowledgeBase(data: {
  name: string
  description: string
  tags: string[]
  config: IndexConfig
}): Promise<KB> {
  await delay(400)
  const newKb: KB = {
    id: `kb-${Date.now()}`,
    name: data.name,
    description: data.description,
    status: 'draft',
    docs: 0, chunks: 0, entities: 0, relations: 0, size: '0 MB',
    updatedAt: new Date().toISOString().slice(0, 10),
    config: data.config,
    documents: [], entitiesData: [], relationsData: [],
    tags: data.tags,
  }
  kbs = [newKb, ...kbs]
  return newKb
}

/** 更新知识库 */
export async function updateKnowledgeBase(
  id: string,
  patch: Partial<KB>,
): Promise<KB | null> {
  await delay(300)
  const idx = kbs.findIndex((k) => k.id === id)
  if (idx === -1) return null
  kbs[idx] = { ...kbs[idx], ...patch }
  return kbs[idx]
}

/** 删除知识库 */
export async function deleteKnowledgeBase(id: string): Promise<boolean> {
  await delay(300)
  const idx = kbs.findIndex((k) => k.id === id)
  if (idx === -1) return false
  kbs.splice(idx, 1)
  return true
}

/** 在知识库中上传文档 */
export async function uploadDocuments(
  kbId: string,
  files: { name: string; type: DocType; size: string }[],
): Promise<KBDoc[] | null> {
  await delay(500)
  const kb = kbs.find((k) => k.id === kbId)
  if (!kb) return null
  const newDocs: KBDoc[] = files.map((f, i) => ({
    id: `d-${Date.now()}-${i}`,
    name: f.name,
    type: f.type,
    size: f.size,
    status: 'parsing' as DocStatus,
    progress: 5,
    chunks: 0, entities: 0, relations: 0,
    uploadedAt: new Date().toISOString().slice(0, 10),
    stages: makeStages(5),
  }))
  kb.documents = [...newDocs, ...kb.documents]
  return newDocs
}

/** 删除文档 */
export async function deleteDocument(
  kbId: string,
  docId: string,
): Promise<boolean> {
  await delay(200)
  const kb = kbs.find((k) => k.id === kbId)
  if (!kb) return false
  const idx = kb.documents.findIndex((d) => d.id === docId)
  if (idx === -1) return false
  kb.documents.splice(idx, 1)
  return true
}

/** 重试失败文档 */
export async function retryDocument(
  kbId: string,
  docId: string,
): Promise<boolean> {
  await delay(200)
  const kb = kbs.find((k) => k.id === kbId)
  if (!kb) return false
  const doc = kb.documents.find((d) => d.id === docId)
  if (!doc) return false
  doc.status = 'parsing'
  doc.progress = 5
  doc.stages = makeStages(5)
  return true
}

/** 模拟检索 */
export async function searchKnowledgeBase(
  _kbId: string,
  query: string,
  _mode: string,
): Promise<SearchResult[]> {
  await delay(600)
  return [
    {
      id: 'c1', doc: 'RAG技术白皮书.md',
      chunk: `RAG(Retrieval-Augmented Generation)是一种通过检索外部知识库来增强大语言模型生成能力的技术，${query} 是其中关键环节…`,
      score: 0.94, vec: 0.92, bm25: 0.87,
    },
    {
      id: 'c2', doc: '员工手册-2026.pdf',
      chunk: `关于 ${query} 的具体规定，详见第三章第二节。所有员工应严格遵守相关流程，不得擅自变更…`,
      score: 0.88, vec: 0.85, bm25: 0.91,
    },
    {
      id: 'c3', doc: '产品规格说明书.docx',
      chunk: `${query} 模块基于 BGE-Large 模型构建，结合 BM25 倒排索引实现混合检索，Top-K 默认 10…`,
      score: 0.83, vec: 0.81, bm25: 0.79,
    },
    {
      id: 'c4', doc: 'API 文档.html',
      chunk: `调用 /api/v1/search 接口可指定 ${query} 的检索模式，支持 vector / bm25 / hybrid 三种…`,
      score: 0.76, vec: 0.74, bm25: 0.72,
    },
    {
      id: 'c5', doc: '客户访谈记录.csv',
      chunk: `客户反馈在 ${query} 场景下的检索召回率较以往提升 23%，但对长尾术语仍存在覆盖不足…`,
      score: 0.71, vec: 0.68, bm25: 0.74,
    },
  ]
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
