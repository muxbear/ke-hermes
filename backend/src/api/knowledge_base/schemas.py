"""Knowledge Base API — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


# ─── IndexConfig ────────────────────────────────────────────────────────────

class IndexConfigSchema(BaseModel):
    """索引配置（对应前端 IndexConfig）。"""
    chunk_strategy: str = Field(default="recursive", description="fixed|recursive|semantic|markdown|agentic")
    chunk_size: int = Field(default=512, ge=128, le=2048)
    chunk_overlap: int = Field(default=64, ge=0, le=512)
    embedding_model: str = Field(default="text-embedding-v4")
    embedding_dim: int = Field(default=1024)
    sparse_algo: str = Field(default="bm25", description="bm25|bm25_plus|tf_idf|none")
    bm25_k1: float = Field(default=1.5)
    bm25_b: float = Field(default=0.75)
    entity_model: str = Field(default="deepseek-v3")
    relation_model: str = Field(default="deepseek-v3")
    enable_graph: bool = Field(default=True)
    reranker_model: str = Field(default="bge-reranker-v2-m3")
    enable_reranker: bool = Field(default=False)
    top_k: int = Field(default=5, ge=1, le=50)
    hybrid_alpha: float = Field(default=0.7, ge=0.0, le=1.0)


# ─── KnowledgeBase ──────────────────────────────────────────────────────────

class KBCreateRequest(BaseModel):
    """创建知识库请求（对应前端 CreateKBRequest）。"""
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    tags: list[str] = []
    config: IndexConfigSchema = Field(default_factory=IndexConfigSchema)


class KBUpdateRequest(BaseModel):
    """更新知识库请求。"""
    name: str | None = Field(default=None, max_length=128)
    description: str | None = None
    tags: list[str] | None = None
    config: IndexConfigSchema | None = None


class KBResponse(BaseModel):
    """知识库响应。"""
    id: str
    name: str
    description: str
    status: str
    docs_count: int
    chunks_count: int
    entities_count: int
    relations_count: int
    size_bytes: int
    size_display: str
    tags: list[str]
    config: IndexConfigSchema
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KBListResponse(BaseModel):
    """知识库分页列表。"""
    items: list[KBResponse]
    total: int
    page: int
    page_size: int


class KBStatsResponse(BaseModel):
    """知识库统计信息。"""
    total_kbs: int
    total_docs: int
    total_chunks: int
    total_entities: int
    total_indexing: int


# ─── Document ───────────────────────────────────────────────────────────────

class DocStageInfo(BaseModel):
    """索引流水线阶段信息。"""
    name: str
    status: str  # pending|running|done|failed
    pct: int


class KBDocResponse(BaseModel):
    """文档响应。"""
    id: str
    name: str
    type: str
    size_display: str
    status: str
    progress: int
    chunks_count: int
    entities_count: int
    relations_count: int
    uploaded_at: datetime
    indexed_at: datetime | None = None
    error_message: str | None = None
    stages: list[DocStageInfo] = []
    config: IndexConfigSchema | None = None

    model_config = {"from_attributes": True}


class KBDocListResponse(BaseModel):
    """文档分页列表。"""
    items: list[KBDocResponse]
    total: int
    page: int
    page_size: int


class KBDocUploadResponse(BaseModel):
    """上传文档响应。"""
    id: str
    name: str
    type: str
    size_display: str
    status: str
    uploaded_at: datetime
    config: IndexConfigSchema | None = None


# ─── Graph ──────────────────────────────────────────────────────────────────

class EntityResponse(BaseModel):
    """实体。"""
    id: str
    name: str
    type: str
    mentions: int
    source_text: str | None = None

    model_config = {"from_attributes": True}


class RelationResponse(BaseModel):
    """关系。"""
    id: str
    from_entity: str
    to_entity: str
    label: str
    weight: float
    source_entity_id: str | None = None
    target_entity_id: str | None = None

    model_config = {"from_attributes": True}


class GraphDataResponse(BaseModel):
    """图谱数据。"""
    entities: list[EntityResponse]
    relations: list[RelationResponse]


# ─── Search ──────────────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    """检索请求。"""
    query: str = Field(..., min_length=1, max_length=2000, description="检索查询文本")
    mode: str = Field(default="hybrid", description="检索模式: hybrid | vector | bm25")
    top_k: int = Field(default=5, ge=1, le=50, description="返回结果数量")
    alpha: float | None = Field(default=None, ge=0.0, le=1.0, description="混合检索向量权重")


class ChunkMatch(BaseModel):
    """匹配到的分片。"""
    id: str
    doc_id: str
    doc_name: str
    chunk_index: int
    content: str
    score: float
    vec_score: float | None = None
    bm25_score: float | None = None


class SearchResponse(BaseModel):
    """检索响应。"""
    query: str
    mode: str
    total: int
    results: list[ChunkMatch]


# ─── Chunk ───────────────────────────────────────────────────────────────────


class ChunkResponse(BaseModel):
    """切片响应（对应前端 DocChunk 接口）。"""
    id: str
    index: int
    content: str
    token_count: int
    char_count: int
    page_ref: str = ""
    section: str = ""
    entities: list[str] = []


class ChunkDetailResponse(BaseModel):
    """切片详情（含上下文）。"""
    chunk: ChunkResponse
    prev_chunk: ChunkResponse | None = None
    next_chunk: ChunkResponse | None = None


class ChunkUpdateRequest(BaseModel):
    """更新切片请求。"""
    content: str


class BatchChunkRequest(BaseModel):
    """批量操作请求。"""
    action: str  # "save_all" | "delete"
    chunks: list[dict] = []     # [{id, content}, ...]
    chunk_ids: list[str] = []   # for delete action


# ─── Core Response ──────────────────────────────────────────────────────────

class ApiResponse(BaseModel):
    """统一 API 响应包装（通用泛型，前端 response wrapper 匹配）。"""
    code: int = 0
    data: object | None = None
    message: str = "ok"
