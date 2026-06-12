# Ke-Hermes Knowledge（知识库）功能模块详细设计说明书

**版本**: 1.0.0
**状态**: 待实现
**日期**: 2026-06-11

---

## 1. 概述

### 1.1 背景

ke-hermes 是一个基于 DeepAgents (LangGraph) 的通用智能体服务平台。Knowledge（知识库）模块为企业提供多模态 RAG（检索增强生成）知识库管理与维护能力——用户可创建知识库、上传文档、执行索引流程（解析→切片→向量化→BM25 倒排→实体/关系抽取→入库），并在知识图谱中可视化实体与关系。

### 1.2 现状分析

| 位置 | 现状 |
|------|------|
| `frontend/src/views/KnowledgeBaseView.vue` | 知识库主页面完整实现（列表/详情双模式），含 5 个标签页 |
| `frontend/src/components/knowledgeBase/` | 14 个子组件（概览/文档/图谱/检索/配置/卡片/弹窗等） |
| `frontend/src/stores/knowledgeBase.ts` | Pinia 状态管理，含 mock 动画逻辑 |
| `frontend/src/services/knowledgeBaseApi.ts` | **全部为 Mock 实现**，需替换为真实 HTTP 调用 |
| `frontend/src/types/knowledgeBase.ts` | 完整类型定义，后端 schemas 的参考基线 |
| `backend/src/` | **无任何知识库相关代码** |
| `backend/.env` | 已配置 `MILVUS_URI`/`MILVUS_USER`/`MILVUS_PASSWORD`，但未引用 |
| `backend/src/agent/models/em.py` | DashScope Embeddings 已实例化但未使用 |

### 1.3 目标

1. 后端提供完整的知识库 CRUD API + 数据库持久化
2. 实现文档上传、解析、切片、向量化、BM25 索引、实体/关系抽取的完整 RAG 流水线
3. 支持多向量数据库切换（Milvus / Chroma），默认 Milvus
4. 文档存储可配置（本地目录 / MinIO），默认本地目录
5. 知识图谱数据持久化与查询 API
6. 概览页统计数据 API
7. "检索"和"检索配置"2 个标签页的后端逻辑**暂不实现**

### 1.4 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI + Pydantic |
| ORM | SQLAlchemy 2.0 async |
| 数据库 | PostgreSQL（生产）/ SQLite（开发） |
| 向量数据库 | Milvus（默认）/ Chroma（可配置切换） |
| 文档加载 | langchain 社区加载器（PyPDF、Unstructured、CSV、JSON 等），langchain-opendataloader-pdf PDF 加载器 |
| Embedding | 后端配置的 LLM 模型（DeepSeek / 质谱 / DashScope 等） |
| 实体/关系抽取 | langextract 框架 |
| 图存储 | langextract 内置存储（默认）/ Neo4j（规划，暂不实现） |
| 对象存储 | 本地文件系统（默认）/ MinIO（规划，暂不实现） |
| 任务队列 | 后台异步任务（asyncio + 状态机） |

---

## 2. 系统架构

### 2.1 整体分层

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  KnowledgeBaseView → KbDetail → KbOverviewTab/KbDocsTab/    │
│  KbGraphTab/KbSearchTab/KbConfigTab                          │
│  useKnowledgeBaseStore → knowledgeBaseApi → Axios            │
├──────────────────────────────────────────────────────────────┤
│                HTTP REST (/api/knowledge-bases)               │
├──────────────────────────────────────────────────────────────┤
│                        Backend                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ api/knowledge_base/                                     │ │
│  │   kb_api.py       # 知识库 CRUD 路由                     │ │
│  │   doc_api.py      # 文档上传/删除/重试 路由              │ │
│  │   graph_api.py    # 知识图谱查询路由                     │ │
│  │   schemas.py      # Pydantic 请求/响应模型               │ │
│  │   service.py      # 知识库业务逻辑                       │ │
│  │   doc_service.py  # 文档加载 & RAG 索引流水线             │ │
│  │   graph_service.py# 实体/关系抽取 & 图谱查询              │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ core/rag/                                                │ │
│  │   vector_store.py # 向量数据库抽象（Milvus/Chroma）       │ │
│  │   embedding.py    # Embedding 模型工厂                   │ │
│  │   loaders.py      # 文档加载器工厂                       │ │
│  │   splitters.py    # 文本切片器工厂                       │ │
│  │   bm25_index.py   # BM25 倒排索引                        │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│              PostgreSQL / SQLite (元数据)                     │
│              Milvus / Chroma (向量 + 全文检索)                │
│              langextract 内置存储 / Neo4j (图谱，规划中)       │
│              本地文件系统 / MinIO (文档存储，规划中)           │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 目录规划

```
backend/src/
├── api/
│   ├── __init__.py              ← 修改: 注册 kb_router
│   └── knowledge_base/          ← 新建
│       ├── __init__.py
│       ├── kb_api.py            # 知识库 CRUD 路由 (列表/详情/创建/更新/删除/统计)
│       ├── doc_api.py           # 文档管理路由 (上传/列表/删除/重试/流水线状态)
│       ├── graph_api.py         # 知识图谱路由 (实体/关系查询)
│       ├── schemas.py           # 全部 Pydantic 模型
│       ├── service.py           # 知识库 & 统计业务逻辑（外观模式）
│       ├── doc_service.py       # 索引流水线 + 调度器（模板方法 + 观察者 + 单例模式）
│       ├── doc_state.py         # 文档状态机（状态模式）
│       └── graph_service.py     # 图谱抽取 & 查询业务逻辑
├── core/
│   └── rag/                     ← 新建
│       ├── __init__.py
│       ├── vector_store.py      # 向量数据库抽象 + Milvus/Chroma 实现（策略模式）
│       ├── collection_builder.py# Milvus Collection 建造者（建造者模式）
│       ├── embedding.py         # Embedding 模型工厂
│       ├── loaders.py           # 文档加载器（策略模式 + 组合模式）
│       ├── splitters.py         # 文本切片器（策略模式）
│       └── bm25_index.py        # BM25 倒排索引
├── db/
│   └── models/
│       ├── __init__.py          ← 修改: 导出新模型
│       ├── knowledge_base.py    ← 新建: KnowledgeBase ORM
│       ├── knowledge_base_document.py ← 新建: KBDocument ORM
│       ├── knowledge_base_entity.py   ← 新建: KBEntity ORM
│       └── knowledge_base_relation.py ← 新建: KBRelation ORM
└── server.py                    ← 修改: lifespan 中初始化向量数据库连接
```

---

## 3. 数据库设计（关系型元数据）

### 3.1 knowledge_bases 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `String(36)` | PK, UUID | 主键 |
| `name` | `String(128)` | not null | 知识库名称 |
| `description` | `Text` | default "" | 描述 |
| `status` | `String(16)` | default "draft" | ready / indexing / error / draft |
| `config` | `JSON` | not null | 索引配置（见 5.2.1 IndexConfig） |
| `tags` | `JSON` | default [] | 标签列表 |
| `docs_count` | `Integer` | default 0 | 文档总数（冗余计数） |
| `chunks_count` | `Integer` | default 0 | 分片总数（冗余计数） |
| `entities_count` | `Integer` | default 0 | 实体总数（冗余计数） |
| `relations_count` | `Integer` | default 0 | 关系总数（冗余计数） |
| `size_bytes` | `BigInteger` | default 0 | 文档总大小（字节） |
| `user_id` | `String(36)` | not null, FK→users | 所有者 |
| `created_at` | `DateTime` | server_default | 创建时间 |
| `updated_at` | `DateTime` | onupdate | 更新时间 |

**索引**: `(user_id, updated_at DESC)` 复合索引（按用户+时间排序）

### 3.2 knowledge_base_documents 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `String(36)` | PK, UUID | 主键 |
| `kb_id` | `String(36)` | FK→knowledge_bases, not null | 所属知识库 |
| `name` | `String(256)` | not null | 文件名 |
| `type` | `String(16)` | not null | pdf / md / docx / csv / txt / html / json / xlsx / pptx / image |
| `size_bytes` | `BigInteger` | default 0 | 文件大小（字节） |
| `status` | `String(16)` | default "queued" | queued→parsing→chunking→embedding→bm25→extracting→indexed / failed |
| `progress` | `Integer` | default 0 | 整体进度 0-100 |
| `chunks_count` | `Integer` | default 0 | 该文档分片数 |
| `entities_count` | `Integer` | default 0 | 该文档实体数 |
| `relations_count` | `Integer` | default 0 | 该文档关系数 |
| `storage_path` | `String(512)` | not null | 文件存储路径（本地路径或 MinIO key） |
| `uploaded_at` | `DateTime` | server_default | 上传时间 |
| `indexed_at` | `DateTime` | nullable | 索引完成时间 |
| `error_message` | `Text` | nullable | 失败原因 |

**索引**: `(kb_id, status)` 复合索引；`(kb_id, uploaded_at DESC)` 复合索引

### 3.3 knowledge_base_entities 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `String(36)` | PK, UUID | 主键 |
| `kb_id` | `String(36)` | FK→knowledge_bases, not null | 所属知识库 |
| `name` | `String(256)` | not null | 实体名称 |
| `type` | `String(64)` | not null | 实体类型（人物/组织/产品/概念/算法/地点/时间/事件） |
| `mentions` | `Integer` | default 0 | 提及次数 |
| `metadata_` | `JSON` | default {} | 扩展元数据 |

**索引**: `(kb_id, type)` 复合索引；`(kb_id, mentions DESC)` 复合索引

### 3.4 knowledge_base_relations 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `String(36)` | PK, UUID | 主键 |
| `kb_id` | `String(36)` | FK→knowledge_bases, not null | 所属知识库 |
| `from_entity` | `String(256)` | not null | 源实体名称 |
| `to_entity` | `String(256)` | not null | 目标实体名称 |
| `label` | `String(256)` | not null | 关系标签 |
| `weight` | `Float` | default 1.0 | 关系权重 |

**索引**: `(kb_id, from_entity, to_entity)` 唯一约束；`(kb_id, label)` 复合索引

### 3.5 SQLAlchemy 模型定义示例

```python
# backend/src/db/models/knowledge_base.py

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Text, DateTime, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="draft")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    docs_count: Mapped[int] = mapped_column(Integer, default=0)
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)
    entities_count: Mapped[int] = mapped_column(Integer, default=0)
    relations_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
```

---

## 4. 配置与环境变量

### 4.1 新增环境变量 (`.env` / `Settings`)

```ini
# ──── 向量数据库 ────
# 向量数据库后端: milvus | chroma
VECTOR_DB_BACKEND=milvus

# Milvus 连接
MILVUS_URI=http://localhost:19530
MILVUS_USER=root
MILVUS_PASSWORD=Milvus
MILVUS_DEFAULT_DB=ke_hermes

# Chroma（备选）
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_PERSIST_DIR=./chroma_data

# ──── 文档存储 ────
# 存储后端: local | minio（暂不实现）
DOC_STORE_BACKEND=local
DOC_UPLOAD_DIR=./workspace/docs_upload

# MinIO（规划中，暂不实现）
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_BUCKET=ke-hermes-docs

# ──── 图存储 ────
# 图谱存储: langextract | neo4j（暂不实现）
GRAPH_STORE_BACKEND=langextract

# Neo4j（规划中，暂不实现）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=

# ──── Embedding ────
# 默认 embedding 模型（对应 ai_models 表中的模型名称）
DEFAULT_EMBEDDING_MODEL=text-embedding-v4
DEFAULT_EMBEDDING_DIM=1024

# ──── 索引 ────
# 索引并发数
INDEXING_MAX_CONCURRENT=3
# BM25 默认参数
BM25_DEFAULT_K1=1.5
BM25_DEFAULT_B=0.75
```

### 4.2 Settings 类扩展

在 `backend/src/agent/config/config.py` 的 `Settings` 类中新增对应字段：

```python
# 向量数据库
vector_db_backend: str = "milvus"         # milvus | chroma
chroma_host: str = "localhost"
chroma_port: int = 8001
chroma_persist_dir: str = "./chroma_data"

# 文档存储
doc_store_backend: str = "local"          # local | minio
doc_upload_dir: str = "./workspace/docs_upload"

# 图存储
graph_store_backend: str = "langextract"  # langextract | neo4j

# Embedding
default_embedding_model: str = "text-embedding-v4"
default_embedding_dim: int = 1024

# 索引
indexing_max_concurrent: int = 3
bm25_default_k1: float = 1.5
bm25_default_b: float = 0.75
```

