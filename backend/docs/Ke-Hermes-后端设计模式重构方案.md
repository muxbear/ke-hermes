# Ke-Hermes 后端设计模式重构方案

> 基于 GoF 23 种设计模式思想，对 backend/ 源代码进行系统性分析，输出当前模式使用现状与未来重构建议。

---

## 目录

1. [总体评估](#1-总体评估)
2. [创建型模式（5 种）](#2-创建型模式)
3. [结构型模式（7 种）](#3-结构型模式)
4. [行为型模式（11 种）](#4-行为型模式)
5. [综合得分矩阵](#5-综合得分矩阵)
6. [分阶段实施路线图](#6-分阶段实施路线图)
7. [重点重构示例](#7-重点重构示例)

---

## 1. 总体评估

| 维度 | 得分 | 说明 |
|------|------|------|
| **已应用模式数** | 15/23 | Builder、Strategy、Observer、State、Template Method、Singleton、Decorator、Facade、Adapter、Composite、Iterator、Abstract Factory、Proxy、Chain of Responsibility、Command |
| **应用质量** | B+ | 核心领域（知识库索引、检索、Agent 构建）模式运用成熟；API 层各 service 模式使用不均衡 |
| **未应用模式数** | 8/23 | Prototype、Factory Method、Bridge、Flyweight、Mediator、Memento、Visitor、Interpreter |
| **重构紧迫度** | 中等 | 当前架构可维护，但随业务增长需引入更多模式控制复杂度 |

### 架构分层与模式分布

```
┌─────────────────────────────────────────────────────────┐
│  API 层 (路由 + 依赖注入)                                 │
│  ✓ Decorator  ✓ DI  ✓ Facade                           │
│  △ Mediator (缺失)  △ Command (缺失)                     │
├─────────────────────────────────────────────────────────┤
│  Service 层 (业务逻辑)                                    │
│  ✓ Strategy  ✓ Template Method  ✓ Observer              │
│  ✓ State     ✓ Singleton        ✓ Iterator              │
│  △ Factory Method (缺失)  △ Prototype (缺失)              │
│  △ Visitor (缺失)                                        │
├─────────────────────────────────────────────────────────┤
│  Agent 层 (智能体构建)                                    │
│  ✓ Builder  ✓ Adapter  ✓ Composite  ✓ Proxy             │
│  ✓ Chain of Responsibility  ✓ Command                   │
│  △ Bridge (缺失)                                        │
├─────────────────────────────────────────────────────────┤
│  Core 层 (横切关注点)                                     │
│  ✓ Decorator  ✓ Abstract Factory  ✓ Facade              │
│  △ Flyweight (缺失)                                      │
├─────────────────────────────────────────────────────────┤
│  Data 层 (持久化)                                        │
│  ✓ Iterator (Pagination)                                │
│  △ Memento (缺失)  △ Proxy (连接池，已部分实现)            │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 创建型模式

### 2.1 Factory Method（工厂方法）

**模式定义**: 定义一个创建对象的接口，让子类决定实例化哪个类。

| 项目 | 内容 |
|------|------|
| **当前状态** | 未应用 |
| **严重程度** | 中等 |
| **影响范围** | `src/core/rag/embedding.py`、`src/api/knowledge_base/doc_service.py`、`src/core/rag/vector_store.py` |

**现状分析**:
- 当前使用 `if/elif` 分支创建对象：`get_embedding_model()` 通过 API base URL 判断返回哪种 Embedding 实现；`src/server.py` `_init_knowledge_base()` 通过 `if/elif settings.VECTOR_DB_BACKEND` 判断创建 Milvus/Chroma 实例。
- 每增加一种向量库或 Embedding 后端，都需要修改现有 `if/elif` 链（违反开闭原则）。

**重构建议**:
```python
# 当前: if/elif 分支
if settings.VECTOR_DB_BACKEND == "milvus":
    vector_store = MilvusVectorStore(...)
elif settings.VECTOR_DB_BACKEND == "chroma":
    vector_store = ChromaVectorStore(...)

# 重构: Factory Method + 自动注册
class VectorStoreFactory:
    _creators: dict[str, Callable[..., BaseVectorStore]] = {}

    @classmethod
    def register(cls, backend: str, creator: Callable):
        cls._creators[backend] = creator

    @classmethod
    def create(cls, backend: str, **kwargs) -> BaseVectorStore:
        if backend not in cls._creators:
            raise ValueError(f"Unsupported backend: {backend}")
        return cls._creators[backend](**kwargs)

# 各模块自注册
VectorStoreFactory.register("milvus", lambda **kw: MilvusVectorStore(**kw))
VectorStoreFactory.register("chroma", lambda **kw: ChromaVectorStore(**kw))
```

**优先级**: P1（第二阶段）

---

### 2.2 Abstract Factory（抽象工厂）

**模式定义**: 提供创建一系列相关或相互依赖对象的接口，无需指定具体类。

| 项目 | 内容 |
|------|------|
| **当前状态** | 部分应用 |
| **应用位置** | `src/core/rag/embedding.py` — `get_embedding_model()` 返回不同 Embedding 实现 |
| **成熟度** | C（单一产品族，未形成完整抽象工厂） |

**现状分析**:
- `get_embedding_model()` 仅按 API base URL 区分，实际是简单工厂而非抽象工厂。
- 缺少"产品族"概念：例如当切换到 OpenAI 生态时，应同时切换 LLM + Embedding + VectorStore 为一组产品族。

**重构建议**:
引入 `AIFamilyFactory` 抽象，封装 LLM + Embedding + 其他组件的配套创建。当用户切换 AI 供应商时，整体切换产品族：

```python
class AIFamilyFactory(ABC):
    @abstractmethod
    def create_llm(self) -> BaseChatModel: ...
    @abstractmethod
    def create_embedding(self) -> Embeddings: ...
    @abstractmethod
    def create_vector_store(self) -> BaseVectorStore: ...

class DeepSeekDashScopeFamily(AIFamilyFactory): ...
class OpenAIFamily(AIFamilyFactory): ...
```

**优先级**: P3（远期规划）

---

### 2.3 Builder（建造者）

**模式定义**: 将复杂对象的构建与表示分离，使同样的构建过程创建不同表示。

| 项目 | 内容 |
|------|------|
| **当前状态** | 优秀应用 |
| **应用位置** | `src/agent/builders/agent_builder.py` — `AgentBuilder` |
| **成熟度** | A |

**现状分析**:
- `AgentBuilder` 将原来 118 行的 `create_main_agent()` 分解为 9 个链式步骤，是目前代码库中设计最精良的模式应用。
- 支持步骤顺序校验（前置条件检查），链式 API 表达力强。

**改进空间**:
- 当前 `AgentBuilder` 缺少 **Director** 角色——`create_main_agent_v2()` 直接编排步骤顺序。可提取 `AgentDirector` 封装不同场景的构建顺序（如 `create_lightweight_agent()` vs `create_full_agent()`）。
- 构建步骤中有状态可变性，可考虑让 Builder 支持 `reset()` 复用。

**优先级**: P3（可选优化）

---

### 2.4 Prototype（原型）

**模式定义**: 通过复制现有对象创建新对象，而非通过 new 实例化。

| 项目 | 内容 |
|------|------|
| **当前状态** | 未应用 |
| **严重程度** | 中等 |
| **影响范围** | `src/api/agents/service.py` — Agent 克隆功能 |

**现状分析**:
- `clone_agent()` 功能通过手动逐字段复制实现。当 Agent 的关联数据（tools、skills、files、config）变多时，克隆逻辑会变得冗长且易遗漏。
- 知识库配置复制、文档模板创建等场景也适合原型模式。

**重构建议**:
```python
class AgentPrototype:
    """Agent 原型——支持深拷贝克隆。"""

    def __init__(self, agent: Agent, tools: list, skills: list, files: list):
        self._agent = agent
        self._tools = tools
        self._skills = skills
        self._files = files

    def clone(self, overrides: dict | None = None) -> Agent:
        """克隆 Agent 及其关联数据，支持按需覆盖属性。"""
        import copy
        new_agent = copy.deepcopy(self._agent)
        new_agent.id = str(uuid.uuid4())
        new_agent.name = f"{self._agent.name} (副本)"
        if overrides:
            for k, v in overrides.items():
                setattr(new_agent, k, v)
        return new_agent
```

**优先级**: P2（第三阶段）

---

### 2.5 Singleton（单例）

**模式定义**: 确保类只有一个实例，并提供全局访问点。

| 项目 | 内容 |
|------|------|
| **当前状态** | 已应用但混合两种实现风格 |
| **应用位置** | `src/api/knowledge_base/doc_service.py` `IndexingScheduler`（`__new__` 风格）；`src/api/knowledge_base/search_service.py` `_orchestrator`（模块级全局变量风格） |
| **成熟度** | B+ |

**现状分析**:
- `IndexingScheduler` 使用 `__new__` + `_initialized` 实现线程安全的单例，且 `__init__` 可接受不同参数，设计合理。
- `SearchOrchestrator` 使用模块级全局变量 `_orchestrator` + `set_search_orchestrator()` / `get_search_orchestrator()` 函数对，本质上是"手动单例"。
- 两种风格混用不利于团队统一认知。

**改进空间**:
- 统一单例实现方式，提取公共 `Singleton` 元类或基类。
- `SearchOrchestrator` 可考虑不设为单例（目前依赖注入到 `app.state` 和模块全局变量两处，造成了双重持有），统一走 FastAPI `app.state` 依赖注入。

**优先级**: P2（第三阶段）

---

## 3. 结构型模式

### 3.1 Adapter（适配器）

**模式定义**: 将一个接口转换为客户期望的另一个接口。

| 项目 | 内容 |
|------|------|
| **当前状态** | 良好应用 |
| **应用位置** | `src/agent/sandbox/user_aware_sandbox_backend.py` — 将 `SandboxManager` 适配为 `BaseSandbox` 接口 |
| **成熟度** | A- |

**现状分析**:
- `UserAwareSandboxBackend` 从 LangGraph runtime context 中提取 `user_id`，路由到对应的 per-user sandbox，完美履行适配器职责。

**改进空间**:
- OAuth 模块 (`src/api/oauth/service.py`) 中已用 `if/elif provider` 分支处理 GitHub/Google/WeChat，可抽象统一的 `OAuthProvider` 接口，由各平台适配器实现：
  ```python
  class OAuthProvider(ABC):
      @abstractmethod
      def get_authorization_url(self, state: str) -> str: ...
      @abstractmethod
      async def exchange_code(self, code: str) -> OAuthUserInfo: ...

  class GitHubOAuthAdapter(OAuthProvider): ...
  class GoogleOAuthAdapter(OAuthProvider): ...
  class WeChatOAuthAdapter(OAuthProvider): ...
  ```

**优先级**: P1（第二阶段）

---

### 3.2 Bridge（桥接）

**模式定义**: 将抽象与实现分离，使两者可独立变化。

| 项目 | 内容 |
|------|------|
| **当前状态** | 未应用 |
| **严重程度** | 中等 |
| **影响范围** | `src/core/rag/vector_store.py` + `src/api/knowledge_base/search_service.py` |

**现状分析**:
- 当前 `BaseVectorStore` 的抽象维度（Milvus/Chroma）与搜索策略维度（Vector/BM25/Hybrid）紧耦合——每种策略都需要知道底层是哪种向量库。
- 随着向量库种类增加（如增加 Qdrant、Weaviate），策略 × 向量库的组合会爆炸。

**重构建议**:
```python
# 桥接: 将"搜索操作"抽象从"向量库实现"中分离

class VectorStoreImplementation(ABC):
    """实现侧: 具体向量库"""
    @abstractmethod
    async def similarity_search(self, kb_id, embedding, top_k): ...
    @abstractmethod
    async def bm25_search(self, kb_id, query, top_k): ...

class SearchOperation(ABC):
    """抽象侧: 搜索操作"""
    def __init__(self, impl: VectorStoreImplementation):
        self._impl = impl

    @abstractmethod
    async def execute(self, ctx): ...

class VectorSearch(SearchOperation): ...
class BM25Search(SearchOperation): ...
class HybridSearch(SearchOperation): ...
```

**优先级**: P2（第三阶段）

---

### 3.3 Composite（组合）

**模式定义**: 将对象组合成树形结构，使客户端统一对待单个对象和组合对象。

| 项目 | 内容 |
|------|------|
| **当前状态** | 良好应用 |
| **应用位置** | `deepagents.backends.CompositeBackend`（LangGraph 生态）；`src/core/rag/loaders.py` `FallbackLoaderStrategy` |
| **成熟度** | A- |

**现状分析**:
- `CompositeBackend` 通过路由前缀将 sandbox backend、StoreBackend、FilesystemBackend 组合为统一后端——这是教科书级的组合模式应用。
- `FallbackLoaderStrategy` 组合多个文档加载策略，按优先级链依次尝试，体现组合模式的"责任链"变体。

**改进空间**:
- `src/api/` 路由注册 (`api/__init__.py`) 当前是扁平的 `APIRouter` 列表聚合，可引入层级化路由器组合，支持嵌套路由前缀和中间件分组。

**优先级**: P3（可选优化）

---

### 3.4 Decorator（装饰器）

**模式定义**: 动态给对象添加额外职责，比继承更灵活。

| 项目 | 内容 |
|------|------|
| **当前状态** | 优秀应用 |
| **应用位置** | `src/core/decorators.py` — `@handle_errors`、`@cached`、`@retry`、`@log_call` |
| **成熟度** | A |

**现状分析**:
- 4 个核心装饰器覆盖了 API 层 40+ 个 service 函数的横切关注点，消除了大量重复 try/except/cache 代码。
- 设计质量高：支持参数化（`@cached(ttl=300)`）、可选括号调用（`@handle_errors` vs `@handle_errors(default_message="...")`）、类型安全。

**改进空间**:
- `@handle_errors` 当前只覆盖 `agents_api.py`，其余 13 个 API 模块各自手写 try/except。应推广到所有 API 端点。
- 增加 `@validate_request` 装饰器，统一处理 Pydantic 校验失败 → 400 响应。
- 增加 `@require_permission(role)` 装饰器，统一 RBAC 权限校验。
- 增加 `@rate_limit(max_calls, period)` 装饰器，替代当前手写的登录限流逻辑。

**优先级**: P1（第二阶段）

---

### 3.5 Facade（外观）

**模式定义**: 为子系统中的一组接口提供统一高层接口。

| 项目 | 内容 |
|------|------|
| **当前状态** | 部分应用 |
| **应用位置** | `src/agent/mainagents/main_agent.py` `create_main_agent()`；`src/server.py` `_init_knowledge_base()` |
| **成熟度** | B |

**现状分析**:
- `create_main_agent()` / `create_main_agent_v2()` 为 Agent 子系统提供了简洁的外观入口，调用方无需了解 Builder、Backend、Memory 等内部细节。
- `_init_knowledge_base()` 作为知识库子系统初始化外观，封装了 10+ 个组件的创建与装配。

**改进空间**:
- `_init_knowledge_base()` 函数 80+ 行（`src/server.py:29-127`），内部逻辑庞杂。可将知识库子系统整体提取为 `KnowledgeBaseFacade` 类：
  ```python
  class KnowledgeBaseFacade:
      """知识库子系统外观——封装所有 KB 组件的初始化与生命周期。"""
      def __init__(self, settings): ...
      async def initialize(self, app: FastAPI): ...
      async def shutdown(self): ...
  ```
- 同理，Auth 子系统（JWT + bcrypt + 限流 + OAuth）也可提取 Facade。

**优先级**: P1（第二阶段）

---

### 3.6 Flyweight（享元）

**模式定义**: 运用共享技术有效支持大量细粒度对象。

| 项目 | 内容 |
|------|------|
| **当前状态** | 未应用 |
| **严重程度** | 低 |
| **影响范围** | `src/core/rag/splitters.py`、工具注册表 |

**现状分析**:
- 当前 chunk registry 的 `_get_or_create_chunk_registry()` 已能按 `(chunk_size, chunk_overlap)` 缓存结果，形态接近享元，但未系统化。
- 工具注册（`src/agent/tools/`）中每个 tool 函数是模块级单例，本身不需要享元。
- 大规模文档索引场景中，`Document` 对象的 metadata 重复度高（如 source、doc_type 等），可享元化共享 metadata 减少内存占用。

**重构建议**:
低紧迫度。当文档量达到万级且出现内存压力时再考虑引入 `MetadataFlyweightFactory`。

**优先级**: P3（远期规划）

---

### 3.7 Proxy（代理）

**模式定义**: 为另一个对象提供替身或占位符以控制访问。

| 项目 | 内容 |
|------|------|
| **当前状态** | 部分应用 |
| **应用位置** | `src/agent/sandbox/sandbox_manager.py` `SandboxManager`（对象池代理）；`src/core/store.py` `KeyValueStore`（Redis/MemoryStore 代理）；`src/db/engine.py` `async_session`（连接池代理） |
| **成熟度** | B+ |

**现状分析**:
- `SandboxManager` 管理 per-user sandbox 实例池，实现 TTL 过期和健康检查——本质是 sandbox 实例的"智能引用代理"。
- `KeyValueStore` 在 Redis 不可用时自动降级到 `MemoryStore`——这是保护代理（protection proxy）的良好实践。

**改进空间**:
- 对 LLM 调用添加 **缓存代理**（LLM 响应缓存，避免重复 API 调用）：
  ```python
  class CachedLLMProxy:
      """LLM 调用缓存代理——透明拦截相同 prompt 的重复调用。"""
      def __init__(self, llm, store: KeyValueStore):
          self._llm = llm
          self._store = store

      async def ainvoke(self, messages):
          cache_key = _hash_messages(messages)
          cached = await self._store.get(cache_key)
          if cached:
              return cached
          result = await self._llm.ainvoke(messages)
          await self._store.set(cache_key, result, ttl=3600)
          return result
  ```

**优先级**: P2（第三阶段）

---

## 4. 行为型模式

### 4.1 Chain of Responsibility（责任链）

**模式定义**: 使多个对象都有机会处理请求，避免请求发送者与接收者耦合。

| 项目 | 内容 |
|------|------|
| **当前状态** | 部分应用 |
| **应用位置** | `src/agent/middleware/skill_sandbox_sync.py`（中间件链）；`src/core/decorators.py` `@retry`（重试链） |
| **成熟度** | B- |

**现状分析**:
- Agent 中间件通过 DeepAgents 的 `middleware` 列表实现，`SkillSandboxSyncMiddleware` 在 `abefore_agent` 阶段执行——这是责任链模式的 Agent 层实现。
- 但 API 层缺少请求处理管道。目前没有统一的请求预处理链（如：认证 → 限流 → 校验 → 日志 → 业务逻辑）。

**重构建议**:
引入 API 层中间件责任链，统一请求预处理：

```python
class RequestHandler(ABC):
    def __init__(self):
        self._next: RequestHandler | None = None

    def set_next(self, handler: "RequestHandler") -> "RequestHandler":
        self._next = handler
        return handler

    @abstractmethod
    async def handle(self, request: Request) -> Response | None: ...

class AuthHandler(RequestHandler): ...
class RateLimitHandler(RequestHandler): ...
class ValidationHandler(RequestHandler): ...
```

**优先级**: P1（第二阶段）

---

### 4.2 Command（命令）

**模式定义**: 将请求封装为对象，支持参数化、队列、日志和撤销。

| 项目 | 内容 |
|------|------|
| **当前状态** | 部分应用 |
| **应用位置** | `src/api/knowledge_base/doc_service.py` `IndexingTask`（数据类，非完整 Command 模式） |
| **成熟度** | C |

**现状分析**:
- `IndexingTask` 封装了索引任务的参数，由 `IndexingScheduler` 入队执行，形态接近 Command 模式。
- 但缺少 Command 模式的核心要素：统一的 `execute()` 接口、undo 能力、命令历史日志。

**重构建议**:
- 索引任务可升级为完整 Command 模式，支持撤销（删除已写入的向量数据）、重试、命令审计日志。
- 批量操作（如批量删除文档、批量启用/禁用 Agent）可统一建模为 `BatchCommand`。

**优先级**: P2（第三阶段）

---

### 4.3 Interpreter（解释器）

**模式定义**: 给定一个语言，定义其文法表示及解释器。

| 项目 | 内容 |
|------|------|
| **当前状态** | 未应用 |
| **严重程度** | 低 |
| **影响范围** | 无明确需求 |

**现状分析**:
- 当前业务中没有自定义 DSL 或表达式语言需求。CronJob 的 cron 表达式解析由 `croniter` 库处理。
- 未来如果为 Agent 引入自定义工作流 DSL 或条件触发规则，可应用此模式。

**优先级**: P3（远期规划，无当前需求）

---

### 4.4 Iterator（迭代器）

**模式定义**: 提供顺序访问聚合对象元素的方法，不暴露内部表示。

| 项目 | 内容 |
|------|------|
| **当前状态** | 良好应用 |
| **应用位置** | `src/core/pagination.py` — `PageIterator` + `PageResult` |
| **成熟度** | A- |

**现状分析**:
- `PageIterator` 封装 offset/limit 查询 + total count，消除 6+ 个 list 函数中的重复分页逻辑。设计简洁统一。
- `PageResult` 提供 `total_pages`、`has_next`、`has_prev` 辅助属性。

**改进空间**:
- 推广 `PageIterator` 到所有列表查询端点，当前仍有部分 service（如 `list_documents`）手写分页逻辑。
- 增加游标分页支持（Cursor-based Pagination），用于大数据量实时流式查询场景。

**优先级**: P2（第三阶段）

---

### 4.5 Mediator（中介者）

**模式定义**: 定义一个中介对象封装一组对象间的交互，减少直接耦合。

| 项目 | 内容 |
|------|------|
| **当前状态** | 未应用 |
| **严重程度** | 中等 |
| **影响范围** | 知识库删除操作、Agent 配置更新 |

**现状分析**:
- 当前知识库文档删除操作 (`delete_document()`) 内部直接调用了向量库删除、文件删除、图谱数据删除、统计更新等——多对象间通信散落在单个 service 函数中。
- Agent 配置变更时（添加 skill/工具/文件），需要同步更新 DB、LangGraph Store、沙箱——当前在各 service 函数中分散处理。

**重构建议**:
引入 `KnowledgeBaseMediator` 和 `AgentConfigMediator`，将多组件协作逻辑集中管理：

```python
class KnowledgeBaseMediator:
    """知识库中介者——协调文档删除涉及的所有组件。"""

    def __init__(self, vector_store, graph_service, file_storage):
        self._vector_store = vector_store
        self._graph = graph_service
        self._storage = file_storage

    async def delete_document(self, kb_id: str, doc_id: str) -> None:
        await asyncio.gather(
            self._vector_store.delete_by_doc_id(kb_id, doc_id),
            self._graph.delete_by_doc_id(kb_id, doc_id),
            self._storage.delete_file(doc_id),
        )
        await self._recompute_kb_stats(kb_id)
```

**优先级**: P1（第二阶段）

---

### 4.6 Memento（备忘录）

**模式定义**: 在不破坏封装的前提下，捕获对象内部状态并在之后恢复。

| 项目 | 内容 |
|------|------|
| **当前状态** | 未应用 |
| **严重程度** | 中等 |
| **影响范围** | Agent 配置管理、对话历史恢复 |

**现状分析**:
- Agent 配置变更无内置的撤销/快照机制。用户误操作修改 Agent system_prompt 或 tools 后无法回退。
- 知识库配置修改（chunk_size、chunk_overlap 等）涉及 reindex 操作，变更前应保存快照。

**重构建议**:
```python
class AgentConfigMemento:
    """Agent 配置快照——支持配置回滚。"""

    def __init__(self, agent_id: str, config_snapshot: dict, version: int):
        self.agent_id = agent_id
        self.config = config_snapshot
        self.version = version
        self.timestamp = datetime.utcnow()

class AgentConfigHistory:
    """Agent 配置历史管理器。"""

    def __init__(self, store: KeyValueStore, max_snapshots: int = 10):
        self._store = store
        self._max = max_snapshots

    async def save_snapshot(self, memento: AgentConfigMemento): ...
    async def restore(self, agent_id: str, version: int) -> dict: ...
    async def list_snapshots(self, agent_id: str) -> list[AgentConfigMemento]: ...
```

**优先级**: P2（第三阶段）

---

### 4.7 Observer（观察者）

**模式定义**: 定义对象间一对多依赖，当对象状态改变时所有依赖自动通知。

| 项目 | 内容 |
|------|------|
| **当前状态** | 优秀应用 |
| **应用位置** | `src/api/knowledge_base/doc_service.py` — `ProgressObserver` → `DatabaseProgressObserver` + `LoggingProgressObserver` |
| **成熟度** | A |

**现状分析**:
- 索引流水线中的观察者模式设计完整：抽象观察者接口 `ProgressObserver`、主题 `IndexingPipeline` 提供 `attach()` / `_notify()`、多个具体观察者隔离不同关注点。
- 当前仅用于索引进度通知，可扩展到更多领域。

**改进空间**:
- 引入 **事件总线** 统一管理跨模块事件（Agent 创建/删除/状态变更、文档索引进度、用户注册等）：
  ```python
  class EventBus:
      """轻量事件总线——发布/订阅模式。"""
      _subscriptions: dict[str, list[Callable]] = {}

      @classmethod
      def subscribe(cls, event_type: str, handler: Callable):
          cls._subscriptions.setdefault(event_type, []).append(handler)

      @classmethod
      async def publish(cls, event_type: str, **payload):
          for handler in cls._subscriptions.get(event_type, []):
              await handler(**payload)

  # 使用
  EventBus.subscribe("agent.created", notify_admin)
  EventBus.subscribe("document.indexed", update_search_cache)
  ```

**优先级**: P1（第二阶段）

---

### 4.8 State（状态）

**模式定义**: 允许对象在内部状态改变时改变其行为。

| 项目 | 内容 |
|------|------|
| **当前状态** | 优秀应用 |
| **应用位置** | `src/api/knowledge_base/doc_state.py` — 8 种文档索引状态 |
| **成熟度** | A |

**现状分析**:
- 文档索引状态机是代码库中最精良的设计之一：`DocState` ABC 定义接口，8 个具体状态类各自实现 `handle()`，`IndexingContext` 封装状态持有与转换，`IndexingPipeline` 驱动状态机运行。
- 状态转移通过 `ctx.transition_to()` 统一管理，确保状态一致性。

**改进空间**:
- 知识库本身的 5 种状态（draft → indexing → ready → error → archived）目前通过简单的 status 字符串管理，可升级为完整状态机。
- Agent 的运行状态（active / inactive / error / maintenance）可同样引入状态模式。

**优先级**: P2（第三阶段）

---

### 4.9 Strategy（策略）

**模式定义**: 定义一系列算法，将每个算法封装为可互换的策略类。

| 项目 | 内容 |
|------|------|
| **当前状态** | 优秀应用 |
| **应用位置** | `src/api/knowledge_base/search_service.py` — 3 种检索策略；`src/core/rag/loaders.py` — 12 种文档加载策略；`src/core/rag/splitters.py` — 4 种分片策略 |
| **成熟度** | A |

**现状分析**:
- 策略模式是代码库中应用最广泛的模式。检索策略（Vector/BM25/Hybrid）、文档加载策略（PDF/DOCX/XLSX/...）、分片策略（Recursive/Semantic/Markdown/Agentic）均采用策略 + 注册表组合。
- 接口设计统一：`SearchStrategy.search(ctx, vector_store)`、`DocumentLoaderStrategy.load(file_path)`、`ChunkStrategy.split(documents)`。

**改进空间**:
- 通知渠道（短信/邮件/站内信）可引入策略模式统一接口：
  ```python
  class NotificationStrategy(ABC):
      @abstractmethod
      async def send(self, recipient: str, content: str) -> bool: ...

  class SMSNotification(NotificationStrategy): ...
  class EmailNotification(NotificationStrategy): ...
  class InAppNotification(NotificationStrategy): ...
  ```
- OAuth 登录策略（当前用 `if/elif provider` 分支）可利用策略 + 注册表替代。

**优先级**: P1（第二阶段）

---

### 4.10 Template Method（模板方法）

**模式定义**: 定义算法骨架，将某些步骤延迟到子类实现。

| 项目 | 内容 |
|------|------|
| **当前状态** | 良好应用 |
| **应用位置** | `src/api/knowledge_base/doc_service.py` `IndexingPipeline.execute()`；`src/api/knowledge_base/search_service.py` `SearchOrchestrator.search()` |
| **成熟度** | A- |

**现状分析**:
- `IndexingPipeline.execute()` 定义 8 阶段索引骨架，各阶段通过状态模式实现——模板方法 + 状态模式组合，设计精良。
- `SearchOrchestrator.search()` 定义检索骨架：校验 → 向量化 → 执行策略 → 查询详情 → 组装响应。

**改进空间**:
- CRUD 操作可从各 service 中提取通用模板（validate → pre-process → execute → post-process → respond）：
  ```python
  class CrudTemplate(ABC):
      async def execute(self, db, request) -> ApiResponse:
          await self.validate(db, request)
          result = await self.do_execute(db, request)
          await self.post_process(db, result)
          return self.to_response(result)

      @abstractmethod
      async def validate(self, db, request): ...
      @abstractmethod
      async def do_execute(self, db, request): ...
  ```

**优先级**: P2（第三阶段）

---

### 4.11 Visitor（访问者）

**模式定义**: 将算法与对象结构分离，在不修改类的前提下增加新操作。

| 项目 | 内容 |
|------|------|
| **当前状态** | 未应用 |
| **严重程度** | 低-中等 |
| **影响范围** | ORM 模型序列化、导出功能 |

**现状分析**:
- 多个 ORM 模型有类似的序列化/导出需求（如导出为 CSV、生成统计报表），当前在各 service 中散落 `_model_to_response()` 转换函数。
- 访问者模式可将导出逻辑集中到 Visitor 中，避免污染 ORM 模型。

**重构建议**:
当报表导出、数据迁移、批量序列化需求增多时引入：

```python
class ModelVisitor(ABC):
    @abstractmethod
    def visit_agent(self, agent: Agent) -> dict: ...
    @abstractmethod
    def visit_user(self, user: User) -> dict: ...
    # ...

class CSVExportVisitor(ModelVisitor): ...
class MetricsReportVisitor(ModelVisitor): ...
```

**优先级**: P3（远期规划）

---

## 5. 综合得分矩阵

| # | 模式 | 类型 | 当前状态 | 成熟度 | 改进紧迫度 | 阶段 |
|---|------|------|----------|--------|------------|------|
| 1 | Factory Method | 创建型 | 未应用 | — | 中 | P1 |
| 2 | Abstract Factory | 创建型 | 部分应用 | C | 低 | P3 |
| 3 | Builder | 创建型 | 优秀应用 | A | 低 | P3 |
| 4 | Prototype | 创建型 | 未应用 | — | 中 | P2 |
| 5 | Singleton | 创建型 | 已应用 | B+ | 中 | P2 |
| 6 | Adapter | 结构型 | 良好应用 | A- | 中 | P1 |
| 7 | Bridge | 结构型 | 未应用 | — | 中 | P2 |
| 8 | Composite | 结构型 | 良好应用 | A- | 低 | P3 |
| 9 | Decorator | 结构型 | 优秀应用 | A | 中 | P1 |
| 10 | Facade | 结构型 | 部分应用 | B | 中 | P1 |
| 11 | Flyweight | 结构型 | 未应用 | — | 低 | P3 |
| 12 | Proxy | 结构型 | 部分应用 | B+ | 中 | P2 |
| 13 | Chain of Responsibility | 行为型 | 部分应用 | B- | 中 | P1 |
| 14 | Command | 行为型 | 部分应用 | C | 中 | P2 |
| 15 | Interpreter | 行为型 | 未应用 | — | 低 | P3 |
| 16 | Iterator | 行为型 | 良好应用 | A- | 中 | P2 |
| 17 | Mediator | 行为型 | 未应用 | — | 中 | P1 |
| 18 | Memento | 行为型 | 未应用 | — | 中 | P2 |
| 19 | Observer | 行为型 | 优秀应用 | A | 中 | P1 |
| 20 | State | 行为型 | 优秀应用 | A | 中 | P2 |
| 21 | Strategy | 行为型 | 优秀应用 | A | 中 | P1 |
| 22 | Template Method | 行为型 | 良好应用 | A- | 中 | P2 |
| 23 | Visitor | 行为型 | 未应用 | — | 低 | P3 |

**统计**:
- 优秀应用 (A/A-): 6 个 — Builder、Adapter、Composite、Decorator、Observer、State、Strategy、Iterator、Template Method
- 良好/部分应用 (B/B+/B-/C): 6 个 — Abstract Factory、Singleton、Facade、Proxy、Chain of Responsibility、Command
- 未应用: 8 个 — Factory Method、Prototype、Bridge、Flyweight、Interpreter、Mediator、Memento、Visitor

---

## 6. 分阶段实施路线图

### 第一阶段 (P0) — 巩固现有模式 ✅ 已完成

> 当前代码库中的模式应用已达基本成熟度，第一阶段无需额外工作。

| 项目 | 状态 |
|------|------|
| Builder 模式 (AgentBuilder) | ✅ 已优秀 |
| State 模式 (文档索引状态机) | ✅ 已优秀 |
| Strategy 模式 (检索/加载/分片) | ✅ 已优秀 |
| Observer 模式 (索引进度) | ✅ 已优秀 |
| Decorator 模式 (横切关注点) | ✅ 已优秀 |
| Template Method (索引/检索编排) | ✅ 已良好 |

---

### 第二阶段 (P1) — 消除结构性债务 ⏳ 推荐优先实施

> 目标：在不增加新功能的前提下，提升代码可扩展性和一致性。

| 序号 | 重构项 | 涉及模式 | 影响文件 | 工作量 |
|------|--------|----------|----------|--------|
| P1-1 | **统一 OAuth 适配器接口** | Adapter + Strategy | `src/api/oauth/service.py` → 新增 `src/api/oauth/providers/` | 2d |
| P1-2 | **引入 API 请求处理链** | Chain of Responsibility | 新增 `src/core/middleware_chain.py` | 2d |
| P1-3 | **推广 @handle_errors 至全部端点** | Decorator | 13 个 `src/api/*/` 模块 | 1d |
| P1-4 | **知识库子系统外观** | Facade | `src/server.py` → `src/api/knowledge_base/facade.py` | 1.5d |
| P1-5 | **事件总线 (Observer 升级)** | Observer | 新增 `src/core/event_bus.py` | 1.5d |
| P1-6 | **通知策略统一** | Strategy | `src/api/sms/`、`src/api/email/` → 统一接口 | 2d |
| P1-7 | **引入知识库中介者** | Mediator | `src/api/knowledge_base/mediator.py` | 2d |
| P1-8 | **向量库工厂方法** | Factory Method | `src/server.py`、`src/core/rag/vector_store.py` | 1d |

**预计总工作量**: 13 人天

---

### 第三阶段 (P2) — 提升系统弹性 ⏸ 中期规划

> 目标：增加系统可观测性、可恢复性和操作安全性。

| 序号 | 重构项 | 涉及模式 | 影响文件 | 工作量 |
|------|--------|----------|----------|--------|
| P2-1 | **Agent 配置快照与回滚** | Memento | 新增 `src/api/agents/config_history.py` | 2d |
| P2-2 | **索引任务 Command 模式升级** | Command | `src/api/knowledge_base/doc_service.py` | 2d |
| P2-3 | **统一单例实现** | Singleton | 新增 `src/core/singleton.py` 基类 | 0.5d |
| P2-4 | **推广 PageIterator** | Iterator | 6+ 个 `list_*` service 函数 | 1d |
| P2-5 | **CRUD 模板方法** | Template Method | 新增 `src/core/crud_template.py` | 2d |
| P2-6 | **LLM 调用缓存代理** | Proxy | `src/agent/models/llm.py` | 1.5d |
| P2-7 | **向量库桥接分离** | Bridge | `src/core/rag/vector_store.py` + `search_service.py` | 3d |
| P2-8 | **知识库状态机** | State | `src/api/knowledge_base/service.py` | 1.5d |
| P2-9 | **Agent 克隆原型模式** | Prototype | `src/api/agents/service.py` | 1d |

**预计总工作量**: 14.5 人天

---

### 第四阶段 (P3) — 远期架构演进 ⏸ 按需实施

> 目标：为未来大规模扩展奠定架构基础。

| 序号 | 重构项 | 涉及模式 | 触发条件 | 工作量 |
|------|--------|----------|----------|--------|
| P3-1 | AI 供应商产品族抽象 | Abstract Factory | 接入第 3 个 AI 供应商 | 3d |
| P3-2 | Builder Director 角色 | Builder | Agent 类型 > 5 种 | 1d |
| P3-3 | 层级化路由组合 | Composite | API 模块 > 20 个 | 1d |
| P3-4 | 元数据享元化 | Flyweight | 文档量 > 10 万 | 2d |
| P3-5 | 模型序列化访问者 | Visitor | 导出格式 > 3 种 | 2d |
| P3-6 | Agent 工作流 DSL | Interpreter | 自定义工作流需求 | 5d |

---

## 7. 重点重构示例

### 7.1 P1-1: OAuth 适配器 + 策略统一

**当前问题** (`src/api/oauth/service.py`):
```python
# 当前: if/elif 分支判断 provider
if provider == "github":
    token = await exchange_github_token(code)
elif provider == "google":
    token = await exchange_google_token(code)
elif provider == "wechat":
    token = await exchange_wechat_token(code)
```

**重构后** (`src/api/oauth/providers/`):
```python
# 统一接口
class OAuthProvider(ABC):
    name: str

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str: ...
    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokenResponse: ...
    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo: ...

class GitHubOAuthProvider(OAuthProvider):
    name = "github"
    # ... 实现

class GoogleOAuthProvider(OAuthProvider):
    name = "google"
    # ... 实现

# 注册表
class OAuthProviderRegistry:
    def __init__(self):
        self._providers: dict[str, OAuthProvider] = {}

    def register(self, provider: OAuthProvider):
        self._providers[provider.name] = provider

    def get(self, name: str) -> OAuthProvider:
        if name not in self._providers:
            raise ValueError(f"Unsupported OAuth provider: {name}")
        return self._providers[name]

# service 层简化为
async def oauth_callback(provider_name: str, code: str, ...):
    provider = registry.get(provider_name)
    token = await provider.exchange_code(code, redirect_uri)
    user_info = await provider.get_user_info(token.access_token)
    # ... 统一后续处理
```

---

### 7.2 P1-5: 事件总线

**新增文件**: `src/core/event_bus.py`

```python
"""轻量事件总线——发布/订阅模式解耦跨模块通知。"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Awaitable

logger = logging.getLogger(__name__)

EventHandler = Callable[..., Awaitable[None]]


class EventBus:
    """应用级事件总线。

    使用方式:
        # 订阅
        EventBus.subscribe("agent.created", on_agent_created)
        EventBus.subscribe("document.indexed", on_doc_indexed)

        # 发布
        await EventBus.publish("agent.created", agent_id="xxx", user_id="yyy")
    """

    _subscriptions: dict[str, list[EventHandler]] = defaultdict(list)

    @classmethod
    def subscribe(cls, event_type: str, handler: EventHandler) -> None:
        cls._subscriptions[event_type].append(handler)

    @classmethod
    def unsubscribe(cls, event_type: str, handler: EventHandler) -> None:
        try:
            cls._subscriptions[event_type].remove(handler)
        except ValueError:
            pass

    @classmethod
    async def publish(cls, event_type: str, **payload) -> None:
        handlers = cls._subscriptions.get(event_type, [])
        if not handlers:
            return
        results = await asyncio.gather(
            *[handler(**payload) for handler in handlers],
            return_exceptions=True,
        )
        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                logger.error(
                    "Event handler %s failed for %s: %s",
                    handler.__name__, event_type, result,
                )


# ── 预定义事件类型 ──────────────────────────────────────

class Events:
    AGENT_CREATED = "agent.created"
    AGENT_DELETED = "agent.deleted"
    AGENT_STATUS_CHANGED = "agent.status_changed"
    DOCUMENT_INDEXED = "document.indexed"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_INDEX_FAILED = "document.index_failed"
    KNOWLEDGE_BASE_DELETED = "knowledge_base.deleted"
    USER_REGISTERED = "user.registered"
    PROVIDER_API_KEY_UPDATED = "provider.api_key_updated"
```

---

### 7.3 P1-7: 知识库中介者

**新增文件**: `src/api/knowledge_base/mediator.py`

```python
"""知识库中介者——协调文档/知识库操作中多组件间的交互。"""

import asyncio
import logging

from core.rag.vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


class KnowledgeBaseMediator:
    """封装知识库操作中涉及的多组件协调逻辑。

    将 delete_document() 中散落的：
    - 向量库删除 → vector_store
    - 文件系统删除 → shutil
    - 图谱数据删除 → db
    - KB 统计重算 → db
    集中到此中介者中管理。
    """

    def __init__(self, vector_store: BaseVectorStore):
        self._vector_store = vector_store

    async def on_document_deleted(
        self, kb_id: str, doc_id: str, storage_path: str,
    ) -> None:
        """文档删除后的级联清理。"""
        import os
        import shutil

        errors: list[str] = []

        # 向量库清理
        try:
            await self._vector_store.delete_by_doc_id(kb_id, doc_id)
        except Exception as e:
            errors.append(f"向量库: {e}")
            logger.error("删除文档向量数据失败: %s", e)

        # 文件系统清理
        storage_dir = os.path.dirname(storage_path)
        if os.path.isdir(storage_dir):
            try:
                shutil.rmtree(storage_dir, ignore_errors=True)
            except Exception as e:
                errors.append(f"文件系统: {e}")

        if errors:
            logger.warning("文档 %s 部分清理失败: %s", doc_id, "; ".join(errors))

    async def on_knowledge_base_deleted(self, kb_id: str) -> None:
        """知识库删除后的级联清理——向量库中删除整个 collection。"""
        try:
            await self._vector_store.delete_collection(kb_id)
        except Exception as e:
            logger.error("删除知识库 %s 向量数据失败: %s", kb_id, e)
```

---

### 7.4 P1-3: 推广装饰器至全部端点

**当前状态统计**:

| API 模块 | @handle_errors 使用 |
|----------|---------------------|
| `agents_api.py` | ✅ 已使用 |
| `auth_api.py` | ❌ 手写 try/except |
| `providers_api.py` | ❌ 手写 try/except |
| `kb_api.py` 等 6 个子模块 | ❌ 手写 try/except |
| `skill_api.py` | ❌ 手写 try/except |
| `tools_api.py` | ❌ 手写 try/except |
| `mcp_api.py` | ❌ 手写 try/except |

**重构示例** (`auth_api.py` 当前 vs 重构后):
```python
# 当前: 每个端点手写 try/except
@router.post("/login/account")
async def login_account(req, db=Depends(get_db), store=Depends(get_store)):
    try:
        result = await account_login(req, db, store)
        return ok(result)
    except HTTPException as e:
        return error(e.status_code, e.detail)

# 重构后: 装饰器统一处理
@router.post("/login/account")
@handle_errors
async def login_account(req, db=Depends(get_db), store=Depends(get_store)):
    return await account_login(req, db, store)
```

---

### 7.5 P1-8: 向量库工厂方法

**当前问题**: `src/server.py:55-77` 的 `if/elif` 分支
```python
if settings.VECTOR_DB_BACKEND == "milvus":
    vector_store = MilvusVectorStore(...)
elif settings.VECTOR_DB_BACKEND == "chroma":
    vector_store = ChromaVectorStore(...)
else:
    raise RuntimeError(...)
```

**重构后** (`src/core/rag/vector_store.py` 新增):
```python
class VectorStoreFactory:
    """向量库工厂——支持自动发现和注册后端。"""

    _registry: dict[str, type[BaseVectorStore]] = {}

    @classmethod
    def register(cls, backend: str, store_cls: type[BaseVectorStore]) -> None:
        cls._registry[backend] = store_cls

    @classmethod
    def create(cls, backend: str, **kwargs) -> BaseVectorStore:
        if backend not in cls._registry:
            raise ValueError(
                f"Unsupported vector store backend: {backend}. "
                f"Available: {list(cls._registry.keys())}"
            )
        return cls._registry[backend](**kwargs)


# 各实现在模块加载时自注册
VectorStoreFactory.register("milvus", MilvusVectorStore)
VectorStoreFactory.register("chroma", ChromaVectorStore)
```

---

## 附录: 模式-问题速查表

| 如果你遇到... | 考虑使用... |
|--------------|------------|
| 对象创建逻辑复杂，if/elif 泛滥 | Factory Method、Abstract Factory |
| 需要一步步构建复杂对象 | Builder |
| 需要大量复制对象 | Prototype |
| 全局只需要一个实例 | Singleton |
| 接口不兼容需要对接 | Adapter |
| 多维度的独立变化 | Bridge |
| 树形结构、部分-整体层级 | Composite |
| 需要动态添加功能 | Decorator |
| 复杂子系统需要简单入口 | Facade |
| 海量细粒度对象内存压力大 | Flyweight |
| 需要控制对象访问 | Proxy |
| 多个处理器依次处理请求 | Chain of Responsibility |
| 需要参数化/队列化/可撤销操作 | Command |
| 需要解析自定义 DSL | Interpreter |
| 统一遍历不同集合 | Iterator |
| 多对象间复杂交互协调 | Mediator |
| 需要快照/撤销/回滚 | Memento |
| 一对多状态变更通知 | Observer |
| 对象行为随状态变化 | State |
| 算法族可互换 | Strategy |
| 固定算法骨架，子类定制步骤 | Template Method |
| 对稳定结构增加新操作 | Visitor |

---

> **文档版本**: v1.0
> **编写日期**: 2026-06-27
> **适用范围**: ke-hermes backend/ (FastAPI + LangGraph + DeepAgents)