---

## 5. 后端 API 设计

### 5.1 通用约定

- **Base URL**: `/api`
- **响应格式**: `ApiResponse<T>` 统一包装
  ```json
  { "code": 0, "data": {...}, "message": "ok", "requestId": "...", "timestamp": ... }
  ```
- **认证**: 所有接口需 `Authorization: Bearer <JWT>` 头
- **分页**: 列表接口统一支持 `page`（默认 1）和 `page_size`（默认 20，最大 100）参数，返回 `{ items, total, page, page_size }` 结构
- **错误码**:
  - `404` 知识库/文档不存在
  - `400` 参数校验失败
  - `409` 名称冲突

---

### 5.2 TypeScript 类型定义到 Pydantic Schema 的映射

#### 5.2.1 IndexConfig（索引配置）

对应前端 `types/knowledgeBase.ts` 中的 `IndexConfig`：

```python
# backend/src/api/knowledge_base/schemas.py

from pydantic import BaseModel, Field


class IndexConfigSchema(BaseModel):
    """索引配置"""
    chunk_strategy: str = "recursive"       # fixed | recursive | semantic | markdown | agentic
    chunk_size: int = Field(default=512, ge=128, le=2048)
    chunk_overlap: int = Field(default=64, ge=0, le=512)
    embedding_model: str = "text-embedding-v4"
    embedding_dim: int = 1024
    sparse_algo: str = "bm25"               # bm25 | bm25_plus | tf_idf | none
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    entity_model: str = "deepseek-v3"       # 实体抽取 LLM
    relation_model: str = "deepseek-v3"     # 关系抽取 LLM
    enable_graph: bool = True
    reranker_model: str = "bge-reranker-v2-m3"
    enable_reranker: bool = False
    top_k: int = Field(default=5, ge=1, le=50)
    hybrid_alpha: float = Field(default=0.7, ge=0.0, le=1.0)
```

---

### 5.3 知识库主页面接口

#### 5.3.1 获取知识库列表

```
GET /api/knowledge-bases?page=1&page_size=12&search=
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数，默认 12，最大 100 |
| `search` | string | 否 | 按名称/描述/标签模糊搜索 |

**响应**:
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "uuid-1",
        "name": "企业内部规章制度",
        "description": "公司内部管理规范与制度文档...",
        "status": "ready",
        "docs_count": 6,
        "chunks_count": 1284,
        "entities_count": 156,
        "relations_count": 89,
        "size_bytes": 15728640,
        "size_display": "15.7 MB",
        "tags": ["制度", "管理", "HR"],
        "config": { ... },
        "updated_at": "2026-06-10T15:30:00"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 12
  }
}
```

**后端逻辑**:
1. 从 `knowledge_bases` 表查询当前用户的记录
2. 若 `search` 非空，对 name/description/tags 做 ILIKE 模糊匹配
3. 按 `updated_at DESC` 排序，分页返回
4. `size_display` 在后端格式化（bytes → 人类可读）

---

#### 5.3.2 获取统计信息

```
GET /api/knowledge-bases/stats
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "total_kbs": 5,
    "total_docs": 30,
    "total_chunks": 6420,
    "total_entities": 780,
    "total_indexing": 2
  }
}
```

**后端逻辑**:
1. `total_kbs`: COUNT 当前用户的 knowledge_bases
2. `total_docs`: SUM 所有知识库的 docs_count
3. `total_chunks`: SUM 所有知识库的 chunks_count
4. `total_entities`: SUM 所有知识库的 entities_count
5. `total_indexing`: COUNT status='indexing' 的知识库数量

---

#### 5.3.3 创建知识库

```
POST /api/knowledge-bases
```

**请求体** (对齐前端 `CreateKBRequest`):
```json
{
  "name": "新产品技术文档",
  "description": "产品技术规范与 API 文档",
  "tags": ["技术", "API", "产品"],
  "config": { ... }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | **是** | 名称（最长 128 字符） |
| `description` | string | 否 | 描述 |
| `tags` | string[] | 否 | 标签 |
| `config` | IndexConfigSchema | 否 | 索引配置（不传则使用默认值） |

**后端逻辑**:
1. 校验 name 非空
2. 检查同一用户下 name 是否重复（唯一约束 `(user_id, name)`）
3. 创建 `KnowledgeBase` 记录，status="draft"，初始化 config
4. 在向量数据库中创建对应的 Collection（命名：`kb_{kb_id}`）
5. 返回创建的知识库对象

---

#### 5.3.4 获取知识库详情

```
GET /api/knowledge-bases/{kb_id}
```

**响应**: 完整的 KB 对象（含 config、tags、统计计数），但不含 documents 列表（通过文档列表接口分页获取）

---

#### 5.3.5 更新知识库

```
PUT /api/knowledge-bases/{kb_id}
```

**请求体**:
```json
{
  "name": "新名称",
  "description": "新描述",
  "tags": ["新标签"],
  "config": { ... }
}
```

所有字段可选，仅更新传入的非 null 字段。

**后端逻辑**:
1. 查找知识库，确认归属
2. 若更新 config，判断是否需要重建索引（chunk/embedding 参数变化 → 标记需要重建）
3. 保存更新

---

#### 5.3.6 删除知识库

```
DELETE /api/knowledge-bases/{kb_id}
```

**后端逻辑**:
1. 删除向量数据库中的 Collection（`kb_{kb_id}`）
2. 删除 `knowledge_base_documents` 中该 KB 的所有记录
3. 删除 `knowledge_base_entities` 和 `knowledge_base_relations` 中该 KB 的所有记录
4. 删除本地/对象存储中的所有文档文件
5. 删除 `knowledge_bases` 记录
6. 整个过程包装在事务中（关系型部分），向量库删除失败记录日志但不阻塞整体流程

---

### 5.4 概览标签页接口

概览页的数据已在 "知识库详情"（`GET /api/knowledge-bases/{kb_id}`）中直接返回统计字段，无需额外接口。

#### 5.4.1 最近索引活动

```
GET /api/knowledge-bases/{kb_id}/indexing-activity?limit=5
```

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "doc-uuid-1",
      "name": "员工手册-v3.pdf",
      "status": "indexed",
      "progress": 100,
      "uploaded_at": "2026-06-10T14:00:00"
    },
    {
      "id": "doc-uuid-2",
      "name": "API设计规范.md",
      "status": "embedding",
      "progress": 65,
      "uploaded_at": "2026-06-10T14:30:00"
    }
  ]
}
```

**后端逻辑**: 查询该 KB 下按 `uploaded_at DESC` 排序的前 N 条文档记录。

---

### 5.5 文档标签页接口

#### 5.5.1 上传文档

```
POST /api/knowledge-bases/{kb_id}/documents/upload
Content-Type: multipart/form-data
```

**请求参数** (multipart):

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `files` | File[] | **是** | 一个或多个文件（单次最多 20 个） |

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "doc-uuid-1",
      "name": "员工手册-v3.pdf",
      "type": "pdf",
      "size_display": "2.4 MB",
      "status": "queued",
      "uploaded_at": "2026-06-11T10:00:00"
    }
  ]
}
```

**后端逻辑——文件存储**:
1. 接收上传文件列表，校验文件大小（单文件最大 100MB）、类型（白名单见 6.2 节）
2. 根据 `DOC_STORE_BACKEND` 配置选择存储：
   - `local`（默认）: 文件保存到 `{WORKSPACE}/docs_upload/{kb_id}/{doc_id}/{filename}`
   - `minio`（规划中，暂不实现）: 上传到 MinIO bucket，路径 `kb/{kb_id}/{doc_id}/{filename}`
3. 在 `knowledge_base_documents` 表中创建记录，status="queued"，storage_path 记录实际路径
4. **异步触发 RAG 索引流水线**（见第 6 章）
5. 更新知识库 `docs_count` 和 `size_bytes`
6. 返回文档信息列表

---

#### 5.5.2 获取文档列表

```
GET /api/knowledge-bases/{kb_id}/documents?page=1&page_size=20&search=&status=
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页条数 |
| `search` | string | 否 | 按文件名搜索 |
| `status` | string | 否 | 按状态筛选 |

**响应**:
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "doc-uuid-1",
        "name": "员工手册-v3.pdf",
        "type": "pdf",
        "size_display": "2.4 MB",
        "status": "indexed",
        "progress": 100,
        "chunks_count": 45,
        "entities_count": 12,
        "relations_count": 8,
        "uploaded_at": "2026-06-10T14:00:00",
        "indexed_at": "2026-06-10T14:05:00"
      }
    ],
    "total": 6,
    "page": 1,
    "page_size": 20
  }
}
```

---

#### 5.5.3 获取文档详情 + 索引流水线状态

```
GET /api/knowledge-bases/{kb_id}/documents/{doc_id}
```

**响应**: 相较于列表项，额外包含 `stages` 数组描述 8 个流水线阶段：

```json
{
  "id": "doc-uuid-1",
  "name": "员工手册-v3.pdf",
  "type": "pdf",
  "size_display": "2.4 MB",
  "status": "embedding",
  "progress": 62,
  "chunks_count": 45,
  "entities_count": 0,
  "relations_count": 0,
  "uploaded_at": "2026-06-10T14:00:00",
  "error_message": null,
  "stages": [
    { "name": "排队", "status": "done", "pct": 100 },
    { "name": "解析", "status": "done", "pct": 100 },
    { "name": "切片", "status": "done", "pct": 100 },
    { "name": "向量化", "status": "running", "pct": 45 },
    { "name": "BM25 倒排", "status": "pending", "pct": 0 },
    { "name": "实体抽取", "status": "pending", "pct": 0 },
    { "name": "关系抽取", "status": "pending", "pct": 0 },
    { "name": "入库", "status": "pending", "pct": 0 }
  ]
}
```

**后端逻辑**: 从 `knowledge_base_documents` 表读取文档记录，根据 status 和 progress 实时计算 stages 状态。

---

#### 5.5.4 删除文档

```
DELETE /api/knowledge-bases/{kb_id}/documents/{doc_id}
```

**后端逻辑**:
1. 在向量数据库中删除该文档的所有向量（按 `doc_id` 过滤删除）
2. 删除本地/对象存储中的源文件
3. 删除 `knowledge_base_entities` 和 `knowledge_base_relations` 中该文档贡献的记录（如有记录来源追踪）
4. 删除 `knowledge_base_documents` 记录
5. 更新知识库的计数字段

---

#### 5.5.5 重试失败文档

```
POST /api/knowledge-bases/{kb_id}/documents/{doc_id}/retry
```

**后端逻辑**:
1. 验证文档当前 status="failed"
2. 清理该文档的残留向量数据（如有）
3. 重置 status="queued"，progress=0，error_message=null
4. 重新触发 RAG 索引流水线

---

### 5.6 知识图谱标签页接口

#### 5.6.1 获取知识图谱数据

```
GET /api/knowledge-bases/{kb_id}/graph?entity_type=
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `entity_type` | string | 否 | 按实体类型筛选（人物/组织/产品/概念/算法/地点/时间/事件） |

**响应**:
```json
{
  "code": 0,
  "data": {
    "entities": [
      {
        "id": "ent-uuid-1",
        "name": "张三",
        "type": "人物",
        "mentions": 42
      }
    ],
    "relations": [
      {
        "id": "rel-uuid-1",
        "from": "张三",
        "to": "ke-hermes",
        "label": "开发",
        "weight": 1.0
      }
    ]
  }
}
```

**后端逻辑**:
1. 从 `knowledge_base_entities` 查询该 KB 的实体（可选 entity_type 筛选）
2. 从 `knowledge_base_relations` 查询该 KB 的关系
3. 按 `mentions DESC` 排序实体；按 `weight DESC` 排序关系
4. 前端需要 x/y 坐标 → 后端提供 mentions 计数，前端根据 mentions 计算布局位置（或返回固定布局坐标）

---

#### 5.6.2 获取实体详情

```
GET /api/knowledge-bases/{kb_id}/graph/entities/{entity_id}
```

**响应**: 实体详细信息 + 相关关系列表 + 提及该实体的文档片段

---

### 5.7 不被规划的接口（暂不实现）

以下功能虽然在 `KbSearchTab.vue`（检索）和 `KbConfigTab.vue`（索引配置）中有前端实现，但**不作为本版本后端开发范围**：

| 前端组件 | 对应功能 | 暂不实现原因 |
|----------|----------|--------------|
| `KbSearchTab.vue` | 混合检索/向量检索/BM25 检索 | 检索功能需要统一检索 API，依赖索引流水线先完成 |
| `KbConfigTab.vue` | 索引配置保存与重新索引 | 配置变更后的重新索引调度需在后续版本实现；创建时的初始配置通过 POST /knowledge-bases 完成 |

> 注意：`KbConfigTab.vue` 中的配置读取（GET）已在知识库详情接口中返回，前端可以直接展示当前配置。但配置的**更新保存**和**触发重新索引**暂不实现。

---

## 6. RAG 索引流水线详细设计

### 6.1 流水线总体流程

```
┌───────────────────────────────────────────────────────────────┐
│                     RAG Indexing Pipeline                     │
│                                                               │
│  Upload ──► Queue ──► Parse ──► Chunk ──► Embedding          │
│                                               │               │
│                                               ├──► BM25 Index │
│                                               │               │
│                                               └──► Entity     │
│                                                    Extract    │
│                                                      │        │
│                                                      └──►    │
│                                                    Relation   │
│                                                    Extract    │
│                                                      │        │
│  Indexed ◄── Store ◄────────────────────────────────┘        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**8 个阶段**: 排队 → 解析 → 切片 → 向量化 → BM25 倒排 → 实体抽取 → 关系抽取 → 入库

状态转换：
```
queued → parsing → chunking → embedding → bm25 → extracting → indexed
                      ↓                    ↓        ↓
                   failed               failed   failed
```

### 6.2 文档类型与加载器映射（阶段 2：解析）

根据文档 MIME 类型或后缀选择对应的加载器：

| 文档类型 | 后缀 | 加载器（优先） | 加载器（备选） | 来源 |
|----------|------|----------------|----------------|------|
| PDF | `.pdf` | `opendataloader_pdf.PDFLoader` | `langchain_community.document_loaders.PyPDFLoader` | langchain-opendataloader-pdf / langchain-community |
| Microsoft Word | `.docx` | `langchain_community.document_loaders.Docx2txtLoader` | `langchain_community.document_loaders.UnstructuredWordDocumentLoader` | langchain-community |
| Microsoft Excel | `.xlsx` | `langchain_community.document_loaders.UnstructuredExcelLoader` | — | langchain-community |
| Microsoft PowerPoint | `.pptx` | `langchain_community.document_loaders.UnstructuredPowerPointLoader` | — | langchain-community |
| CSV | `.csv` | `langchain_community.document_loaders.CSVLoader` | — | langchain-community |
| JSON | `.json` | `langchain_community.document_loaders.JSONLoader` | — | langchain-community |
| Markdown | `.md` | `langchain_community.document_loaders.UnstructuredMarkdownLoader` | — | langchain-community |
| HTML | `.html` | `langchain_community.document_loaders.UnstructuredHTMLLoader` | — | langchain-community |
| Text | `.txt` | `langchain_community.document_loaders.TextLoader` | — | langchain-community |
| 图片 | `.png/.jpg/.jpeg` | `langchain_community.document_loaders.UnstructuredImageLoader` | — | langchain-community |

**文档加载器——策略模式 (Strategy Pattern)**：

> **设计模式**: 策略模式 (Strategy Pattern)
> **基本原理**: 将每种文档类型的加载算法封装为独立的策略类（`DocumentLoaderStrategy`），通过注册表（`DocumentLoaderRegistry`）在运行时根据文件类型选择策略。PDF 等复杂类型通过 `FallbackStrategy` 组合多个策略形成优先级链。新增文档类型只需注册新策略类，无需修改已有代码（开闭原则）。

```python
# backend/src/core/rag/loaders.py

import importlib
import logging
from abc import ABC, abstractmethod
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 策略接口 (Strategy Interface)
# ══════════════════════════════════════════════════════════════

class DocumentLoaderStrategy(ABC):
    """文档加载策略抽象接口。

    每种文档类型对应一个具体的策略实现，封装该类型的加载细节。
    """

    @abstractmethod
    def load(self, file_path: str) -> list[Document]:
        """加载文档并返回 LangChain Document 列表。

        Args:
            file_path: 源文件路径

        Returns:
            解析后的 Document 对象列表

        Raises:
            Exception: 加载失败时抛出异常
        """
        ...


# ══════════════════════════════════════════════════════════════
# 具体策略实现 (Concrete Strategies)
# ══════════════════════════════════════════════════════════════

class PyPDFLoaderStrategy(DocumentLoaderStrategy):
    """PDF 加载——langchain_community PyPDFLoader（备选策略）。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import PyPDFLoader
        return PyPDFLoader(file_path).load()


class OpenDataLoaderPDFStrategy(DocumentLoaderStrategy):
    """PDF 加载——langchain-opendataloader-pdf（优先策略，更优的 PDF 解析能力）。"""

    def load(self, file_path: str) -> list[Document]:
        from opendataloader_pdf import PDFLoader
        return PDFLoader(file_path).load()


class DocxLoaderStrategy(DocumentLoaderStrategy):
    """Word 文档加载。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import Docx2txtLoader
        return Docx2txtLoader(file_path).load()


class UnstructuredExcelStrategy(DocumentLoaderStrategy):
    """Excel 表格加载。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import UnstructuredExcelLoader
        return UnstructuredExcelLoader(file_path).load()


class UnstructuredPPTStrategy(DocumentLoaderStrategy):
    """PowerPoint 演示文稿加载。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import UnstructuredPowerPointLoader
        return UnstructuredPowerPointLoader(file_path).load()


class CSVLoaderStrategy(DocumentLoaderStrategy):
    """CSV 表格加载。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import CSVLoader
        return CSVLoader(file_path).load()


class JSONLoaderStrategy(DocumentLoaderStrategy):
    """JSON 文件加载。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import JSONLoader
        return JSONLoader(file_path, jq_schema=".", text_content=False).load()


class MarkdownLoaderStrategy(DocumentLoaderStrategy):
    """Markdown 文件加载。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import UnstructuredMarkdownLoader
        return UnstructuredMarkdownLoader(file_path).load()


class HTMLLoaderStrategy(DocumentLoaderStrategy):
    """HTML 文件加载。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import UnstructuredHTMLLoader
        return UnstructuredHTMLLoader(file_path).load()


class TextLoaderStrategy(DocumentLoaderStrategy):
    """纯文本文件加载。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import TextLoader
        return TextLoader(file_path, encoding="utf-8").load()


class ImageLoaderStrategy(DocumentLoaderStrategy):
    """图片文件加载（OCR / 多模态）。"""

    def load(self, file_path: str) -> list[Document]:
        from langchain_community.document_loaders import UnstructuredImageLoader
        return UnstructuredImageLoader(file_path).load()


# ══════════════════════════════════════════════════════════════
# 组合策略——Fallback（容错降级）
# ══════════════════════════════════════════════════════════════

class FallbackLoaderStrategy(DocumentLoaderStrategy):
    """组合策略：按优先级链依次尝试多个加载器，返回第一个成功的结果。

    当优先策略因依赖缺失而失败时，自动降级到备选策略。

    Example:
        pdf_strategy = FallbackLoaderStrategy([
            OpenDataLoaderPDFStrategy(),   # 优先
            PyPDFLoaderStrategy(),         # 备选
        ])
    """

    def __init__(self, strategies: list[DocumentLoaderStrategy]):
        self._strategies = strategies

    def load(self, file_path: str) -> list[Document]:
        errors: list[str] = []
        for strategy in self._strategies:
            try:
                result = strategy.load(file_path)
                logger.info("Loader %s succeeded for %s", type(strategy).__name__, file_path)
                return result
            except Exception as e:
                errors.append(f"{type(strategy).__name__}: {e}")
                logger.debug("Loader %s failed: %s", type(strategy).__name__, e)

        raise ValueError(
            f"All loaders failed for '{file_path}'. Errors: {'; '.join(errors)}"
        )


# ══════════════════════════════════════════════════════════════
# 策略注册表 (Registry / Context)
# ══════════════════════════════════════════════════════════════

class DocumentLoaderRegistry:
    """文档加载策略注册表。

    负责维护"文件类型 → 加载策略"的映射关系。
    外部通过 register() 扩展新类型，通过 get_strategy() 获取策略实例。
    """

    def __init__(self):
        self._strategies: dict[str, DocumentLoaderStrategy] = {}

    def register(self, file_type: str, strategy: DocumentLoaderStrategy) -> None:
        """注册一个文件类型对应的加载策略。

        Args:
            file_type: 文件类型标识（pdf/docx/xlsx/...）
            strategy: 对应的加载策略实例
        """
        self._strategies[file_type] = strategy
        logger.debug("Registered loader strategy for '%s': %s", file_type, type(strategy).__name__)

    def get_strategy(self, file_type: str) -> DocumentLoaderStrategy:
        """获取指定文件类型的加载策略。

        Raises:
            ValueError: 文件类型未被注册
        """
        if file_type not in self._strategies:
            raise ValueError(f"Unsupported file type: {file_type}")
        return self._strategies[file_type]

    def load(self, file_path: str, file_type: str) -> list[Document]:
        """便捷方法：直接加载文档。"""
        strategy = self.get_strategy(file_type)
        return strategy.load(file_path)


# ══════════════════════════════════════════════════════════════
# 默认注册表构建（工厂函数）
# ══════════════════════════════════════════════════════════════

def create_default_loader_registry() -> DocumentLoaderRegistry:
    """创建预注册所有内置类型的加载器注册表。"""
    registry = DocumentLoaderRegistry()

    # PDF: 优先 opendataloader_pdf，备选 PyPDFLoader
    registry.register("pdf", FallbackLoaderStrategy([
        OpenDataLoaderPDFStrategy(),
        PyPDFLoaderStrategy(),
    ]))

    # Word: 优先 Docx2txt，备选 UnstructuredWord
    registry.register("docx", FallbackLoaderStrategy([
        DocxLoaderStrategy(),
        _make_unstructured_word_strategy(),
    ]))

    # 单策略类型
    registry.register("xlsx", UnstructuredExcelStrategy())
    registry.register("pptx", UnstructuredPPTStrategy())
    registry.register("csv", CSVLoaderStrategy())
    registry.register("json", JSONLoaderStrategy())
    registry.register("md", MarkdownLoaderStrategy())
    registry.register("html", HTMLLoaderStrategy())
    registry.register("txt", TextLoaderStrategy())

    # 图片类型共享同一策略
    image_strategy = ImageLoaderStrategy()
    for ft in ("png", "jpg", "jpeg"):
        registry.register(ft, image_strategy)

    return registry


def _make_unstructured_word_strategy() -> DocumentLoaderStrategy:
    """创建 UnstructuredWord 备选策略（需 unstructured 包）。"""

    class _UnstructuredWordStrategy(DocumentLoaderStrategy):
        def load(self, file_path: str) -> list[Document]:
            from langchain_community.document_loaders import UnstructuredWordDocumentLoader
            return UnstructuredWordDocumentLoader(file_path).load()

    return _UnstructuredWordStrategy()
```

> **扩展指南**: 若需新增一种文档格式（如 `.epub`），只需：
> 1. 实现 `DocumentLoaderStrategy` 子类
> 2. 调用 `registry.register("epub", EpubLoaderStrategy())`
> 现有代码无需任何修改。

### 6.3 文本切片器——策略模式 (Strategy Pattern)

对应前端定义的 5 种切片策略：

| 策略 | 切片器类 | 说明 |
|------|----------|------|
| `fixed` | `FixedChunkStrategy` | 按固定字符数硬切 |
| `recursive` | `RecursiveChunkStrategy` | 按段落→换行→句号递归切分 |
| `semantic` | `SemanticChunkStrategy` | 基于 embedding 向量相似度自动切分 |
| `markdown` | `MarkdownChunkStrategy` | 按 Markdown 标题层级切分 |
| `agentic` | `AgenticChunkStrategy` | LLM 判断主题边界 |

> **设计模式**: 策略模式 (Strategy Pattern)
> **基本原理**: 5 种切片算法各自封装为独立的 `ChunkStrategy` 子类，通过 `ChunkStrategyRegistry` 按策略名（如 "recursive"）查找执行策略。与文档加载器的策略模式结构一致，遵循"封装变化、面向接口编程"原则。前端新增切片策略时，后端只需新增一个策略类并注册到 Registry。

```python
# backend/src/core/rag/splitters.py

from abc import ABC, abstractmethod
from langchain_core.documents import Document
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    SemanticChunker,
)


# ══════════════════════════════════════════════════════════════
# 策略接口 (Strategy Interface)
# ══════════════════════════════════════════════════════════════

class ChunkStrategy(ABC):
    """文本切片策略抽象接口。

    每种切片算法封装为一个具体策略，统一接受 Document 列表并返回切片后的 Document 列表。
    """

    @abstractmethod
    def split(self, documents: list[Document]) -> list[Document]:
        """将文档列表切分为更小的分片。

        Args:
            documents: 待切分的 LangChain Document 列表

        Returns:
            切片后的 Document 列表（保留原始 metadata 并附加 chunk 序号）
        """
        ...


# ══════════════════════════════════════════════════════════════
# 具体策略实现 (Concrete Strategies)
# ══════════════════════════════════════════════════════════════

class FixedChunkStrategy(ChunkStrategy):
    """固定长度切片——按指定字符数硬切。"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        splitter = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )
        return splitter.split_documents(documents)


class RecursiveChunkStrategy(ChunkStrategy):
    """递归分隔符切片——按段落→换行→句号→空格优先级递归切分。"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        return splitter.split_documents(documents)


class SemanticChunkStrategy(ChunkStrategy):
    """语义切片——基于 embedding 向量相似度自动确定主题边界。

    Attributes:
        _embedding_model: Embedding 模型实例，用于计算句子向量相似度
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64,
                 embedding_model=None):
        if embedding_model is None:
            raise ValueError("SemanticChunkStrategy requires an embedding model")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._embedding_model = embedding_model

    def split(self, documents: list[Document]) -> list[Document]:
        splitter = SemanticChunker(
            embeddings=self._embedding_model,
            breakpoint_threshold_type="percentile",
        )
        return splitter.split_documents(documents)


class MarkdownChunkStrategy(ChunkStrategy):
    """Markdown 结构切片——按标题层级（H1/H2/H3）切分，保留文档结构。"""

    def split(self, documents: list[Document]) -> list[Document]:
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ],
            strip_headers=True,
        )
        results: list[Document] = []
        for doc in documents:
            chunks = splitter.split_text(doc.page_content)
            for i, chunk in enumerate(chunks):
                chunk.metadata.update(doc.metadata)
                chunk.metadata["chunk_index"] = i
            results.extend(chunks)
        return results


class AgenticChunkStrategy(ChunkStrategy):
    """Agentic 智能切片——调用 LLM 判断主题边界。

    将文档分段后请 LLM 标注语义边界，适合高质量但低吞吐场景。
    """

    def __init__(self, llm, chunk_size: int = 512, chunk_overlap: int = 64):
        self._llm = llm
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        # 分段后由 LLM 判断语义边界
        # 具体实现: 对每段文本发送 prompt "请判断以下文本的主题边界位置..."
        # 根据 LLM 返回的边界位置执行最终切分
        raise NotImplementedError("AgenticChunkStrategy: 将在后续版本实现")


# ══════════════════════════════════════════════════════════════
# 策略注册表 (Registry / Context)
# ══════════════════════════════════════════════════════════════

class ChunkStrategyRegistry:
    """切片策略注册表。

    维护"策略名 → 策略实例"的映射，按知识库索引配置在运行时选择策略。
    """

    def __init__(self):
        self._strategies: dict[str, ChunkStrategy] = {}

    def register(self, name: str, strategy: ChunkStrategy) -> None:
        """注册一个命名切片策略。"""
        self._strategies[name] = strategy

    def get(self, name: str) -> ChunkStrategy:
        """获取指定名称的切片策略。

        Raises:
            ValueError: 策略名未注册
        """
        if name not in self._strategies:
            raise ValueError(f"Unknown chunk strategy: {name}")
        return self._strategies[name]

    def split(self, name: str, documents: list[Document]) -> list[Document]:
        """便捷方法：使用指定策略切片。"""
        return self.get(name).split(documents)


# ══════════════════════════════════════════════════════════════
# 策略工厂——根据 IndexConfig 创建 Registry
# ══════════════════════════════════════════════════════════════

def create_chunk_registry(config: dict, embedding_model=None, llm=None) -> ChunkStrategyRegistry:
    """根据索引配置创建预注册所有策略的切片注册表。

    Args:
        config: IndexConfig 字典（含 chunk_size, chunk_overlap 等）
        embedding_model: Embedding 模型（semantic 策略需要）
        llm: LLM 实例（agentic 策略需要）

    Returns:
        已注册 fixed/recursive/semantic/markdown/agentic 五种策略的注册表
    """
    chunk_size = config.get("chunk_size", 512)
    chunk_overlap = config.get("chunk_overlap", 64)

    registry = ChunkStrategyRegistry()
    registry.register("fixed", FixedChunkStrategy(chunk_size, chunk_overlap))
    registry.register("recursive", RecursiveChunkStrategy(chunk_size, chunk_overlap))
    registry.register("semantic", SemanticChunkStrategy(chunk_size, chunk_overlap, embedding_model))
    registry.register("markdown", MarkdownChunkStrategy())
    registry.register("agentic", AgenticChunkStrategy(llm, chunk_size, chunk_overlap))

    return registry
```

### 6.4 Embedding 模型工厂（阶段 4：向量化）

```python
# backend/src/core/rag/embedding.py

from langchain_openai import OpenAIEmbeddings

def get_embedding_model(model_name: str, api_base: str, api_key: str) -> OpenAIEmbeddings:
    """获取 Embedding 模型实例。

    大多数 Embedding 模型（BGE、Qwen3-Embedding、Jina、DashScope text-embedding-v4）
    都兼容 OpenAI API 格式，统一使用 langchain_openai.OpenAIEmbeddings。

    Args:
        model_name: 模型名称
        api_base: API 地址
        api_key: API 密钥

    Returns:
        OpenAIEmbeddings 实例
    """
    return OpenAIEmbeddings(
        model=model_name,
        openai_api_base=api_base,
        openai_api_key=api_key,
    )
```

> **模型来源**: 从 `ai_models` 表中查询配置的 embedding 模型，获取其 provider 的 api_base 和 api_key（解密后）。

### 6.5 BM25 倒排索引（阶段 5）

BM25 索引通过 Milvus 的全文检索能力实现（Milvus 2.4+ 支持 BM25），或 Chroma 的全文搜索。

```python
# backend/src/core/rag/bm25_index.py

class BM25Indexer:
    """BM25 倒排索引管理。

    对 Milvus Collection 调用 BM25 函数索引创建，
    对 Chroma 使用内置全文检索。
    """

    def __init__(self, vector_store: "BaseVectorStore"):
        self._store = vector_store

    async def index(self, kb_id: str, documents: list[Document]) -> None:
        """为文档建立 BM25 索引。

        对于 Milvus: 调用 create_function("BM25") 或使用内置 BM25 索引
        对于 Chroma: 利用 Chroma 全文搜索能力
        """
        await self._store.add_bm25_index(kb_id, documents)

    async def search(self, kb_id: str, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """BM25 全文检索。

        Returns:
            [(chunk_id, bm25_score), ...] 按分数降序排列
        """
        return await self._store.bm25_search(kb_id, query, top_k)
```

> Milvus 2.4 原生支持 BM25 Function。在创建 Collection 时启用 Analyzer Function，并注册 BM25 Function；检索时通过 `BM25` function 打分。具体实现将在开发阶段根据 Milvus SDK 版本确定 API。

### 6.6 实体与关系抽取（阶段 6 & 7）

使用 **langextract** 框架进行实体抽取和关系抽取。

```python
# backend/src/api/knowledge_base/graph_service.py

from langextract import DocumentExtractor, EntityExtractor, RelationExtractor

class GraphExtractionService:
    """知识图谱抽取服务。

    使用 langextract 框架从文档分片中抽取实体和实体间关系。
    抽取结果存储到 langextract 内置存储（默认），
    或通过配置切换到 Neo4j（规划中，暂不实现）。
    """

    def __init__(self, llm, vector_store, graph_store_backend: str):
        self._llm = llm
        self._vector_store = vector_store
        self._backend = graph_store_backend

    async def extract_entities_and_relations(
        self, kb_id: str, doc_id: str, chunks: list[Document]
    ) -> tuple[list[dict], list[dict]]:
        """从文档分片中抽取实体和关系。

        Args:
            kb_id: 知识库 ID
            doc_id: 文档 ID
            chunks: 文档分片列表

        Returns:
            (entities, relations): 实体列表和关系列表
        """
        # 1. 使用 langextract.DocumentExtractor 处理文档
        doc_extractor = DocumentExtractor(llm=self._llm)

        # 2. 抽取实体
        entity_extractor = EntityExtractor(llm=self._llm)
        entities = await entity_extractor.aextract(chunks)

        # 3. 抽取关系
        relation_extractor = RelationExtractor(llm=self._llm)
        relations = await relation_extractor.aextract(chunks, entities=entities)

        # 4. 存储到 langextract 内置存储（或 Neo4j）
        if self._backend == "langextract":
            await self._store_to_langextract(kb_id, doc_id, entities, relations)
        elif self._backend == "neo4j":
            # 规划中，暂不实现
            pass

        return entities, relations

    async def _store_to_langextract(
        self, kb_id: str, doc_id: str, entities: list[dict], relations: list[dict]
    ) -> None:
        """将实体和关系存储到 langextract 框架的内置存储中。

        langextract 框架内部管理实体和关系的存储结构，
        通过其 API 进行查询。同时将元数据同步写到 SQL 表中以便前端快速列表展示。
        """
        # 同步元数据到 knowledge_base_entities 和 knowledge_base_relations 表
        ...
```

**设计要点**:
- langextract 框架负责实体/关系抽取的存储和查询核心逻辑
- 同时将实体/关系的元数据（名称、类型、提及次数、权重等）同步写入关系型数据库，供前端知识库列表统计和知识图谱 Tab 快速加载
- 详细抽取配置（实体类型定义、关系类型约束等）在 `langextract` 框架配置中管理
- Neo4j 切换能力：通过 `GRAPH_STORE_BACKEND` 环境变量配置，默认使用 `langextract` 内置存储

### 6.7 入库与完成（阶段 8）

所有阶段完成后：
1. 前 4 个阶段（解析、切片、向量化、BM25）: 数据写入向量数据库
2. 后 2 个阶段（实体抽取、关系抽取）: 数据写入 langextract 存储 + 关系型数据库同步
3. 更新文档状态为 "indexed"，记录 indexed_at
4. 更新知识库计数字段
5. 更新知识库状态为 "ready"（若该 KB 下无其他索引中文档）

### 6.8 文档状态机——状态模式 (State Pattern)

> **设计模式**: 状态模式 (State Pattern)
> **基本原理**: 文档在索引流水线中经历 8 种状态转换（queued→parsing→chunking→...→indexed/failed）。状态模式将每种状态的行为（进入/处理/退出/转换）封装为独立的 `DocState` 子类，上下文（`IndexingContext`）持有当前状态引用并委托执行。消除 `if status == "parsing": ... elif status == "chunking": ...` 的条件分支。

```
                  ┌─────────┐
                  │ queued  │
                  └────┬────┘
                       │ enqueue()
                  ┌────▼────┐
                  │ parsing │
                  └────┬────┘
                       │ parse_done()
                  ┌────▼────┐
                  │chunking │
                  └────┬────┘
                       │ chunk_done()
                  ┌────▼────┐        ┌────────┐
                  │embedding├───────►│ failed │  (任意阶段可进入)
                  └────┬────┘        └────────┘
                       │ embed_done()
                  ┌────▼────┐
                  │  bm25   │
                  └────┬────┘
                       │ bm25_done()
                  ┌────▼────┐
                  │extracting│
                  └────┬────┘
                       │ extract_done()
                  ┌────▼────┐
                  │ indexed │
                  └─────────┘
```

**状态转换规则**:

| 当前状态 | 允许的下一状态 | 触发条件 |
|----------|---------------|----------|
| `queued` | `parsing` | 调度器从队列中取出任务 |
| `parsing` | `chunking`, `failed` | 文档加载成功 / 异常 |
| `chunking` | `embedding`, `failed` | 切片完成 / 异常 |
| `embedding` | `bm25`, `failed` | 向量化完成 / 异常 |
| `bm25` | `extracting`, `failed` | BM25 索引完成 / 异常 |
| `extracting` | `indexed`, `failed` | 实体/关系抽取完成 / 异常 |
| `indexed` | — (终态) | — |
| `failed` | `queued` | 手动重试 |

```python
# backend/src/api/knowledge_base/doc_state.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Awaitable


# ══════════════════════════════════════════════════════════════
# 上下文——持有状态引用和共享数据
# ══════════════════════════════════════════════════════════════

@dataclass
class IndexingContext:
    """索引上下文——状态模式中的 Context 角色。

    持有当前文档的索引状态、阶段数据，以及各阶段的执行回调。
    状态对象通过 context 读写数据并触发状态转换。
    """
    doc_id: str
    kb_id: str
    file_path: str
    file_type: str
    config: dict

    # 当前状态
    current_state: "DocState | None" = None
    status: str = "queued"
    progress: int = 0
    error_message: str | None = None

    # 阶段产物（各状态执行后填充）
    documents: list = field(default_factory=list)       # 解析后
    chunks: list = field(default_factory=list)           # 切片后
    embeddings: list = field(default_factory=list)        # 向量化后

    # 回调——由外部注入，用于持久化状态变更和进度通知
    on_status_change: Callable[["IndexingContext"], Awaitable[None]] | None = None

    async def transition_to(self, state: "DocState", status: str, progress: int) -> None:
        """转换到新状态。

        Args:
            state: 目标状态对象
            status: 状态字符串（写入数据库）
            progress: 进度百分比 0-100
        """
        self.current_state = state
        self.status = status
        self.progress = progress
        if self.on_status_change:
            await self.on_status_change(self)

    async def fail(self, error: str) -> None:
        """进入失败状态。"""
        self.error_message = error
        await self.transition_to(FailedState(), "failed", -1)


# ══════════════════════════════════════════════════════════════
# 状态接口 (State Interface)
# ══════════════════════════════════════════════════════════════

class DocState(ABC):
    """文档索引状态抽象接口。

    每个具体状态封装该阶段的处理逻辑和状态转换规则。
    """

    @abstractmethod
    async def handle(self, ctx: IndexingContext, pipeline: "IndexingPipeline") -> None:
        """执行当前状态的处理逻辑。

        处理完成后通过 ctx.transition_to() 转换到下一状态。
        失败时通过 ctx.fail() 进入 FailedState。

        Args:
            ctx: 索引上下文（持有共享数据）
            pipeline: 索引流水线（提供各阶段的执行能力）
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """状态名称（对应数据库 status 字段）。"""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


# ══════════════════════════════════════════════════════════════
# 具体状态实现 (Concrete States)
# ══════════════════════════════════════════════════════════════

class QueuedState(DocState):
    """排队等待——初始状态，等待调度器分配资源。"""

    name = "queued"

    async def handle(self, ctx: IndexingContext, pipeline: "IndexingPipeline") -> None:
        await ctx.transition_to(ParsingState(), "parsing", 3)


class ParsingState(DocState):
    """文档解析——使用文档加载策略解析源文件。"""

    name = "parsing"

    async def handle(self, ctx: IndexingContext, pipeline: "IndexingPipeline") -> None:
        try:
            loader_registry = pipeline.loader_registry
            ctx.documents = loader_registry.load(ctx.file_path, ctx.file_type)
            await ctx.transition_to(ChunkingState(), "chunking", 15)
        except Exception as e:
            await ctx.fail(f"文档解析失败: {e}")


class ChunkingState(DocState):
    """文本切片——根据配置的策略将文档切分为分片。"""

    name = "chunking"

    async def handle(self, ctx: IndexingContext, pipeline: "IndexingPipeline") -> None:
        try:
            strategy_name = ctx.config.get("chunk_strategy", "recursive")
            chunk_registry = pipeline.chunk_registry
            ctx.chunks = chunk_registry.split(strategy_name, ctx.documents)
            await ctx.transition_to(EmbeddingState(), "embedding", 30)
        except Exception as e:
            await ctx.fail(f"文本切片失败: {e}")


class EmbeddingState(DocState):
    """向量化——调用 Embedding 模型将分片文本转换为稠密向量。"""

    name = "embedding"

    async def handle(self, ctx: IndexingContext, pipeline: "IndexingPipeline") -> None:
        try:
            texts = [chunk.page_content for chunk in ctx.chunks]
            ctx.embeddings = await pipeline.embedding_model.aembed_documents(texts)
            await ctx.transition_to(BM25State(), "bm25", 55)
        except Exception as e:
            await ctx.fail(f"向量化失败: {e}")


class BM25State(DocState):
    """BM25 倒排索引——将分片写入向量数据库，建立 BM25 稀疏索引。"""

    name = "bm25"

    async def handle(self, ctx: IndexingContext, pipeline: "IndexingPipeline") -> None:
        try:
            await pipeline.vector_store.add_documents(ctx.kb_id, ctx.chunks, ctx.embeddings)
            await ctx.transition_to(ExtractingState(), "extracting", 70)
        except Exception as e:
            await ctx.fail(f"BM25 索引失败: {e}")


class ExtractingState(DocState):
    """实体/关系抽取——使用 langextract 提取知识图谱数据。"""

    name = "extracting"

    async def handle(self, ctx: IndexingContext, pipeline: "IndexingPipeline") -> None:
        try:
            if ctx.config.get("enable_graph", True):
                await pipeline.graph_service.extract_entities_and_relations(
                    ctx.kb_id, ctx.doc_id, ctx.chunks
                )
            await ctx.transition_to(IndexedState(), "indexed", 100)
        except Exception as e:
            await ctx.fail(f"实体抽取失败: {e}")


class IndexedState(DocState):
    """索引完成——终态，文档已完整入库。"""

    name = "indexed"

    async def handle(self, ctx: IndexingContext, pipeline: "IndexingPipeline") -> None:
        # 终态，无后续操作
        pass


class FailedState(DocState):
    """索引失败——终态，记录错误信息，等待手动重试。"""

    name = "failed"

    async def handle(self, ctx: IndexingContext, pipeline: "IndexingPipeline") -> None:
        # 终态，记录日志即可
        pass
```

---

## 7. 向量数据库抽象层

### 7.0 向量数据库数据模型设计

向量数据库中每个知识库对应一个 Collection，每条记录存储一个文档分片（Chunk）的完整信息，包括向量、BM25 稀疏向量和元数据。

#### 7.0.1 Milvus Collection Schema

Collection 命名规则: `kb_{kb_id}`（例如 `kb_a1b2c3d4-e5f6-7890-abcd-ef1234567890`）

| 字段名 | 字段类型 | 约束 | 说明 |
|--------|----------|------|------|
| `id` | `VarChar(36)` | PK, auto_id=False | 分片主键，UUID v4，由后端生成 |
| `doc_id` | `VarChar(36)` | not null, indexed | 所属文档 ID，关联 `knowledge_base_documents.id`，用于按文档批量删除 |
| `kb_id` | `VarChar(36)` | not null, indexed | 所属知识库 ID（冗余，方便跨知识库操作） |
| `chunk_index` | `Int64` | not null | 分片在文档内的序号（从 0 开始），用于按原始顺序重组 |
| `chunk_text` | `VarChar(65535)` | not null, analyzer=zh | 分片全文（最大 65535 字符），启用中文分词分析器，供 BM25 检索 |
| `chunk_text_sparse` | `SparseFloatVector` | nullable | BM25 稀疏向量（由 Milvus BM25 Function 从 chunk_text 自动生成），用于混合检索 |
| `embedding` | `FloatVector(dim)` | not null, indexed | 稠密向量（维度由配置 `embedding_dim` 决定，默认 1024），索引类型 IVF_FLAT 或 HNSW |
| `doc_name` | `VarChar(256)` | not null | 文档名称（冗余，方便检索结果无需回表即可展示来源） |
| `doc_type` | `VarChar(16)` | not null | 文档类型（pdf/docx/md/...），方便检索时按类型过滤 |
| `metadata_` | `JSON` | default {} | 扩展元数据（页码、章节标题、自定义标签等） |
| `created_at` | `Int64` | not null | 创建时间（Unix 时间戳，毫秒） |

**索引策略**:

| 字段 | 索引类型 | 参数 | 说明 |
|------|----------|------|------|
| `embedding` | `IVF_FLAT` 或 `HNSW` | `nlist=128` / `M=16, efConstruction=200` | 稠密向量索引，HNSW 适合高召回场景，IVF_FLAT 适合大数据量 |
| `chunk_text_sparse` | `SPARSE_INVERTED_INDEX` | `drop_ratio_build=0.2` | 稀疏向量索引，供 BM25 混合检索 |
| `id` | 主键索引 | — | Milvus 自动创建 |
| `doc_id` | 标量索引 | `index_type=INVERTED` | 按文档 ID 快速过滤/删除 |
| `kb_id` | 标量索引 | `index_type=INVERTED` | 按知识库快速过滤 |

**BM25 Function 注册**:

```python
from pymilvus import Function, FunctionType, Collection

# 在创建 Collection 后注册 BM25 Function，自动从 chunk_text 生成 chunk_text_sparse
bm25_fn = Function(
    name="bm25",
    function_type=FunctionType.BM25,
    input_field_names=["chunk_text"],
    output_field_names=["chunk_text_sparse"],
)
collection.create_function(bm25_fn)
```

> **说明**: Milvus 2.4+ 原生支持 BM25 Function — 写入 `chunk_text` 时自动计算并填充 `chunk_text_sparse` 稀疏向量，检索时直接用 BM25 分词打分。这避免了在应用层自行维护倒排索引。

**创建 Collection 完整示例**:

```python
from pymilvus import (
    Collection, CollectionSchema, DataType, FieldSchema,
    Function, FunctionType, MilvusClient, connections,
)

def create_kb_collection(kb_id: str, dim: int) -> None:
    """为知识库创建 Milvus Collection。"""
    collection_name = f"kb_{kb_id}"

    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=36),
        FieldSchema(name="kb_id", dtype=DataType.VARCHAR, max_length=36),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535,
                    analyzer_params={"type": "chinese"}),
        FieldSchema(name="chunk_text_sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="metadata_", dtype=DataType.JSON),
        FieldSchema(name="created_at", dtype=DataType.INT64),
    ]

    schema = CollectionSchema(fields=fields, description=f"Knowledge base: {kb_id}")
    collection = Collection(name=collection_name, schema=schema)

    # 注册 BM25 函数，自动从 chunk_text 生成 chunk_text_sparse
    bm25_fn = Function(
        name="bm25",
        function_type=FunctionType.BM25,
        input_field_names=["chunk_text"],
        output_field_names=["chunk_text_sparse"],
    )
    collection.create_function(bm25_fn)

    # 为 embedding 字段创建稠密向量索引
    index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {"M": 16, "efConstruction": 200},
    }
    collection.create_index(field_name="embedding", index_params=index_params)

    # 为 chunk_text_sparse 创建稀疏向量索引
    sparse_index_params = {
        "metric_type": "BM25",
        "index_type": "SPARSE_INVERTED_INDEX",
        "params": {"drop_ratio_build": 0.2},
    }
    collection.create_index(field_name="chunk_text_sparse", index_params=sparse_index_params)

    # 标量索引
    for field_name in ["doc_id", "kb_id"]:
        collection.create_index(
            field_name=field_name,
            index_params={"index_type": "INVERTED"},
        )
```

#### 7.0.2 Chroma Collection Schema

Chroma 的数据模型是基于 Document + Metadata + Embedding 的扁平结构（无固定 Schema），通过 metadatas 字典存储标量字段。

命名规则: `kb_{kb_id}`（与 Milvus 保持一致）

| 逻辑字段 | Chroma 映射方式 | 说明 |
|----------|-----------------|------|
| `id` | `ids` 参数 | 分片主键 UUID |
| `doc_id` | `metadatas["doc_id"]` | 所属文档 ID |
| `kb_id` | `metadatas["kb_id"]` | 所属知识库 ID |
| `chunk_index` | `metadatas["chunk_index"]` | 分片序号（int） |
| `chunk_text` | `documents` 参数 | 分片全文（用于 BM25 全文检索） |
| `embedding` | `embeddings` 参数 | 稠密向量 |
| `doc_name` | `metadatas["doc_name"]` | 文档名称 |
| `doc_type` | `metadatas["doc_type"]` | 文档类型 |
| `metadata_` | `metadatas["metadata_"]` | 扩展元数据（JSON 序列化为 string） |
| `created_at` | `metadatas["created_at"]` | 创建时间戳（int，毫秒） |

> **Chroma BM25 说明**: Chroma 0.5+ 支持 `full_text_search`。写入时将 `chunk_text` 作为 Chroma Document 的 `documents` 参数传入（Chroma 内部会自动构建全文索引），检索时通过 `where_document` 进行关键词搜索。Chroma 没有独立的稀疏向量字段，BM25 由其内置全文检索引擎实现，不依赖 BM25 Function。

#### 7.0.3 Chunk 写入数据对象

应用层与向量数据库之间传递的数据对象，屏蔽底层差异：

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChunkRecord:
    """写入向量数据库的 Chunk 数据对象。"""
    id: str                          # 分片 UUID
    doc_id: str                      # 文档 ID
    kb_id: str                       # 知识库 ID
    chunk_index: int                 # 序号
    chunk_text: str                  # 分片全文
    embedding: list[float]           # 稠密向量
    doc_name: str                    # 文档名称
    doc_type: str                    # 文档类型
    metadata_: dict = field(default_factory=dict)  # 扩展元数据
    created_at: int = field(         # Unix 毫秒
        default_factory=lambda: int(datetime.now().timestamp() * 1000)
    )
```

#### 7.0.4 向量数据库切换时的行为差异

| 能力 | Milvus | Chroma |
|------|--------|--------|
| 稠密向量索引 | HNSW / IVF_FLAT / IVF_SQ8 等 | HNSW（默认） |
| BM25 检索 | 原生 BM25 Function（带分词器配置） | 内置全文搜索（full_text_search） |
| 混合检索 | 原生支持 `hybrid_search`（稠密+稀疏分数融合） | 需应用层自行将两种分数融合 |
| 标量过滤 | 原生 `filter` 表达式（`doc_id == "xxx"`） | `where` 条件（`{"doc_id": "xxx"}`） |
| 按文档删除 | `delete(expr="doc_id == 'xxx'")` | `collection.delete(where={"doc_id": "xxx"})` |
| 分区管理 | 支持 Partition | 不支持，用不同 Collection 模拟 |
| 连接认证 | 支持 user/password + TLS | HTTP Basic Auth（Chroma 服务端模式） |

> **混合检索兼容方案**: 对于 Chroma，应用层通过两步实现混合检索——(1) 调用 `similarity_search_with_score` 获取向量分数；(2) 调用 Chroma 全文搜索获取 BM25 分数；(3) 两路分数按 `alpha` 参数加权融合后重排 Top-K。这封装在 `ChromaVectorStore.hybrid_search()` 方法内部。

#### 7.0.5 Collection 构建器——建造者模式 (Builder Pattern)

> **设计模式**: 建造者模式 (Builder Pattern)
> **基本原理**: Milvus Collection 的创建涉及 11 个字段定义、2 个向量索引配置、BM25 Function 注册、标量索引设置——参数多、步骤复杂、构造顺序有约束。`CollectionBuilder` 将"构建过程"（field → schema → index → function）与"最终产物"（Collection 实例）分离，提供链式调用让调用方按步骤清晰构建，避免构造函数参数爆炸。

```python
# backend/src/core/rag/collection_builder.py

from pymilvus import (
    Collection, CollectionSchema, DataType, FieldSchema,
    Function, FunctionType,
)


class CollectionBuilder:
    """Milvus Collection 建造者。

    链式调用构建 Collection，隐藏字段定义、索引创建、函数注册的复杂性。

    Usage:
        collection = (
            CollectionBuilder(kb_id, dim=1024)
            .add_common_fields()
            .add_vector_field()
            .add_sparse_vector_field()
            .create_schema()
            .create_collection()
            .register_bm25_function()
            .create_vector_index()
            .create_sparse_index()
            .create_scalar_indices()
            .build()
        )
    """

    def __init__(self, kb_id: str, dim: int):
        self._kb_id = kb_id
        self._collection_name = f"kb_{kb_id}"
        self._dim = dim
        self._fields: list[FieldSchema] = []
        self._schema: CollectionSchema | None = None
        self._collection: Collection | None = None

    def add_common_fields(self) -> "CollectionBuilder":
        """添加非向量通用字段。"""
        self._fields.extend([
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(name="kb_id", dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535,
                        analyzer_params={"type": "chinese"}),
            FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=16),
            FieldSchema(name="metadata_", dtype=DataType.JSON),
            FieldSchema(name="created_at", dtype=DataType.INT64),
        ])
        return self

    def add_vector_field(self) -> "CollectionBuilder":
        """添加稠密向量字段（embedding）。"""
        self._fields.append(
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self._dim),
        )
        return self

    def add_sparse_vector_field(self) -> "CollectionBuilder":
        """添加稀疏向量字段（BM25）。"""
        self._fields.append(
            FieldSchema(name="chunk_text_sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
        )
        return self

    def create_schema(self) -> "CollectionBuilder":
        """按当前字段列表构建 CollectionSchema。"""
        self._schema = CollectionSchema(
            fields=self._fields,
            description=f"Knowledge base: {self._kb_id}",
        )
        return self

    def create_collection(self) -> "CollectionBuilder":
        """用 Schema 创建 Collection 实例。"""
        if self._schema is None:
            raise ValueError("Must call create_schema() before create_collection()")
        self._collection = Collection(name=self._collection_name, schema=self._schema)
        return self

    def register_bm25_function(self) -> "CollectionBuilder":
        """注册 BM25 Function（chunk_text → chunk_text_sparse）。"""
        if self._collection is None:
            raise ValueError("Must call create_collection() before register_bm25_function()")
        bm25_fn = Function(
            name="bm25",
            function_type=FunctionType.BM25,
            input_field_names=["chunk_text"],
            output_field_names=["chunk_text_sparse"],
        )
        self._collection.create_function(bm25_fn)
        return self

    def create_vector_index(self, metric: str = "COSINE") -> "CollectionBuilder":
        """为 embedding 字段创建稠密向量索引（HNSW）。"""
        if self._collection is None:
            raise ValueError("Must call create_collection() before create_vector_index()")
        self._collection.create_index(
            field_name="embedding",
            index_params={
                "metric_type": metric,
                "index_type": "HNSW",
                "params": {"M": 16, "efConstruction": 200},
            },
        )
        return self

    def create_sparse_index(self) -> "CollectionBuilder":
        """为 chunk_text_sparse 字段创建稀疏向量索引。"""
        if self._collection is None:
            raise ValueError("Must call create_collection() before create_sparse_index()")
        self._collection.create_index(
            field_name="chunk_text_sparse",
            index_params={
                "metric_type": "BM25",
                "index_type": "SPARSE_INVERTED_INDEX",
                "params": {"drop_ratio_build": 0.2},
            },
        )
        return self

    def create_scalar_indices(self) -> "CollectionBuilder":
        """为 doc_id / kb_id 创建标量索引。"""
        if self._collection is None:
            raise ValueError("Must call create_collection() before create_scalar_indices()")
        for field_name in ["doc_id", "kb_id"]:
            self._collection.create_index(
                field_name=field_name,
                index_params={"index_type": "INVERTED"},
            )
        return self

    def build(self) -> Collection:
        """返回构建完成的 Milvus Collection 实例。"""
        if self._collection is None:
            raise ValueError("Must call create_collection() before build()")
        return self._collection
```



---

### 7.1 接口定义

```python
# backend/src/core/rag/vector_store.py

from abc import ABC, abstractmethod
from langchain_core.documents import Document


class BaseVectorStore(ABC):
    """向量数据库抽象接口。

    统一 Milvus 和 Chroma 的操作接口，支持向量检索和 BM25 全文检索。
    """

    @abstractmethod
    async def create_collection(self, kb_id: str, dim: int, enable_bm25: bool) -> None:
        """为知识库创建 Collection。

        Args:
            kb_id: 知识库 ID
            dim: Embedding 向量维度
            enable_bm25: 是否启用 BM25 索引
        """

    @abstractmethod
    async def delete_collection(self, kb_id: str) -> None:
        """删除知识库对应的 Collection。"""

    @abstractmethod
    async def add_documents(
        self, kb_id: str, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        """将文档向量写入向量数据库。

        Returns:
            写入的 chunk ID 列表
        """

    @abstractmethod
    async def delete_by_doc_id(self, kb_id: str, doc_id: str) -> None:
        """按文档 ID 删除所有相关向量。"""

    @abstractmethod
    async def similarity_search(
        self, kb_id: str, query_embedding: list[float], top_k: int
    ) -> list[tuple[str, float]]:
        """向量相似度搜索。"""

    @abstractmethod
    async def bm25_search(
        self, kb_id: str, query: str, top_k: int
    ) -> list[tuple[str, float]]:
        """BM25 全文搜索。"""

    @abstractmethod
    async def hybrid_search(
        self, kb_id: str, query: str, query_embedding: list[float],
        top_k: int, alpha: float
    ) -> list[tuple[str, float]]:
        """混合搜索（向量 + BM25）。

        Args:
            alpha: 向量搜索权重（0=纯BM25, 1=纯向量）
        """
```

### 7.2 Milvus 实现

```python
class MilvusVectorStore(BaseVectorStore):
    """基于 Milvus 的向量数据库实现。

    使用 pymilvus SDK，Collection 命名规则: kb_{kb_id}
    每个 Collection 包含字段: id (PK), doc_id, chunk_text, embedding (vector), bm25_sparse (sparse vector)
    """

    def __init__(self, uri: str, user: str, password: str, db_name: str):
        ...

    async def create_collection(self, kb_id: str, dim: int, enable_bm25: bool) -> None:
        """创建 Milvus Collection，schema 含 embedding (FLOAT_VECTOR) 和
        可选的 sparse vector 字段（用于 BM25）。"""

    async def bm25_search(self, kb_id: str, query: str, top_k: int) -> list[tuple[str, float]]:
        """通过 Milvus BM25 Function 对原始文本做 BM25 检索，返回分片 ID 和分数。"""
```

### 7.3 Chroma 实现

```python
class ChromaVectorStore(BaseVectorStore):
    """基于 Chroma 的向量数据库实现。

    使用 langchain_chroma.Chroma，每个知识库对应一个 Collection。
    """

    def __init__(self, host: str, port: int, persist_dir: str):
        ...

    async def bm25_search(self, kb_id: str, query: str, top_k: int) -> list[tuple[str, float]]:
        """Chroma 的 BM25 通过其全文搜索能力实现（Chroma 0.5+ 支持的 full-text search）。"""
```

### 7.4 工厂函数

```python
def create_vector_store(settings) -> BaseVectorStore:
    """根据配置创建向量数据库实例。"""
    if settings.vector_db_backend == "milvus":
        return MilvusVectorStore(
            uri=settings.milvus_uri,
            user=settings.milvus_user,
            password=settings.milvus_password,
            db_name=settings.milvus_default_db,
        )
    elif settings.vector_db_backend == "chroma":
        return ChromaVectorStore(
            host=settings.chroma_host,
            port=settings.chroma_port,
            persist_dir=settings.chroma_persist_dir,
        )
    else:
        raise ValueError(f"Unsupported vector DB backend: {settings.vector_db_backend}")
```

---

## 8. 后台索引任务调度

### 8.1 设计思路

索引流水线涉及 3 个设计模式的组合使用：

| 模式 | 应用场景 | 职责 |
|------|----------|------|
| **模板方法模式** | `IndexingPipeline` 定义 8 阶段执行骨架 | 固定阶段顺序，子步骤可替换 |
| **观察者模式** | 进度推送给 DB、SSE、日志等订阅者 | 解耦进度产生者与消费者 |
| **单例模式** | `IndexingScheduler` 全局唯一调度器 | 保证任务队列和并发控制集中管理 |

1. 文档上传后，在数据库中标记 status="queued"
2. 后台 `IndexingScheduler`（单例）按 FIFO 顺序从队列中取任务
3. 每个任务通过 `IndexingPipeline`（模板方法）执行 8 阶段，状态转换委托给状态模式（见 6.8 节）
4. 进度变更通过观察者模式通知所有订阅者（数据库持久化 + SSE 推送 + 日志）
5. 通过 `indexing_max_concurrent` 配置控制最大并发数

### 8.2 模板方法模式——IndexingPipeline

> **设计模式**: 模板方法模式 (Template Method Pattern)
> **基本原理**: `IndexingPipeline.execute()` 为模板方法，定义流水线的 8 阶段执行骨架和调用顺序；每个阶段的具体行为通过钩子方法（`_do_parse / _do_chunk / ...`）实现，子类可覆写以定制特定阶段的行为；错误处理由 `_on_error` 钩子统一接管。

```python
# backend/src/api/knowledge_base/doc_service.py

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field

from langchain_core.documents import Document

from api.knowledge_base.doc_state import IndexingContext, DocState, QueuedState

logger = logging.getLogger(__name__)


@dataclass
class IndexingTask:
    """索引任务（命令模式中的 Command 对象）。"""
    kb_id: str
    doc_id: str
    file_path: str
    file_type: str
    config: dict  # IndexConfig


# ══════════════════════════════════════════════════════════════
# 观察者接口 (Observer Pattern)
# ══════════════════════════════════════════════════════════════

class ProgressObserver(ABC):
    """索引进度观察者抽象接口。

    每个观察者订阅索引流水线的进度变更事件。
    """

    @abstractmethod
    async def on_progress(self, ctx: IndexingContext) -> None:
        """收到进度变更通知。

        Args:
            ctx: 当前索引上下文，包含 doc_id/status/progress/stages 等信息
        """
        ...


class DatabaseProgressObserver(ProgressObserver):
    """数据库进度观察者——将进度写入 knowledge_base_documents 表。"""

    def __init__(self, db_session_factory):
        self._db_factory = db_session_factory

    async def on_progress(self, ctx: IndexingContext) -> None:
        async with self._db_factory() as db:
            from sqlalchemy import select, update
            from db.models.knowledge_base_document import KnowledgeBaseDocument

            stmt = (
                update(KnowledgeBaseDocument)
                .where(KnowledgeBaseDocument.id == ctx.doc_id)
                .values(
                    status=ctx.status,
                    progress=ctx.progress,
                    error_message=ctx.error_message,
                    chunks_count=len(ctx.chunks),
                )
            )
            await db.execute(stmt)
            await db.commit()


class LoggingProgressObserver(ProgressObserver):
    """日志进度观察者——记录索引各阶段日志。"""

    async def on_progress(self, ctx: IndexingContext) -> None:
        stage_name = ctx.current_state.name if ctx.current_state else "unknown"
        logger.info(
            "Doc %s: status=%s progress=%d%% stage=%s",
            ctx.doc_id, ctx.status, ctx.progress, stage_name,
        )


# ══════════════════════════════════════════════════════════════
# 模板方法——IndexingPipeline (Template Method Pattern)
# ══════════════════════════════════════════════════════════════

class IndexingPipeline:
    """索引流水线——模板方法模式中的 AbstractClass 角色。

    定义 8 阶段索引执行的骨架算法:
      排队 → 解析 → 切片 → 向量化 → BM25 → 实体抽取 → 关系抽取 → 入库

    每个阶段通过状态模式委托给对应的 DocState 处理（见 6.8 节），
    进度变更通过观察者模式通知所有订阅者。
    """

    def __init__(
        self,
        loader_registry,         # DocumentLoaderRegistry（策略模式）
        chunk_registry,          # ChunkStrategyRegistry（策略模式）
        embedding_model,         # Embedding 模型
        vector_store,            # BaseVectorStore（策略模式）
        graph_service,           # GraphExtractionService
    ):
        self.loader_registry = loader_registry
        self.chunk_registry = chunk_registry
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.graph_service = graph_service

        # 观察者列表
        self._observers: list[ProgressObserver] = []

    # ── 观察者管理 ──

    def attach(self, observer: ProgressObserver) -> None:
        """注册进度观察者。"""
        self._observers.append(observer)

    def detach(self, observer: ProgressObserver) -> None:
        """移除进度观察者。"""
        self._observers.remove(observer)

    async def _notify(self, ctx: IndexingContext) -> None:
        """通知所有观察者。"""
        for observer in self._observers:
            try:
                await observer.on_progress(ctx)
            except Exception as e:
                logger.error("Observer %s failed: %s", type(observer).__name__, e)

    # ── 模板方法 (Template Method) ──

    async def execute(self, task: IndexingTask) -> None:
        """**模板方法**——定义 8 阶段索引骨架。

        子类可覆写 _on_start / _on_complete / _on_error 钩子以定制行为。
        每个阶段的具体处理委托给状态模式中的 DocState 对象。
        """
        ctx = IndexingContext(
            doc_id=task.doc_id,
            kb_id=task.kb_id,
            file_path=task.file_path,
            file_type=task.file_type,
            config=task.config,
            current_state=QueuedState(),
            status="queued",
            progress=0,
        )

        # 注入状态变更回调——触发观察者通知
        async def _on_status_change(c: IndexingContext) -> None:
            await self._notify(c)

        ctx.on_status_change = _on_status_change

        await self._on_start(ctx)
        try:
            # 按状态顺序执行，每个状态完成后自动转换到下一状态
            await self._run_state_machine(ctx)
            await self._on_complete(ctx)
        except Exception as e:
            logger.exception("Pipeline failed for doc %s", task.doc_id)
            await self._on_error(ctx, e)

    async def _run_state_machine(self, ctx: IndexingContext) -> None:
        """驱动状态机：依次执行每个状态，直到进入终态。

        状态对象（见 6.8 节）负责处理当前阶段并在完成后调用
        ctx.transition_to() 转换到下一状态。
        """
        while ctx.current_state is not None:
            state = ctx.current_state
            await state.handle(ctx, self)

            # 检查终态
            if ctx.status in ("indexed", "failed"):
                break

    # ── 钩子方法 (Hook Methods) ──

    async def _on_start(self, ctx: IndexingContext) -> None:
        """钩子——流水线开始。默认通知进度。"""
        await self._notify(ctx)

    async def _on_complete(self, ctx: IndexingContext) -> None:
        """钩子——流水线成功完成。默认通知进度 + 更新知识库计数。"""
        await self._notify(ctx)

    async def _on_error(self, ctx: IndexingContext, error: Exception) -> None:
        """钩子——流水线发生错误。默认进入失败状态并通知。"""
        await ctx.fail(str(error))
        await self._notify(ctx)


# ══════════════════════════════════════════════════════════════
# 调度器——单例模式 (Singleton Pattern)
# ══════════════════════════════════════════════════════════════

class IndexingScheduler:
    """索引任务调度器（单例）。

    职责：
    - 维护 FIFO 任务队列
    - 控制并发数量（Semaphore）
    - 为每个任务创建 IndexingPipeline 并执行
    """

    _instance: "IndexingScheduler | None" = None

    def __new__(cls, *args, **kwargs) -> "IndexingScheduler":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        pipeline: IndexingPipeline | None = None,
        max_concurrent: int = 3,
    ):
        if self._initialized:
            return
        self._initialized = True

        self._pipeline = pipeline
        self._queue: deque[IndexingTask] = deque()
        self._running: dict[str, asyncio.Task] = {}
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    @classmethod
    def instance(cls) -> "IndexingScheduler | None":
        """获取单例实例。"""
        return cls._instance

    async def enqueue(self, task: IndexingTask) -> None:
        """将任务加入 FIFO 队列并尝试启动。"""
        self._queue.append(task)
        logger.info("Task enqueued: doc=%s, queue_size=%d", task.doc_id, len(self._queue))
        await self._try_start_next()

    async def _try_start_next(self) -> None:
        """尝试从队列中取出下一个任务并启动。"""
        if not self._queue:
            return
        if len(self._running) >= self._max_concurrent:
            return

        task = self._queue.popleft()
        async_task = asyncio.create_task(self._pipeline.execute(task))
        self._running[task.doc_id] = async_task
        async_task.add_done_callback(lambda _: self._on_task_done(task.doc_id))

    def _on_task_done(self, doc_id: str) -> None:
        """任务完成回调——清理并启动下一个。"""
        self._running.pop(doc_id, None)
        asyncio.create_task(self._try_start_next())

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    @property
    def running_count(self) -> int:
        return len(self._running)
```

### 8.3 生命周期管理

- 在 `server.py` 的 `lifespan` 中创建 `IndexingScheduler` 单例
- 应用关闭时优雅停止：等待当前运行的任务完成，队列中未执行的任务保留到数据库中（下次启动时扫描 status="queued" 的文档自动恢复）

---

## 9. 前端 API 服务改造指引

### 9.1 knowledgeBaseApi.ts 改造

将 `frontend/src/services/knowledgeBaseApi.ts` 中的 Mock 实现替换为真实 HTTP 调用，遵循项目现有的 Axios 实例模式：

```typescript
// frontend/src/services/knowledgeBaseApi.ts

import request from './request'
import type { ApiResponse, PaginatedResponse } from '@/types/common'
import type { KB, KBDoc, Entity, Relation, SearchResult, CreateKBRequest, IndexConfig } from '@/types/knowledgeBase'

// 知识库 CRUD
export function fetchKnowledgeBases(params: { page?: number; page_size?: number; search?: string }) {
  return request.get<ApiResponse<PaginatedResponse<KB>>>('/knowledge-bases', { params })
}

export function fetchStats() {
  return request.get<ApiResponse<KBStats>>('/knowledge-bases/stats')
}

export function createKnowledgeBase(data: CreateKBRequest) {
  return request.post<ApiResponse<KB>>('/knowledge-bases', data)
}

export function fetchKnowledgeBase(id: string) {
  return request.get<ApiResponse<KB>>(`/knowledge-bases/${id}`)
}

export function updateKnowledgeBase(id: string, data: Partial<CreateKBRequest>) {
  return request.put<ApiResponse<KB>>(`/knowledge-bases/${id}`, data)
}

export function deleteKnowledgeBase(id: string) {
  return request.delete<ApiResponse<null>>(`/knowledge-bases/${id}`)
}

// 文档管理
export function uploadDocuments(kbId: string, files: File[]) {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  return request.post<ApiResponse<KBDoc[]>>(`/knowledge-bases/${kbId}/documents/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function fetchDocumentList(kbId: string, params?: { page?: number; page_size?: number; search?: string; status?: string }) {
  return request.get<ApiResponse<PaginatedResponse<KBDoc>>>(`/knowledge-bases/${kbId}/documents`, { params })
}

export function fetchDocumentDetail(kbId: string, docId: string) {
  return request.get<ApiResponse<KBDoc>>(`/knowledge-bases/${kbId}/documents/${docId}`)
}

export function deleteDocument(kbId: string, docId: string) {
  return request.delete<ApiResponse<null>>(`/knowledge-bases/${kbId}/documents/${docId}`)
}

export function retryDocument(kbId: string, docId: string) {
  return request.post<ApiResponse<KBDoc>>(`/knowledge-bases/${kbId}/documents/${docId}/retry`)
}

// 知识图谱
export function fetchGraphData(kbId: string, entityType?: string) {
  return request.get<ApiResponse<{ entities: Entity[]; relations: Relation[] }>>(`/knowledge-bases/${kbId}/graph`, { params: { entity_type: entityType } })
}

// 索引活动
export function fetchIndexingActivity(kbId: string, limit?: number) {
  return request.get<ApiResponse<KBDoc[]>>(`/knowledge-bases/${kbId}/indexing-activity`, { params: { limit } })
}
```

### 9.2 Store 改造

`knowledgeBase.ts` 中的 Pinia store 需要：
1. 移除索引进度模拟动画逻辑（`startIndexAnimation` / `stopIndexAnimation`）
2. 添加轮询机制或 WebSocket 监听索引进度变化（推荐使用 5 秒轮询作为简单方案，或 SSE 推送）
3. 移除通过数组操作修改本地数据的逻辑，改为每次操作后重新拉取列表

---

## 10. 实施计划

### 10.1 开发阶段

| 阶段 | 内容 | 预估工作量 |
|------|------|-----------|
| **Phase 1** | 数据库模型 + 知识库 CRUD API | ORM 模型 3 个 + API 路由 5 个 |
| **Phase 2** | 向量数据库抽象层 + Milvus 连接 | vector_store.py + embedding.py + 配置 |
| **Phase 3** | 文档上传 + 文档加载器工厂 | doc_api.py + loaders.py + splitters.py |
| **Phase 4** | RAG 索引流水线（解析→切片→向量→BM25） | doc_service.py + bm25_index.py |
| **Phase 5** | 实体/关系抽取 + 知识图谱 API | graph_service.py + graph_api.py |
| **Phase 6** | 概览统计 + 索引活动 API | kb_api.py 统计接口补充 |
| **Phase 7** | 前端 API 对接 & 联调 | knowledgeBaseApi.ts 改造 + Store 改造 |
| **后续版本** | 检索功能 + 索引配置更新 + MinIO + Neo4j | 另行规划 |

### 10.2 依赖项

需在 `pyproject.toml` 中新增的依赖：

```toml
[project]
dependencies = [
    "pymilvus>=2.4",                     # Milvus Python SDK
    "langchain-chroma>=0.2",             # Chroma 向量存储
    "langchain-community>=0.3",          # 文档加载器集合
    "langchain-text-splitters>=0.3",     # 文本切片器
    "unstructured>=0.16",                # Unstructured 文档解析
    "langchain-opendataloader-pdf>=0.1",   # PDF 文档加载器（优先使用）
    "langextract>=0.1",                  # 实体/关系抽取框架
]
```

> 注意: `langextract` 为当前项目中规划使用的框架名称，实际开发阶段根据该框架的实际 pip 包名和 API 进行调整。若该框架不可用，备选方案为 `langchain-experimental` 的 GraphRAG 工具链或自建 LLM-based 抽取。

### 10.3 风险与降级

| 风险 | 降级方案 |
|------|----------|
| Milvus 不可用 | 自动降级到 Chroma（通过 `VECTOR_DB_BACKEND` 切换） |
| langextract 框架不成熟 | 使用 LLM prompt-based 实体抽取 + 关系型数据库直接存储（绕过 langextract） |
| 大文件索引超时 | 前端展示进度条，后台异步处理；大文件（>50MB）自动拒绝 |
| Embedding 模型不可用 | 返回明确错误，阻止索引任务启动 |
| BM25 在某向量数据库不支持 | 对不支持的数据库降级为纯向量检索，日志记录警告 |

---

## 附录 A: 前后端数据流对照

```
┌──────────────────────────────────────────────────────────┐
│                    前端组件                               │         后端 API
│                                                          │
│  KnowledgeBaseView (列表模式)                             │
│    ├─ Stats Row                                          │ ← GET /api/knowledge-bases/stats
│    ├─ KbCard[] / Table                                   │ ← GET /api/knowledge-bases
│    └─ KbCreateDialog                                     │ → POST /api/knowledge-bases
│                                                          │
│  KbDetail (详情模式)                                      │
│    ├─ Header (名称/状态/操作)                              │ ← GET /api/knowledge-bases/{id}
│    │                                                      │ → PUT /api/knowledge-bases/{id}
│    │                                                      │ → DELETE /api/knowledge-bases/{id}
│    │                                                      │
│    ├─ Tab: 概览 (KbOverviewTab)                           │
│    │   ├─ 4 KbStatCard                                   │ ← GET /api/knowledge-bases/{id} (统计字段)
│    │   ├─ 最近索引活动                                     │ ← GET /api/knowledge-bases/{id}/indexing-activity
│    │   └─ 索引方案摘要                                     │ ← GET /api/knowledge-bases/{id} (config 字段)
│    │                                                      │
│    ├─ Tab: 文档 (KbDocsTab)                               │
│    │   ├─ 文档列表                                        │ ← GET /api/knowledge-bases/{id}/documents
│    │   ├─ 上传文档                                        │ → POST /api/knowledge-bases/{id}/documents/upload
│    │   ├─ 删除文档                                        │ → DELETE /api/knowledge-bases/{id}/documents/{doc_id}
│    │   ├─ 重试文档                                        │ → POST /api/knowledge-bases/{id}/documents/{doc_id}/retry
│    │   └─ 索引流水线面板                                   │ ← GET /api/knowledge-bases/{id}/documents/{doc_id}
│    │                                                      │
│    ├─ Tab: 知识图谱 (KbGraphTab)                           │
│    │   ├─ 图谱可视化                                      │ ← GET /api/knowledge-bases/{id}/graph
│    │   └─ 实体列表                                        │ ← GET /api/knowledge-bases/{id}/graph
│    │                                                      │
│    ├─ Tab: 检索 (KbSearchTab) — 【暂不实现】               │
│    │                                                      │
│    └─ Tab: 索引配置 (KbConfigTab) — 【读取已有，更新暂不实现】│
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 附录 B: 错误码定义

| HTTP 状态码 | 错误场景 | 前端处理 |
|-------------|----------|----------|
| `200` | 正常响应 | - |
| `400` | 参数校验失败（文件类型不支持、切片参数越界等） | 显示错误提示 |
| `404` | 知识库/文档不存在 | 跳转回列表页 |
| `409` | 知识库名称冲突 | 提示用户修改名称 |
| `413` | 上传文件过大 | 提示文件大小限制 |
| `422` | Pydantic 校验失败 | 显示具体字段错误 |
| `500` | 向量数据库连接失败 / 索引异常 | 显示通用错误，记录日志 |

---

## 附录 C: 设计模式应用总结

本详细设计方案中系统性地应用了以下 9 种 GoF 设计模式。下表给出了每种模式的在本系统中的角色、应用位置和核心收益。

| # | 模式 | 模式类型 | 应用位置 | 在本系统中的角色 | 核心收益 |
|---|------|----------|----------|-----------------|---------|
| 1 | **策略模式** (Strategy) | 行为型 | §6.2 文档加载器 / §6.3 文本切片器 / §7.1 向量数据库 | `DocumentLoaderStrategy` → 11 种文档加载策略；`ChunkStrategy` → 5 种切片策略；`BaseVectorStore` → Milvus/Chroma 策略 | 消除 `if-elif` 分支；新增格式/策略无需改已有代码（开闭原则） |
| 2 | **模板方法模式** (Template Method) | 行为型 | §8.2 `IndexingPipeline` | `execute()` 模板方法定义 8 阶段骨架，`_on_start/_on_complete/_on_error` 为可覆写钩子 | 固定流水线顺序，子类可替换具体步骤；复用错误处理逻辑 |
| 3 | **状态模式** (State) | 行为型 | §6.8 文档状态机 | `DocState` → 8 个具体状态类（`QueuedState`→`ParsingState`→...→`IndexedState`/`FailedState`） | 消除状态判断的条件分支；状态转换规则显式化；新增状态独立安全 |
| 4 | **观察者模式** (Observer) | 行为型 | §8.2 `ProgressObserver` | `DatabaseProgressObserver`（持久化）、`LoggingProgressObserver`（日志）；可扩展 SSE 推送观察者 | 进度产生者与消费者解耦；新增通知渠道（SSE/WebSocket）无需改流水线代码 |
| 5 | **建造者模式** (Builder) | 创建型 | §7.0.5 `CollectionBuilder` | 链式调用构建 Milvus Collection（字段→Schema→索引→Function） | 隐藏 11 字段 + 3 索引 + BM25 Function 的复杂创建步骤；保证构建顺序正确 |
| 6 | **工厂模式** (Factory) | 创建型 | §6.2 `create_default_loader_registry()` / §6.3 `create_chunk_registry()` / §7.4 `create_vector_store()` | 工厂函数封装对象创建逻辑，根据配置/参数返回对应的策略注册表或实例 | 隔离对象创建复杂性；调用方仅依赖抽象接口 |
| 7 | **单例模式** (Singleton) | 创建型 | §8.2 `IndexingScheduler` | 全局唯一调度器（`__new__` + `_instance`），保证任务队列和并发控制集中管理 | 避免多调度器竞争；状态全局一致 |
| 8 | **组合模式** (Composite) | 结构型 | §6.2 `FallbackLoaderStrategy` | 将多个 `DocumentLoaderStrategy` 组合为一个具有优先级链的复合策略 | 单个策略与组合策略统一对待（`load()` 接口一致）；透明实现容错降级 |
| 9 | **外观模式** (Facade) | 结构型 | §5 API 层 `service.py` / §8.2 `IndexingPipeline` | `KnowledgeBaseService` 对外暴露简洁 CRUD 接口；`IndexingPipeline` 对外暴露 `execute(task)` | 隐藏内部 RAG 流水线复杂性；前端/API 层仅需一行调用 |

### C.1 各模式协作关系

```
┌─────────────────────────────────────────────────────────────┐
│                    KnowledgeBaseService                      │
│                     (外观模式 Facade)                         │
│  upload_document() / create_kb() / delete_doc() / ...       │
└────────────┬────────────────────────────────────────────────┘
             │ 调用
    ┌────────▼────────┐
    │ IndexingScheduler│  ← 单例模式 (Singleton)
    │   .enqueue()     │
    └────────┬────────┘
             │ 分发任务
    ┌────────▼────────────────────────────────────────────────┐
    │               IndexingPipeline                           │
    │              (模板方法 Template Method)                   │
    │                                                          │
    │  execute(task):  ─ 模板方法骨架                          │
    │    _on_start()                                           │
    │    _run_state_machine()  ──► DocState.handle()           │
    │    │                        (状态模式 State)              │
    │    │   ├─ ParsingState  ──► DocumentLoaderStrategy       │
    │    │   │                    (策略模式 Strategy)           │
    │    │   ├─ ChunkingState ──► ChunkStrategy                │
    │    │   │                    (策略模式 Strategy)           │
    │    │   ├─ EmbeddingState ──► Embedding 模型              │
    │    │   ├─ BM25State ───────► BaseVectorStore             │
    │    │   │                    (策略模式 Strategy)           │
    │    │   └─ ExtractingState──► GraphExtractionService      │
    │    │                                                      │
    │    │  每次状态转换:                                       │
    │    │    ctx.on_status_change()                            │
    │    │      └──► ProgressObserver.on_progress()            │
    │    │           (观察者模式 Observer)                       │
    │    │           ├─ DatabaseProgressObserver                │
    │    │           └─ LoggingProgressObserver                 │
    │    │                                                      │
    │    _on_complete() / _on_error()  ─ 钩子方法               │
    └──────────────────────────────────────────────────────────┘
```

### C.2 设计原则遵循

| 设计原则 | 体现 |
|----------|------|
| **开闭原则 (OCP)** | 新增文档类型/切片策略只需新增策略类并注册，无需修改 Pipeline 代码 |
| **单一职责 (SRP)** | 每种策略类只负责一种加载/切片算法；每个 Observer 只负责一种通知渠道；每个 State 只负责一个阶段 |
| **依赖倒置 (DIP)** | `IndexingPipeline` 依赖 `DocumentLoaderStrategy`/`ChunkStrategy`/`BaseVectorStore` 抽象接口，而非具体实现 |
| **接口隔离 (ISP)** | `DocState` 只定义 `handle()`；`ProgressObserver` 只定义 `on_progress()`；策略接口极简且专一 |
| **里氏替换 (LSP)** | 任何 `ChunkStrategy` 子类可替换使用而不影响 Pipeline 正确性；Milvus/Chroma 可互换 |
| **合成复用 (CARP)** | `FallbackLoaderStrategy` 通过组合多个策略实现容错降级，优于多层继承 |

### C.3 未使用但已考虑的模式

以下模式在评审中考虑过但判断不适用当前场景：

| 模式 | 考虑场景 | 不适用原因 |
|------|----------|------------|
| **责任链模式** (Chain of Responsibility) | 流水线 8 个阶段串联 | 阶段顺序固定且有状态依赖（前一步输出是后一步输入），不适合任意链组合；改用模板方法+状态模式更清晰 |
| **装饰器模式** (Decorator) | 为加载/切片策略加日志/重试/缓存 | 当前需求不涉及多层装饰；若后续需要重试/熔断，可以在策略注册表外包装一层装饰器 |
| **命令模式** (Command) | `IndexingTask` 可视为 Command 对象 | 当前缺少"撤销"需求，`IndexingTask` 仅作为数据载体（dataclass），不是完整 Command；后续若支持暂停/恢复/撤销再引入 |
| **适配器模式** (Adapter) | 统一不同向量数据库 API | 当前通过 `BaseVectorStore` 策略接口已解决问题，无需额外适配层 |
