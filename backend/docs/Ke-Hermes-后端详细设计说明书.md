# Ke-Hermes 后端详细设计说明书 — v1.7.0


| 版本  | 日期       | 作者 | 变更说明                                                     |
| ----- | ---------- | ---- | ------------------------------------------------------------ |
| 1.0.0 | 2026-05-18 | -    | 后端详细设计初版：智能体架构、Chat API、流式对话             |
| 1.2.0 | 2026-05-18 | -    | 对照前端 v1.2.0 详细设计，新增登录/注册/验证码/OAuth 模块完整设计方案，补充安全体系、数据存储、前后端接口对齐与差异分析 |
| 1.2.1 | 2026-05-19 | -    | 完成 v1.2.0 全部模块编码实现；新增 KeyValueStore 存储抽象层（Redis + 内存降级）；文档对照实际代码更新（bcrypt/cryptography 替代 passlib、JWT 密钥持久化、验证码 Session Cookie、SMS 开发模式等） |
| 1.2.2 | 2026-05-22 | -    | Agent 图重构为 init_graph/get_graph 生命周期模式、支持 PostgreSQL 检查点后端、FilesystemBackend 虚拟文件系统、internet_search 工具、Chat API 增加 thread_id 上下文管理、Windows 事件循环兼容、KeyValueStore 增加 ttl 方法 |
| 1.3.0 | 2026-05-26 | -    | Agent 图升级为 CompositeBackend + LangGraph Store + Context 上下文 + 子智能体系统；新增对话历史 CRUD 模块（Conversation API）；新增 qwen_llm 子智能体模型；配置模块扩展（DATABASE_BACKEND、STORE_BACKEND、WORKSPACE）；internet_search 工具迁移至子智能体中 |
| 1.4.0 | 2026-05-28 | -    | 新增 MCP 广场模块（4 接口 + 种子数据 + 安装/卸载）；新增 Skills 技能管理模块（9 接口 + 上传校验 + 批量操作）；新增 Email 邮箱验证码模块；新增 ORM 模型（McpTool/McpInstallation/Skill）；新增预装 Workspace 技能（github/self-improvement）；更新路由注册链（6→9 子模块）、API 接口总数（21→30）、环境变量数量（38→39+） |
| 1.5.0 | 2026-06-05 | -    | 文档对照实际代码更新：新增智能体管理模块（Agents API，12 接口 + CRUD + 配置管理 + 文件操作）；新增模型管理模块（Providers API，9 接口 + 提供商/模型 CRUD + 克隆 + 状态切换）；新增 OpenSandbox 沙盒后端模块（代码执行 + 文件上下传）；新增 ORM 模型（Agent/AgentFile/AIModel/Provider）；Agent 图默认后端切换为 OpenSandboxBackend；更新路由注册链（9→11 子模块）、API 接口总数（30→51）、ORM 模型（7→11）、环境变量数量（39→41） |
| 1.6.0 | 2026-06-11 | -    | 新增 Tools API 模块（7 接口 + 11 个预置工具）；新增 AgentSkill/AgentTool/Tool/CronJob 4 个 ORM 模型；新增 SandboxManager 沙盒管理器（每用户独立沙盒 + TTL + 健康检查）；新增 UserAwareSandboxBackend（运行时用户感知）；新增 SkillSandboxSyncMiddleware 智能体中间件（技能同步 + 网络策略）；新增 main_agent.py Agent 工厂（数据库驱动动态构建）；新增 subagents_operate.py 动态子智能体加载；Agents API 新增 4 个接口（更新/技能管理/CronJob 查询）；Provider api_key 加密存储 + 明文迁移；扩展沙盒配置项（TTL/CLEANUP/IMAGE/CPU/MEMORY/IDLE_TIMEOUT/ALLOWED_DOMAINS）；更新 Agent 模型（system_prompt 替代 prompts、provider_id/model_id 关联、移除 user_id、工具/技能改为关联表）；更新路由注册链（11→12 子模块）、API 接口总数（51→63+）、ORM 模型（11→15）、环境变量数量（41→50） |
| 1.7.0 | 2026-06-16 | -    | 新增知识库（Knowledge Base）完整 RAG 子系统（20+ 接口 + 4 个 ORM 模型 + 文档索引 8 状态机 + 知识图谱实体关系提取）；新增核心工具层（decorators.py 4 个装饰器、pagination.py PageIterator 分页迭代器）；新增 AgentBuilder 建造者模式重构 Agent 构建（9 步链式构建）；新增 Agent 共享工具模块（common.py：resolve_model / get_tool_registry）；Agent 模型简化为单一 DeepSeek 默认模型（移除 qwen_llm）；新增 RAG 基础设施（Milvus/Chroma 双向量库、13 种文档加载器、5 种切片策略、BM25 关键词索引）；引入设计模式重构（Builder/State/Observer/Strategy/Template Method/Iterator/Decorator 7 种模式正式应用）；扩展配置项（Milvus/Chroma/文档存储/图存储/索引参数共 16 个）；更新路由注册（12→16 子模块）、API 接口总数（67→87+）、ORM 模型（15→19）、环境变量数量（50→66） |


---

## 目录

1. [概述](#1-概述)
2. [技术栈](#2-技术栈)
3. [目录结构](#3-目录结构)
4. [模块详细设计](#4-模块详细设计)
  - 4.1 [服务入口 — server.py](#41-服务入口--serverpy)
  - 4.2 [配置模块 — agent/config](#42-配置模块--agentconfig)
  - 4.3 [模型模块 — agent/models](#43-模型模块--agentmodels)
  - 4.4 [上下文模块 — agent/context](#44-上下文模块--agentcontext)
  - 4.5 [智能体图 — agent/graph.py](#45-智能体图--agentgraphpy)
  - 4.6 [Agent 共享工具 — agent/common.py](#46-agent-共享工具--agentcommonpy)
  - 4.7 [主智能体工厂 — agent/mainagents](#47-主智能体工厂--agentmainagents)
  - 4.8 [Agent 建造者 — agent/builders](#48-agent-建造者--agentbuilders)
  - 4.9 [子智能体模块 — agent/subagents](#49-子智能体模块--agentsubagents)
  - 4.10 [Agent 工具集 — agent/tools](#410-agent-工具集--agenttools)
  - 4.11 [Chat API — 对话与流式接口](#411-chat-api--对话与流式接口)
  - 4.12 [Conversation API — 对话历史 CRUD](#412-conversation-api--对话历史-crud)
  - 4.13 [Auth API — 认证授权模块](#413-auth-api--认证授权模块)
  - 4.14 [Captcha API — 验证码模块](#414-captcha-api--验证码模块)
  - 4.15 [OAuth API — 第三方登录模块](#415-oauth-api--第三方登录模块)
  - 4.16 [SMS API — 短信服务模块](#416-sms-api--短信服务模块)
  - 4.17 [Email API — 邮箱验证码模块](#417-email-api--邮箱验证码模块)
  - 4.18 [MCP API — MCP 广场模块](#418-mcp-api--mcp-广场模块)
  - 4.19 [Skills API — 技能管理模块](#419-skills-api--技能管理模块)
  - 4.20 [Agents API — 智能体管理模块](#420-agents-api--智能体管理模块)
  - 4.21 [Providers API — 模型管理模块](#421-providers-api--模型管理模块)
  - 4.22 [Tools API — 工具管理模块](#422-tools-api--工具管理模块)
  - 4.23 [Knowledge Base API — 知识库管理模块](#423-knowledge-base-api--知识库管理模块)
  - 4.24 [Sandbox — 沙盒代码执行模块](#424-sandbox--沙盒代码执行模块)
  - 4.25 [Middleware — 智能体中间件](#425-middleware--智能体中间件)
  - 4.26 [核心工具层 — core/ 模块](#426-核心工具层--core-模块)
5. [数据存储设计](#5-数据存储设计)
6. [安全设计](#6-安全设计)
7. [API 接口总览与前后端对照](#7-api-接口总览与前后端对照)
8. [数据流](#8-数据流)
9. [环境变量设计](#9-环境变量设计)
10. [关键设计决策](#10-关键设计决策)
11. [测试设计](#11-测试设计)
12. [启动与部署](#12-启动与部署)
13. [前后端实施差异与待实现项](#13-前后端实施差异与待实现项)

---

## 1. 概述

### 1.1 文档目的

本文档为 Ke-Hermes 后端的详细设计说明书 v1.7.0，对照实际代码实现编写。文档覆盖：

- **已实现模块**：智能体框架（含数据库驱动的主智能体工厂 + AgentBuilder 建造者模式 + 动态子智能体加载 + Agent 共享工具模块 + Agent 工具集 + OpenSandboxBackend 代码执行后端 + SandboxManager 每用户沙盒管理 + UserAwareSandboxBackend 用户感知 + SkillSandboxSyncMiddleware 技能同步中间件）、Chat API（普通对话 + SSE 流式 + thread_id 上下文管理）、Conversation API（对话历史 CRUD）、Agents API（智能体 CRUD + 配置管理 + 文件操作 + 技能关联 + CronJob 查询，17 接口）、Providers API（提供商/模型 CRUD + 克隆 + 状态切换，9 接口 + api_key 加密）、Tools API（工具 CRUD + 列表 + 切换，7 接口 + 11 个预置工具）、Knowledge Base API（知识库 CRUD + 文档上传/索引/重试 + 知识图谱实体关系提取 + 分块管理，20+ 接口）、MCP 广场 API（工具列表/详情/安装/卸载 + 12 个种子数据）、Skills 技能管理 API（CRUD + 上传校验 + 批量删除 + 5 个预置技能）、认证授权、验证码、OAuth 第三方登录、短信服务、邮箱验证码
- **基础设施**：KeyValueStore 存储抽象层（Redis + 内存降级）、RSA + JWT + bcrypt + Fernet 安全体系、SQLAlchemy 异步 ORM（SQLite + PostgreSQL 双后端，19 个 ORM 模型）、LangGraph 检查点双后端（SQLite + PostgreSQL）+ LangGraph Store（Memory + PostgreSQL）、OpenSandbox 沙盒代码执行环境（每用户独立沙盒 + TTL 生命周期 + 健康检查 + 后台清理）、RAG 知识库基础设施（Milvus/Chroma 双向量库后端 + 13 种文档加载器 + 5 种文本切片策略 + BM25 关键词索引 + Langextract 知识图谱提取）、核心工具层（装饰器库 + 分页迭代器）

文档供后端开发人员编码实现、代码审查和后期维护使用。

### 1.2 技术栈


| 组件           | 技术/框架                                            | 版本要求        | 用途                       |
| ------------ | ------------------------------------------------ | ----------- | ------------------------ |
| Web 框架       | FastAPI                                          | >=0.100.0   | HTTP API 路由与请求处理         |
| ASGI 服务器     | uvicorn                                          | >=0.20.0    | 服务运行与部署                  |
| 智能体框架        | deepagents                                       | >=0.6.1     | 智能体图构建                   |
| LLM/模型调用     | langchain-openai                                 | >=1.2.0     | DeepSeek/DashScope 模型调用  |
| 配置管理         | pydantic-settings                                | >=2.0.0     | 环境变量配置类                  |
| 环境加载         | python-dotenv                                    | >=1.0.1     | .env 文件加载                |
| 图执行引擎        | langgraph                                        | >=1.0.0     | 智能体图状态机运行                |
| 检查点存储        | langgraph-checkpoint-sqlite / AsyncPostgresSaver | —           | 对话上下文检查点持久化（双后端）         |
| LangGraph Store | AsyncPostgresStore / InMemoryStore               | —           | 长期记忆/跨对话状态存储（双后端）         |
| 互联网搜索        | tavily-python                                    | —           | 子智能体互联网搜索工具               |
| 沙盒代码执行        | opensandbox / opensandbox-code-interpreter       | >=0.1.2     | OpenSandbox 沙盒代码执行后端      |
| 密码哈希         | bcrypt                                           | >=4.0       | 密码哈希存储与校验                |
| JWT          | PyJWT                                            | >=2.8       | Token 签发与验证              |
| RSA 加密       | cryptography                                     | >=42.0      | RSA 密钥对生成与加解密            |
| 对称加密         | cryptography (Fernet)                            | >=42.0      | Provider API Key 加密存储     |
| 数据校验         | pydantic                                         | >=2.0       | 请求/响应模型定义                |
| 异步数据库        | SQLAlchemy[asyncio]                              | >=2.0       | ORM + 连接池                |
| 异步 SQLite 驱动 | aiosqlite                                        | >=0.20      | 开发环境数据库驱动                |
| 数据库          | SQLite / PostgreSQL                              | —           | 开发环境 / 生产环境              |
| 验证码生成        | Pillow                                           | >=10.0      | 图形验证码图片生成                |
| 键值存储         | redis (可选)                                       | >=5.0       | Redis 缓存存储；不可用时自动降级为内存存储 |
| OAuth        | httpx                                            | >=0.27      | 第三方 OAuth API 调用         |
| Python       | CPython                                          | >=3.11,<4.0 | 运行环境                     |


### 1.3 相关文档

- [Ke-Hermes 前端详细设计说明书 v1.2.0](../../frontend/docs/Ke%20Hermes%20详细设计说明书-1.2.0.md)
- [Ke-Hermes 前端需求说明书-登录模块（桌面版）v1.1.0](../../frontend/docs/Ke%20Hermes%20需求说明书-登录模块（桌面版）-1.1.0.md)

---

## 2. 技术栈

（见 1.2 节完整技术栈表，此处不再重复。）

---

## 3. 目录结构

```
backend/
├── src/
│   ├── server.py                    # 服务入口（FastAPI + uvicorn）
│   ├── agent/
│   │   ├── __init__.py              # 导出 get_graph, get_checkpointer, init_graph, shutdown_graph
│   │   ├── common.py                # Agent 共享工具（v1.7.0 新增：resolve_model, get_tool_registry）
│   │   ├── config/
│   │   │   ├── __init__.py          # 导出 settings 实例
│   │   │   └── config.py            # Settings 配置类定义（v1.7.0 扩展：Milvus/Chroma/DocStore/GraphStore/Embedding/Indexing）
│   │   ├── models/
│   │   │   ├── __init__.py          # 导出 llm, embeddings
│   │   │   ├── llm.py               # ChatOpenAI 实例（v1.7.0 简化为单一 DeepSeek 模型）
│   │   │   └── em.py                # OpenAIEmbeddings 实例（DashScope）
│   │   ├── context/
│   │   │   ├── __init__.py          # 导出 Context
│   │   │   └── context.py           # Context 数据类（server_info + user_id）
│   │   ├── tools/
│   │   │   ├── __init__.py          # 导出 3 个运行时工具
│   │   │   ├── tavily_search.py     # Tavily 互联网搜索工具
│   │   │   ├── http_request.py      # HTTP 请求工具（含 SSRF 防护）
│   │   │   └── get_datetime.py      # 时区感知的日期时间工具
│   │   ├── buildrs/                 # v1.7.0 新增：Agent 建造者模式
│   │   │   ├── __init__.py          # 导出 AgentBuilder
│   │   │   └── agent_builder.py     # AgentBuilder 分步构建器（9 步链式构建）
│   │   ├── subagents/
│   │   │   ├── __init__.py          # 导出 create_subagents
│   │   │   └── subagents_operate.py # 动态子智能体加载器
│   │   ├── mainagents/
│   │   │   ├── __init__.py          # 导出 create_main_agent
│   │   │   └── main_agent.py        # 主智能体工厂（v1.7.0 重构：委托给 AgentBuilder）
│   │   ├── sandbox/
│   │   │   ├── opensandbox_backend.py       # OpenSandboxBackend 实现
│   │   │   ├── user_aware_sandbox_backend.py # UserAwareSandboxBackend
│   │   │   ├── sandbox_manager.py            # SandboxManager（每用户沙盒池）
│   │   │   └── opensandbox_operate.py        # 沙盒创建/连接辅助函数
│   │   ├── middleware/
│   │   │   ├── __init__.py          # 导出 SkillSandboxSyncMiddleware
│   │   │   └── skill_sandbox_sync.py # 技能→沙盒同步中间件
│   │   └── utils/
│   │       └── __init__.py          # 辅助方法导出（预留）
│   │
│   ├── api/
│   │   ├── __init__.py              # 导出顶层 router（v1.7.0：汇总 16 个子模块）
│   │   ├── deps.py                  # 依赖注入
│   │   ├── agent/
│   │   │   ├── __init__.py          # 导出 agent router
│   │   │   └── agent_api.py         # Chat API 路由与数据模型
│   │   ├── agents/
│   │   │   ├── __init__.py          # 导出 agents router
│   │   │   ├── agents_api.py        # 智能体管理 API 路由（17 个接口）
│   │   │   ├── schemas.py           # 智能体管理请求/响应 Pydantic 模型
│   │   │   └── service.py           # 智能体管理业务逻辑
│   │   ├── auth/
│   │   │   ├── __init__.py          # 导出 auth router
│   │   │   ├── auth_api.py          # 认证 API 路由（8 个接口）
│   │   │   ├── schemas.py           # 认证请求/响应 Pydantic 模型
│   │   │   └── service.py           # 认证业务逻辑
│   │   ├── captcha/
│   │   │   ├── __init__.py          # 导出 captcha router
│   │   │   ├── captcha_api.py       # 验证码 API 路由（4 个接口）
│   │   │   ├── schemas.py           # 验证码请求/响应 Pydantic 模型
│   │   │   └── service.py           # 验证码业务逻辑
│   │   ├── conversation/
│   │   │   ├── __init__.py          # 导出 conversation router
│   │   │   └── conversation_api.py  # 对话历史 CRUD API（4 个接口）
│   │   ├── oauth/
│   │   │   ├── __init__.py          # 导出 oauth router
│   │   │   ├── oauth_api.py         # OAuth API 路由（2 个接口）
│   │   │   ├── schemas.py           # OAuth 请求/响应 Pydantic 模型
│   │   │   └── service.py           # OAuth 业务逻辑
│   │   ├── providers/
│   │   │   ├── __init__.py          # 导出 providers router
│   │   │   ├── providers_api.py     # 模型管理 API 路由（9 个接口）
│   │   │   ├── schemas.py           # 提供商/模型请求/响应 Pydantic 模型
│   │   │   └── service.py           # 提供商/模型业务逻辑
│   │   ├── tools/
│   │   │   ├── __init__.py          # 导出 tools router
│   │   │   ├── tools_api.py         # 工具管理 API 路由（7 个接口）
│   │   │   ├── schemas.py           # 工具请求/响应 Pydantic 模型
│   │   │   └── service.py           # 工具业务逻辑
│   │   ├── knowledge_base/          # v1.7.0 新增：知识库 RAG 子系统
│   │   │   ├── __init__.py          # 导出 kb_router, doc_router, graph_router, chunk_router
│   │   │   ├── kb_api.py            # 知识库 CRUD API（10 个接口）
│   │   │   ├── doc_api.py           # 文档上传/索引/管理 API（5 个接口）
│   │   │   ├── chunk_api.py         # 分块管理 API（5 个接口）
│   │   │   ├── graph_api.py         # 知识图谱 API（3 个接口）
│   │   │   ├── schemas.py           # 知识库/文档/分块/图谱 Pydantic 模型
│   │   │   ├── service.py           # 知识库业务逻辑
│   │   │   ├── doc_service.py       # 文档索引流水线 + 观察者 + 调度器
│   │   │   ├── doc_state.py         # 文档索引 8 状态机（State 模式）
│   │   │   ├── chunk_service.py     # 分块管理业务逻辑
│   │   │   └── graph_service.py     # 知识图谱提取服务（Langextract）
│   │   └── sms/
│   │       ├── __init__.py          # 导出 sms router
│   │       ├── sms_api.py           # 短信 API 路由（1 个接口）
│   │       └── service.py           # 短信发送业务逻辑
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── engine.py                # SQLAlchemy async engine + sessionmaker + init_db + 迁移函数
│   │   ├── base.py                  # DeclarativeBase
│   │   ├── utils.py                 # utcnow() 辅助函数
│   │   └── models/
│   │       ├── __init__.py          # 导出所有 model（v1.7.0：共 19 个）
│   │       ├── user.py              # User 模型
│   │       ├── user_oauth.py        # UserOAuth 第三方绑定模型
│   │       ├── login_record.py      # LoginRecord 登录记录模型
│   │       ├── conversation.py      # Conversation 对话记录模型
│   │       ├── skill.py             # Skill 技能模型
│   │       ├── mcp_tool.py          # McpTool MCP 工具模型
│   │       ├── mcp_installation.py  # McpInstallation 安装记录模型
│   │       ├── agent.py             # Agent 智能体模型
│   │       ├── agent_file.py        # AgentFile 智能体文件模型
│   │       ├── agent_skill.py       # AgentSkill 多对多关联模型
│   │       ├── agent_tool.py        # AgentTool 多对多关联模型
│   │       ├── ai_model.py          # AIModel 模型元数据模型
│   │       ├── provider.py          # Provider 模型提供商模型
│   │       ├── tool.py              # Tool 工具定义模型
│   │       ├── cron_job.py          # CronJob 定时任务模型
│   │       ├── knowledge_base.py    # KnowledgeBase 知识库模型（v1.7.0 新增）
│   │       ├── knowledge_base_document.py  # KnowledgeBaseDocument 文档模型（v1.7.0 新增）
│   │       ├── knowledge_base_entity.py    # KnowledgeBaseEntity 实体模型（v1.7.0 新增）
│   │       └── knowledge_base_relation.py  # KnowledgeBaseRelation 关系模型（v1.7.0 新增）
│   │   └── seeds/
│   │       └── mcp_tools_seed.json   # MCP 工具种子数据
│   │
│   └── core/
│       ├── __init__.py
│       ├── security.py              # bcrypt + RSA + JWT + Fernet 安全体系
│       ├── store.py                 # KeyValueStore 抽象 + RedisStore / MemoryStore
│       ├── response.py              # 统一响应格式 ApiResponse[T]
│       ├── decorators.py            # v1.7.0 新增：装饰器库（handle_errors/cached/retry/log_call）
│       ├── pagination.py            # v1.7.0 新增：PageIterator 分页迭代器
│       └── rag/                     # v1.7.0 新增：RAG 核心基础设施
│           ├── __init__.py          # 导出所有 RAG 组件
│           ├── embedding.py         # 嵌入模型工厂（DashScope + OpenAI 兼容）
│           ├── vector_store.py      # 向量库抽象层（Milvus + Chroma）
│           ├── loaders.py           # 文档加载器策略/注册表（13 种格式）
│           ├── splitters.py         # 文本切片策略/注册表（5 种策略）
│           └── bm25_index.py        # BM25 关键词索引器
│
├── db/                              # SQLite 数据库文件目录
│   └── ke-hermes.db                 # 开发环境 SQLite 数据库文件
│
├── workspace/                       # 智能体工作目录
│   ├── memories/AGENT.md            # Agent 持久化记忆文件
│   ├── skills/                      # 每智能体技能文件目录
│   └── skills_upload/               # 上传技能目录
│
├── docs/
│   ├── Ke-Hermes-后端详细设计说明书.md  # 本文件
│   └── Ke-Hermes-后端代码设计模式评估报告.md  # 设计模式评估报告
│
├── tests/
│   ├── conftest.py
│   ├── test_loaders.py              # 文档加载器测试（v1.7.0 新增）
│   ├── unit_tests/
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   ├── test_agent.py
│   │   ├── test_agent_service.py
│   │   ├── test_http_request.py
│   │   └── test_tavily_search.py
│   └── integration_tests/
│       ├── test_server.py
│       ├── test_agent_api.py
│       └── test_agents_api.py
│
├── .env
├── .env.example
├── .jwt_secret
├── .fernet_key                      # Fernet 密钥持久化文件
├── .rsa_key                         # RSA 密钥持久化文件
├── pyproject.toml
├── run.py
├── Makefile
└── langgraph.json
```

---

## 4. 模块详细设计

### 4.1 服务入口 — `server.py`

**职责：** 创建 FastAPI 应用实例，加载环境变量，初始化基础设施，注册所有 API 路由。

**v1.6.0 完整实现：**

```python
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    import uvicorn.loops.asyncio as _uvicorn_loops

    _uvicorn_loops.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

load_dotenv()

from api import router
from api.deps import set_store
from core.store import create_store
from db.engine import init_db
from agent.graph import init_graph, shutdown_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()               # 1. 创建业务数据库表

    # 2-4. 种子数据 + 明文密钥迁移（在独立 session 中执行）
    from api.mcp.service import seed_mcp_tools
    from api.skill.service import seed_builtin_skills
    from api.tools.service import seed_builtin_tools
    from db.engine import async_session

    async with async_session() as session:
        await seed_mcp_tools(session)       # MCP 工具种子（12 个）
        await seed_builtin_skills(session)   # 内置技能种子（5 个）
        await seed_builtin_tools(session)    # 内置工具种子（11 个）
        await session.commit()

    from api.providers.service import migrate_plaintext_api_keys
    async with async_session() as session:
        await migrate_plaintext_api_keys(session)  # 将存储的明文 api_key 加密
        await session.commit()

    await init_graph()            # 5. 初始化 Agent（检查点 + Store + SandboxManager + create_main_agent）
    store = await create_store()   # 6. 初始化 KeyValueStore（Redis 或内存降级）
    set_store(store)
    from core.security import _get_jwt_secret as init_jwt
    init_jwt()                    # 7. 预初始化 JWT secret
    yield
    await shutdown_graph()        # 8. 关闭检查点连接池 + 沙盒管理器


app = FastAPI(
    title="ke-hermes",
    description="通用智能体服务",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
```

**v1.6.0 启动时的基础设施初始化顺序：**

1. `init_db()` → SQLAlchemy 自动建表（`Base.metadata.create_all`）+ 运行迁移函数
2. `seed_mcp_tools(session)` → MCP 工具种子数据初始化（12 个）
3. `seed_builtin_skills(session)` → 内置技能种子数据初始化（5 个）
4. `seed_builtin_tools(session)` → 内置工具种子数据初始化（11 个）
5. `migrate_plaintext_api_keys(session)` → 将 Provider 表中明文 api_key 迁移为加密存储
6. `init_graph()` → 创建检查点后端 + LangGraph Store + SandboxManager + create_main_agent
7. **`_init_knowledge_base(app)`**（v1.7.0 新增）→ 初始化嵌入模型 + 向量库（Milvus/Chroma）+ 文档加载器注册表 + 切片策略注册表 + 图谱提取服务 + 索引流水线 + 进度观察者 + 索引调度器
8. `create_store()` → 尝试连接 Redis，失败则降级为 `MemoryStore`
9. `set_store(store)` → 注入到 FastAPI 依赖注入系统
10. `init_jwt()` → 读取或生成持久化 JWT 签名密钥
11. (关闭时) `shutdown_graph()` → 关闭沙盒管理器 + PostgreSQL 连接池

**Windows 兼容性：** server.py 在导入链顶部通过 monkeypatch 强制使用 `SelectorEventLoop`，确保 PostgreSQL 驱动在 Windows 下正常工作。

**路由注册链（v1.7.0：16 个子模块）：**

```
api/__init__.py → 汇总所有子模块 router
  ├── api/agent/         → agent_api.router        (prefix="/api")               ← 已实现
  ├── api/agents/        → agents_api.router       (prefix="/api/agents")        ← v1.5.0 新增
  ├── api/auth/          → auth_api.router         (prefix="/api/auth")          ← 已实现
  ├── api/captcha/       → captcha_api.router      (prefix="/api/captcha")       ← 已实现
  ├── api/oauth/         → oauth_api.router        (prefix="/api/oauth")         ← 已实现
  ├── api/sms/           → sms_api.router          (prefix="/api/sms")           ← 已实现
  ├── api/conversation/  → conversation_api.router (prefix="/api")               ← v1.3.0 新增
  ├── api/email/         → email_api.router        (prefix="/api/email")         ← v1.4.0 新增
  ├── api/mcp/           → mcp_api.router          (prefix="/api/mcp")           ← v1.4.0 新增
  ├── api/providers/     → providers_api.router    (prefix="/api/providers")     ← v1.5.0 新增
  ├── api/skill/         → skill_api.router        (prefix="/api/skill")         ← v1.4.0 新增
  ├── api/tools/         → tools_api.router        (prefix="/api/tools")         ← v1.6.0 新增
  ├── api/knowledge_base/→ kb_api.router           (prefix="/api/knowledge-bases")         ← v1.7.0 新增
  ├── api/knowledge_base/→ doc_api.router          (prefix="/api/knowledge-bases/{kb_id}") ← v1.7.0 新增
  ├── api/knowledge_base/→ graph_api.router        (prefix="/api/knowledge-bases/{kb_id}") ← v1.7.0 新增
  └── api/knowledge_base/→ chunk_api.router        (prefix="/api/knowledge-bases/{kb_id}") ← v1.7.0 新增
        ↓
server.py → app.include_router(router)
```

**启动命令：**

```bash
cd backend
uv run python run.py
```

### 4.2 配置模块 — `agent/config`

**职责：** 集中管理所有环境变量配置。

#### `config.py` — Settings 类（v1.6.0 扩展）

```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


def get_default_workspace() -> str:
    """Return the agent filesystem workspace directory."""
    env = os.getenv("WORKSPACE", "").strip()
    if env:
        return os.path.abspath(env)

    backend_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    return os.path.join(backend_root, "workspace")


class Settings(BaseSettings):
    # ---- Server ----
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT") or 8000)

    # ---- LLM (DeepSeek) ----
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "")

    # ---- Embeddings (DashScope) ----
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_EMBEDDING: str = os.getenv("DASHSCOPE_EMBEDDING", "")
    DASHSCOPE_BASE_URL: str = os.getenv("DASHSCOPE_BASE_URL", "")

    # ---- Tavily ----
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # ---- Workspace ----
    WORKSPACE: str = Field(default_factory=get_default_workspace)

    @field_validator("WORKSPACE", mode="before")
    @classmethod
    def _workspace_use_default_when_empty(cls, value: object) -> str:
        if value is None or (isinstance(value, str) and not value.strip()):
            return get_default_workspace()
        return str(value)

    SKILLS_ROOT: str = f"{WORKSPACE}/skills/"

    # ---- OpenSandBox ----
    OPENSANDBOX_DOMAIN: str = os.getenv("OPENSANDBOX_DOMAIN", "http://127.0.0.1:8080")
    OPENSANDBOX_API_KEY: str = os.getenv("OPENSANDBOX_API_KEY", "")
    SANDBOX_TTL_SECONDS: int = int(os.getenv("SANDBOX_TTL_SECONDS", "1800"))
    SANDBOX_CLEANUP_INTERVAL: int = int(os.getenv("SANDBOX_CLEANUP_INTERVAL", "300"))
    SANDBOX_IMAGE: str = os.getenv(
        "SANDBOX_IMAGE",
        "sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:v1.0.2",
    )
    SANDBOX_CPU: str = os.getenv("SANDBOX_CPU", "2")
    SANDBOX_MEMORY: str = os.getenv("SANDBOX_MEMORY", "3Gi")
    SANDBOX_IDLE_TIMEOUT_MINUTES: int = int(os.getenv("SANDBOX_IDLE_TIMEOUT_MINUTES", "10"))
    SANDBOX_ALLOWED_DOMAINS: str = os.getenv("SANDBOX_ALLOWED_DOMAINS", "")

    @property
    def sandbox_allowed_domains_list(self) -> list[str]:
        """解析 SANDBOX_ALLOWED_DOMAINS 为域名列表。"""
        raw = self.SANDBOX_ALLOWED_DOMAINS.strip()
        if not raw:
            return []
        return [d.strip() for d in raw.split(",") if d.strip()]

    # ---- Database ----
    DATABASE_BACKEND: str = os.getenv("DATABASE_BACKEND", "sqlite")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "")

    # ---- Checkpoint Database ----
    CHECKPOINT_BACKEND: str = os.getenv("CHECKPOINT_BACKEND", "sqlite")
    CHECKPOINT_DB_URL: str = os.getenv("CHECKPOINT_DB_URL", "postgresql://127.0.0.1:5432/ke_hermes")
    CHECKPOINT_DB_PATH: str = os.getenv("CHECKPOINT_DB_PATH", "./db/ke_hermes.db")

    # ---- Store Database ----
    STORE_BACKEND: str = os.getenv("STORE_BACKEND", "sqlite")
    STORE_DB_URL: str = os.getenv("STORE_DB_URL", "postgresql://127.0.0.1:5432/ke_hermes")
    STORE_DB_PATH: str = os.getenv("STORE_DB_PATH", "./db/ke_hermes.db")

    # ---- Encryption ----
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

    # ---- JWT ----
    JWT_SECRET_KEY: str = ""
    JWT_ACCESS_EXPIRE: int = int(os.getenv("JWT_ACCESS_EXPIRE") or 7200)
    JWT_REFRESH_EXPIRE: int = int(os.getenv("JWT_REFRESH_EXPIRE") or 604800)

    # ---- RSA ----
    RSA_KEY_SIZE: int = int(os.getenv("RSA_KEY_SIZE") or 2048)

    # ---- Rate Limit ----
    LOGIN_MAX_FAILS: int = int(os.getenv("LOGIN_MAX_FAILS") or 5)
    LOGIN_LOCK_MINUTES: int = int(os.getenv("LOGIN_LOCK_MINUTES") or 30)
    SMS_DAILY_LIMIT: int = int(os.getenv("SMS_DAILY_LIMIT") or 5)

    # ---- Captcha ----
    CAPTCHA_EXPIRE: int = int(os.getenv("CAPTCHA_EXPIRE") or 300)
    SLIDE_THRESHOLD: int = int(os.getenv("SLIDE_THRESHOLD") or 8)

    # ---- Redis ----
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    # ---- OAuth ----
    OAUTH_GITHUB_CLIENT_ID: str = os.getenv("OAUTH_GITHUB_CLIENT_ID", "")
    OAUTH_GITHUB_CLIENT_SECRET: str = os.getenv("OAUTH_GITHUB_CLIENT_SECRET", "")
    OAUTH_GOOGLE_CLIENT_ID: str = ""
    OAUTH_GOOGLE_CLIENT_SECRET: str = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "")
    OAUTH_WECHAT_CLIENT_ID: str = os.getenv("OAUTH_WECHAT_CLIENT_ID", "")
    OAUTH_WECHAT_CLIENT_SECRET: str = os.getenv("OAUTH_WECHAT_CLIENT_SECRET", "")

    # ---- SMS ----
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "")
    SMS_ACCESS_KEY: str = os.getenv("SMS_ACCESS_KEY", "")
    SMS_SECRET_KEY: str = os.getenv("SMS_SECRET_KEY", "")
    SMS_SIGN_NAME: str = os.getenv("SMS_SIGN_NAME", "")
    SMS_TEMPLATE_CODE: str = os.getenv("SMS_TEMPLATE_CODE", "")
```

**v1.6.0 新增/变更配置项：**

| 配置项                         | 说明                                              |
| ---------------------------- | ------------------------------------------------- |
| `SKILLS_ROOT`                | 技能文件系统根目录（默认 `{WORKSPACE}/skills/`，v1.6.0 新增） |
| `SANDBOX_TTL_SECONDS`        | 每用户沙盒 TTL 秒数（默认 1800，30 分钟，v1.6.0 新增）         |
| `SANDBOX_CLEANUP_INTERVAL`   | 沙盒清理后台线程轮询间隔秒数（默认 300，v1.6.0 新增）               |
| `SANDBOX_IMAGE`              | 沙盒容器镜像（v1.6.0 新增）                                |
| `SANDBOX_CPU`                | 沙盒 CPU 核数（默认 2，v1.6.0 新增）                       |
| `SANDBOX_MEMORY`             | 沙盒内存分配（默认 3Gi，v1.6.0 新增）                        |
| `SANDBOX_IDLE_TIMEOUT_MINUTES` | 沙盒闲置超时分钟数（默认 10，v1.6.0 新增）                     |
| `SANDBOX_ALLOWED_DOMAINS`    | 逗号分隔的额外允许出站域名列表（v1.6.0 新增）                      |
| `ENCRYPTION_KEY`             | Fernet 对称加密密钥，用于 Provider API Key 加密（v1.6.0 新增）  |
| `sandbox_allowed_domains_list` | 计算属性，将 SANDBOX_ALLOWED_DOMAINS 解析为域名列表（v1.6.0 新增） |

### 4.3 模型模块 — `agent/models`

**职责：** 创建 LLM 和向量模型实例。

#### `llm.py` — DeepSeek 单模型（v1.7.0 简化）

```python
from langchain_openai import ChatOpenAI
from agent.config import settings

llm = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    extra_body={"thinking": {"type": "disabled"}}
)

__all__ = ["llm"]
```

- **`llm`**：DeepSeek 模型，通过 `extra_body` 关闭思考过程以加速响应。作为全局 fallback 默认值
- **v1.7.0 变更**：移除 `qwen_llm`（Qwen 3.6 Plus）模块级实例。系统默认只配置一个 DeepSeek 大模型，子智能体模型通过 Provider/AIModel 表或 `resolve_model()` 动态选择
- 主智能体和子智能体的模型均可通过 Provider/AIModel 表动态覆盖，模块级 `llm` 仅作为 fallback

#### `em.py` — DashScope Embeddings

```python
from langchain_openai import OpenAIEmbeddings
from agent.config import settings

embeddings = OpenAIEmbeddings(
    model=settings.DASHSCOPE_EMBEDDING,
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.DASHSCOPE_BASE_URL,
)
```

### 4.4 上下文模块 — `agent/context`

**职责：** 定义传递到 Agent 图中的运行时上下文数据结构。

#### `context.py`

```python
from dataclasses import dataclass

@dataclass
class Context:
    server_info: str
    user_id: str
```

- **`server_info`**：服务端标识字符串（当前固定为 `"ke_hermes_server"`）
- **`user_id`**：当前请求用户的 ID（从 JWT Token 中提取），用于 Backend namespace 路由、沙盒选择和记忆隔离

Context 实例在每次 Chat API 调用时创建，通过 `get_graph().ainvoke()` 的 `context` 参数传入 Agent 图。

### 4.5 智能体图 — `agent/graph.py`（v1.6.0 重构）

**职责：** 管理 Agent 图的完整生命周期（初始化 → 运行 → 关闭），支持双检查点后端（SQLite / PostgreSQL）+ 双 Store 后端（InMemory / PostgreSQL），集成 SandboxManager 每用户沙盒管理、数据库驱动的主智能体工厂。

#### 生命周期架构

```python
import aiosqlite
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.store.memory import InMemoryStore

from agent.config import settings
from agent.mainagents import create_main_agent
from agent.sandbox.sandbox_manager import SandboxManager

_graph = None
_conn_pool = None
_checkpointer = None
_store = None
_sandbox_manager = None

def get_graph():
    if _graph is None:
        raise RuntimeError("图未初始化，请先调用 init_graph()。")
    return _graph

def get_checkpointer():
    if _checkpointer is None:
        raise RuntimeError("检查点未初始化，请先调用 init_graph()。")
    return _checkpointer

async def init_graph():
    global _graph, _conn_pool, _checkpointer, _store, _sandbox_manager
    backend = settings.CHECKPOINT_BACKEND

    if backend == "sqlite":
        conn = await aiosqlite.connect(settings.CHECKPOINT_DB_PATH)
        _checkpointer = AsyncSqliteSaver(conn)
        _store = InMemoryStore()
    elif backend == "postgres":
        _conn_pool = AsyncConnectionPool(
            conninfo=settings.CHECKPOINT_DB_URL,
            open=False,
            kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        )
        await _conn_pool.open()
        _checkpointer = AsyncPostgresSaver(_conn_pool)
        await _checkpointer.setup()
        _store = AsyncPostgresStore(_conn_pool)
        await _store.setup()
    else:
        raise ValueError(f"未知的 CHECKPOINT_BACKEND: '{backend}'")

    # v1.6.0：创建 SandboxManager（每用户沙盒管理）替代单个沙盒
    _sandbox_manager = SandboxManager(
        extra_domains=settings.sandbox_allowed_domains_list,
    )
    _sandbox_manager.start_cleanup()

    # v1.6.0：委托给 main_agent.py 工厂函数（数据库驱动动态构建）
    _graph = await create_main_agent(
        checkpointer=_checkpointer,
        store=_store,
        sandbox_manager=_sandbox_manager,
    )

async def shutdown_graph():
    global _conn_pool, _sandbox_manager
    if _sandbox_manager is not None:
        _sandbox_manager.shutdown()       # v1.6.0：关闭所有用户沙盒
        _sandbox_manager = None
    if _conn_pool is not None:
        await _conn_pool.close()
        _conn_pool = None
```

**v1.6.0 架构变更要点：**

1. **SandboxManager 替代单个沙盒**：不再创建单个全局沙盒，改为 `SandboxManager` 管理每用户独立沙盒池（TTL + 健康检查 + 后台清理）
2. **create_main_agent 工厂**：Agent 图构建逻辑迁移到 `main_agent.py` 的 `create_main_agent()` 工厂函数中，从数据库查询配置动态构建
3. **shutdown_graph 增强**：关闭时先调用 `_sandbox_manager.shutdown()` 清理所有用户沙盒，再关闭数据库连接池

**检查点双后端设计（不变）：**

| 后端         | CHECKPOINT_BACKEND | 实现类                  | Store 实现          | 适用场景         |
| ---------- | ------------------ | -------------------- | ----------------- | ------------ |
| SQLite     | `sqlite`           | `AsyncSqliteSaver`   | `InMemoryStore`   | 开发环境 / 单机部署  |
| PostgreSQL | `postgres`         | `AsyncPostgresSaver` | `AsyncPostgresStore` | 生产环境 / 多实例部署 |

### 4.6 Agent 共享工具 — `agent/common.py`（v1.7.0 新增）

**文件：** `agent/common.py`

**职责：** 提供 Agent 子系统共享的工具函数——工具名称解析和 LLM 模型动态加载。作为外观模式（Facade）封装底层复杂逻辑。

#### `get_tool_registry()` — 工具注册表

```python
def get_tool_registry() -> dict:
    """构建工具名称到可调用函数的映射字典。"""
    from agent.tools import get_datetime, http_request, tavily_search
    return {
        "get_datetime": get_datetime,
        "http_request": http_request,
        "tavily_search": tavily_search,
    }
```

#### `resolve_model()` — 模型动态加载器

```python
async def resolve_model(
    provider_id: str | None,
    model_id: str | None,
    fallback_to_settings: bool = True,
):
    """从数据库动态加载 LLM 模型实例。

    1. 若提供了 provider_id 和 model_id，从 Provider + AIModel 表查询配置
    2. 解密 api_key（Fernet），构造 ChatOpenAI 实例
    3. 若查询失败且 fallback_to_settings=True，回退到默认 llm
    4. 若查询失败且 fallback_to_settings=False，抛出异常
    """
```

**设计要点：**
- **外观模式**：封装了跨表查询 → 解密 → 模型构造的复杂流程，对调用方暴露单一函数接口
- **灵活回退**：数据库配置优先，缺失时自动回退到 `agent.models.llm` 默认值
- **多调用方**：被 `AgentBuilder.with_model()` 和 `subagents_operate.py` 共同使用

---

### 4.7 主智能体工厂 — `agent/mainagents`（v1.7.0 重构）

**文件：** `agent/mainagents/main_agent.py`

**职责：** 从数据库查询智能体配置，委托给 `AgentBuilder` 构建主智能体图。

#### v1.7.0 重构

```python
async def create_main_agent(*, checkpointer, store, sandbox_manager):
    """主智能体工厂——委托给 AgentBuilder 构建。

    v1.7.0 重构：原 118 行内联构建逻辑迁移至 AgentBuilder 建造者模式。
    """
    from agent.builders.agent_builder import create_main_agent_v2
    return await create_main_agent_v2(
        checkpointer=checkpointer,
        store=store,
        sandbox_manager=sandbox_manager,
    )
```

**v1.7.0 变更：**
- `create_main_agent()` 从内联 118 行构建逻辑简化为对 `AgentBuilder` 的委托调用
- 原内联的 DB 查询 → 模型解析 → 工具注册 → 子智能体加载 → Backend 组装 → 中间件挂载流程全部迁移至 `AgentBuilder`

---

### 4.8 Agent 建造者 — `agent/builders`（v1.7.0 新增）

**文件：** `agent/builders/agent_builder.py`

**职责：** 用建造者模式（Builder Pattern）将主智能体的复杂构建过程分解为 9 个可组合、可验证的步骤。

#### `AgentBuilder` 类

```python
class AgentBuilder:
    """分步构建 Deep Agent 的建造者。

    将原来 118 行的 create_main_agent() 分解为独立的、可测试的构建步骤。
    每个 with_* 方法返回 self 以支持链式调用。
    """

    def __init__(self):
        self._agent_info = None          # DB 查询结果
        self._model = None               # ChatOpenAI 实例
        self._tools = []                 # 可调用工具函数列表
        self._system_prompt = ""         # 系统提示词
        self._subagents = []             # 子智能体列表
        self._sandbox_manager = None     # 沙盒管理器
        self._sandbox_backend = None     # 沙盒后端
        self._backend = None             # 组合后端
        self._memory = []                # 记忆路径列表
        self._middleware = []            # 中间件列表

    async def with_agent_from_db(self, db) -> "AgentBuilder": ...
    async def with_model(self) -> "AgentBuilder": ...
    async def with_tools(self) -> "AgentBuilder": ...
    def with_system_prompt(self, default=None) -> "AgentBuilder": ...
    async def with_subagents(self) -> "AgentBuilder": ...
    def with_sandbox(self, sandbox_manager=None) -> "AgentBuilder": ...
    def with_backend(self) -> "AgentBuilder": ...
    def with_memory(self) -> "AgentBuilder": ...
    def with_middleware(self) -> "AgentBuilder": ...
    def build(self, checkpointer=None, store=None): ...
```

#### 构建流程

```python
agent = await (
    AgentBuilder()
    .with_agent_from_db(db)        # 1. 查询活跃主智能体
    .with_model()                  # 2. 解析 LLM（Provider/AIModel → ChatOpenAI）
    .with_tools()                  # 3. 工具名称 → 可调用函数
    .with_system_prompt()          # 4. 设置系统提示词
    .with_subagents()              # 5. 动态加载子智能体
    .with_sandbox(sandbox_manager) # 6. 每用户沙盒后端
    .with_backend()                # 7. CompositeBackend 三层路由
    .with_memory()                 # 8. 记忆路径
    .with_middleware()             # 9. SkillSandboxSyncMiddleware
    .build(checkpointer, store)    # 10. 组装 deep agent
)
```

**设计要点：**
- **步骤验证**：关键步骤（如 `with_model()`）在运行时检查前置条件（`with_agent_from_db()` 必须先调用），失败抛出 `RuntimeError`
- **可选注入**：`with_sandbox()` 支持外部传入 `SandboxManager`（由调用方管理生命周期）或内部自动创建
- **便利函数**：`create_main_agent_v2()` 封装 Builder 的标准调用流程，保持与原 `create_main_agent()` 相同签名

#### CompositeBackend 三层路由（不变）

| 路由               | Backend                   | namespace / root                         | 说明                      |
| ---------------- | ------------------------- | ---------------------------------------- | ----------------------- |
| `/memories/`     | `StoreBackend`            | `(user_id,)`                             | 用户级记忆隔离              |
| `/skills/`       | `FilesystemBackend`       | `settings.SKILLS_ROOT`，virtual_mode=True | 技能文件虚拟文件系统         |
| default (其他路径)   | `UserAwareSandboxBackend` | —                                        | 用户感知沙盒后端             |

---

### 4.9 子智能体模块 — `agent/subagents`

**职责：** 提供子智能体的动态加载。v1.6.0 新增 `subagents_operate.py` 实现从数据库动态加载子智能体。

#### `subagents_operate.py` — 动态子智能体加载器（v1.6.0 新增）

```python
async def create_subagents(sandbox_manager):
    """从数据库查询活跃子智能体，动态构建子智能体列表。"""
    from db.engine import async_session
    from api.providers.service import decrypt_api_key

    async with async_session() as session:
        # 查询 type="sub" 且 status="active" 的 Agent
        sub_agents = await _query_active_sub_agents(session)

        result = []
        for agent in sub_agents:
            # 1. 解析模型（按 provider_id/model_id 或 fallback 到 qwen_llm）
            model = await _resolve_model(session, agent)

            # 2. 解析工具（按名称从注册表查找）
            tools = _resolve_tools(agent.tools)

            # 3. 构建子智能体字典
            result.append({
                "name": agent.name,
                "description": agent.description,
                "tools": tools,
                "model": model,
                "system_prompt": agent.system_prompt or "你是一个智能助手。",
                "skills": [f"/skills/{agent.id}/"],
            })

        return result
```

**设计要点：**
- **本系统**：通过 `parent_id` 字段建立主/子智能体层级关系
- **动态加载**：子智能体从数据库 `Agent` 表动态查询，非硬编码
- **独立模型**：每个子智能体可独立配置 Provider + AIModel，默认使用 `qwen_llm`
- **独立技能目录**：每个子智能体有独立的 `/skills/{agent_id}/` 路径
- **工具独立**：每个子智能体可配置独立的工具列表

### 4.10 Agent 工具集 — `agent/tools`

**文件：** `agent/tools/__init__.py`（v1.6.0 重构）

**v1.6.0 变更**：工具集从空列表扩展为 3 个可调用工具函数，供子智能体使用。

```python
from agent.tools.get_datetime import get_datetime
from agent.tools.http_request import http_request
from agent.tools.tavily_search import tavily_search

__all__ = ["get_datetime", "http_request", "tavily_search"]
```

| 工具              | 文件                   | 说明                                                     |
| --------------- | -------------------- | ------------------------------------------------------ |
| `get_datetime`  | `get_datetime.py`    | 返回时区感知的当前日期时间，支持 `Asia/Shanghai` 等 IANA 时区别名        |
| `http_request`  | `http_request.py`    | 发起 HTTP/HTTPS 请求，含 SSRF 防护（禁止内网 IP 访问）                |
| `tavily_search` | `tavily_search.py`   | Tavily 互联网搜索，支持 depth/topic/time_range/include_answer 参数 |

- `tavily_search` 支持高级参数：搜索深度（basic/advanced）、主题分类（general/news/finance）、时间范围（day/week/month/year）、AI 总结答案
- `http_request` 内置 SSRF 防护，禁止访问 127.0.0.0/8、10.0.0.0/8、172.16.0.0/12、192.168.0.0/16 等内网地址
- `get_datetime` 支持常见时区别名（如 `china` → `Asia/Shanghai`）

### 4.11 Chat API — 对话与流式接口

**文件：** `api/agent/agent_api.py`（已实现）

**路由前缀：** `/api`

| 接口                 | 方法   | 请求体                                          | 响应体                                                                | 状态  |
| ------------------ | ---- | -------------------------------------------- | ------------------------------------------------------------------ | --- |
| `/api/chat`        | POST | `{"message":"string","thread_id?":"string"}` | `{"response":"string","thread_id":"string"}`                       | 已实现 |
| `/api/chat/stream` | POST | `{"message":"string","thread_id?":"string"}` | SSE `data:{"token":"..."}\n\n` + 结束 `data:{"thread_id":"..."}\n\n` | 已实现 |

#### 数据模型

```python
class ChatRequest(BaseModel):
    user_id: str | None = 'user_123'   # TODO: 过渡方案，实际由 JWT 注入
    thread_id: str | None = None
    message: str = Field(min_length=1)

class ChatResponse(BaseModel):
    thread_id: str
    response: str

class StreamToken(BaseModel):
    token: str
```

#### `/api/chat` — 普通对话（v1.6.0 无变更）

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    is_new = not req.thread_id
    thread_id = req.thread_id or str(uuid7())
    config = {"configurable": {"thread_id": thread_id}}
    context = Context(server_info="ke_hermes_server", user_id=user_id)

    result = await get_graph().ainvoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config,
        context=context
    )

    if is_new:
        await create_conversation(db, user_id, thread_id, req.message)

    final_message = result["messages"][-1]
    return ChatResponse(response=final_message.content, thread_id=thread_id)
```

**v1.6.0 通过 `context.user_id`**，`UserAwareSandboxBackend` 在内部自动定位到对应用户的沙盒实例。

### 4.12 Conversation API — 对话历史 CRUD

**文件：** `api/conversation/conversation_api.py`

**接口不变，保持 4 个**：列表、消息详情、重命名、删除。路由实现与 v1.5.0 一致。

### 4.11 Auth API — 认证授权模块

**保持不变**，8 个接口，实现逻辑与 v1.5.0 一致。

### 4.12 Captcha API — 验证码模块

**保持不变**，4 个接口，实现逻辑与 v1.5.0 一致。

### 4.13 OAuth API — 第三方登录模块

**保持不变**，2 个接口，实现逻辑与 v1.5.0 一致。

### 4.14 SMS API — 短信服务模块

**保持不变**，1 个接口，实现逻辑与 v1.5.0 一致。

### 4.15 Email API — 邮箱验证码模块

**保持不变**，1 个接口，实现逻辑与 v1.5.0 一致。

### 4.16 MCP API — MCP 广场模块

**保持不变**，4 个接口，12 个种子工具，实现逻辑与 v1.5.0 一致。

### 4.17 Skills API — 技能管理模块

**基本不变**，9 个接口，v1.6.0 变更：

- **种子数据**：新增 `seed_builtin_skills()` 函数，预置 5 个内置技能（network_search、code_interpreter、image_generation、data_analysis、file_management），在 lifespan 阶段自动调用
- **Skill 模型变更**：见 5.1 节—`validation_errors` 类型从 `dict|None`(JSON) 变更为 `str`(Text)，`name` 从 String(128) 变更为 String(64)

### 4.18 Agents API — 智能体管理模块

**文件：** `api/agents/agents_api.py`、`schemas.py`、`service.py`

**路由前缀：** `/api/agents`

#### API 接口（v1.6.0：16 个接口）

| 接口 | 方法 | 请求体 | 响应体 | 说明 |
|------|------|--------|--------|------|
| `/api/agents` | GET | — | `ApiResponse[AgentListResponse]` | 获取当前用户所有智能体（首访自动创建默认主智能体） |
| `/api/agents/{agent_id}` | GET | — | `ApiResponse[AgentInfo]` | 获取单个智能体详情（含子智能体列表 + 技能列表） |
| `/api/agents` | POST | `AgentCreateRequest` | `ApiResponse[AgentInfo]` | 创建新智能体（主智能体或子智能体） |
| `/api/agents/{agent_id}` | PUT | `AgentUpdateRequest` | `ApiResponse[AgentInfo]` | 更新智能体（名称/描述/system_prompt/模型关联）（v1.6.0 新增） |
| `/api/agents/{agent_id}` | DELETE | — | `ApiResponse[None]` | 删除智能体（主智能体级联删除子智能体） |
| `/api/agents/{agent_id}/status` | PATCH | — | `ApiResponse[AgentInfo]` | 切换智能体激活/停用状态 |
| `/api/agents/{agent_id}/clone` | POST | — | `ApiResponse[AgentInfo]` | 克隆智能体（名称去重，含文件内容） |
| `/api/agents/{agent_id}/config` | POST | `AgentConfigRequest` | `ApiResponse[AgentInfo]` | 添加配置项（tool/prompt/file/subagent，skill 另处理） |
| `/api/agents/{agent_id}/config` | DELETE | `AgentConfigRequest` | `ApiResponse[AgentInfo]` | 移除配置项（subagent 类型会删除子智能体） |
| `/api/agents/{agent_id}/config` | PUT | `AgentConfigUpdateRequest` | `ApiResponse[AgentInfo]` | 更新配置项（文件重命名/修改描述） |
| `/api/agents/{agent_id}/file-descriptions` | GET | — | `ApiResponse[list[dict]]` | 获取智能体所有文件的描述列表 |
| `/api/agents/{agent_id}/files/{filename}` | GET | — | `ApiResponse[AgentFileContent]` | 获取文件内容（首访自动创建空记录） |
| `/api/agents/{agent_id}/files/{filename}` | PUT | `AgentFileUpdateRequest` | `ApiResponse[AgentFileContent]` | 保存文件内容（upsert） |
| `/api/agents/{agent_id}/skills` | GET | — | `ApiResponse[list[SkillBrief]]` | 获取智能体关联的技能列表（v1.6.0 新增） |
| `/api/agents/{agent_id}/skills` | POST | `AgentAddSkillRequest` | `ApiResponse[AgentInfo]` | 添加技能到智能体（v1.6.0 新增） |
| `/api/agents/{agent_id}/skills/{skill_id}` | DELETE | — | `ApiResponse[None]` | 从智能体移除技能（v1.6.0 新增） |
| `/api/agents/{agent_id}/cron-jobs` | GET | — | `ApiResponse[list[CronJobBrief]]` | 获取智能体的定时任务列表（v1.6.0 新增） |

共 **17 个接口**（v1.5.0 为 12 个，v1.6.0 新增 PUT 更新 + 技能关联子路由 + CronJob 查询），均需 JWT 鉴权。

#### 数据模型（v1.6.0 更新，`api/agents/schemas.py`）

```python
class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    system_prompt: str = ""
    parent_id: str | None = None
    provider_id: str | None = None       # v1.6.0 新增
    model_id: str | None = None          # v1.6.0 新增

class AgentUpdateRequest(BaseModel):      # v1.6.0 新增
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    system_prompt: str = ""
    provider_id: str | None = None
    model_id: str | None = None

class AgentInfo(BaseModel):
    id: str; name: str; type: str; status: str
    description: str
    tools: list[str]
    skills: list[SkillBrief]             # v1.6.0：从 list[str] 变更为 SkillBrief 对象列表
    system_prompt: str                   # v1.5.0 为 prompts: list[str]
    files: list[str]
    sub_agents: list[str] = []
    parent_id: str | None = None
    provider_id: str | None = None       # v1.6.0 新增
    model_id: str | None = None          # v1.6.0 新增
    undeletable: bool = False
    created_at: datetime; updated_at: datetime

class SkillBrief(BaseModel):             # v1.6.0 新增
    id: str; name: str; description: str
    category: str; icon: str; enabled: bool

class AgentAddSkillRequest(BaseModel):   # v1.6.0 新增
    skill_id: str

class CronJobBrief(BaseModel):           # v1.6.0 新增
    id: str; agent_id: str; name: str; description: str
    cron_expression: str; cron_label: str; status: str
    target_type: str; target: str
    last_run: datetime | None; next_run: datetime | None
    tags: list[str]; created_at: datetime; updated_at: datetime
```

#### 核心业务逻辑（v1.6.0 更新）

**智能体 CRUD（v1.6.0 变更）：**
- `list_agents()`: 查询所有智能体（不再按 user_id 过滤—Agent 模型已移除 user_id 字段）。首次访问时自动创建默认主智能体
- `get_agent()`: 按 agent_id 查询，通过 `AgentSkill` 关联表加载技能列表（SkillBrief 对象），通过 `AgentTool` 关联表加载工具名称列表
- `create_agent()`: 创建智能体，支持 `system_prompt`/`provider_id`/`model_id` 字段
- **`update_agent()`**（v1.6.0 新增）：按 agent_id 更新名称/描述/system_prompt/模型关联
- `delete_agent()`: 级联删除子智能体 + AgentFile + AgentSkill + AgentTool
- `clone_agent()`: 深拷贝 system_prompt 和文件内容，名称自动追加"(副本)"

**技能关联（v1.6.0 新增）：**
- `list_agent_skills()`: 通过 `AgentSkill` 关联表查询智能体的技能列表
- `add_agent_skill()`: 验证技能存在 + 唯一性检查 → 写入 `AgentSkill` 表
- `remove_agent_skill()`: 删除指定关联记录

**工具关联：** 通过 `AgentTool` 关联表管理（替代 v1.5.0 的 JSON 数组方式）

**CronJob 查询：** 通过 `CronJob.agent_id` 过滤，按 `next_run` 排序

### 4.19 Providers API — 模型管理模块

**文件：** `api/providers/providers_api.py`、`schemas.py`、`service.py`

**9 个接口不变**（与 v1.5.0 一致）。

**v1.6.0 变更：**
- **API Key 加密**：`create_provider()` 和 `update_provider()` 使用 Fernet 对称加密存储 api_key。解密函数 `decrypt_api_key()` 被 `main_agent.py` 和 `subagents_operate.py` 调用
- **明文迁移**：`migrate_plaintext_api_keys()` 在 lifespan 阶段执行，将存量的明文 api_key 迁移为加密形式
- **加密密钥持久化**：Fernet 密钥自动生成并持久化到 `.fernet_key` 文件，确保重启后可解密

### 4.20 Tools API — 工具管理模块

**文件：** `api/tools/tools_api.py`、`schemas.py`、`service.py`（v1.6.0 新增）

**路由前缀：** `/api/tools`

#### API 接口

| 接口 | 方法 | 请求体 | 响应体 | 说明 |
|------|------|--------|--------|------|
| `/api/tools/list` | GET | query: source?, category?, status?, keyword?, page?, page_size? | `ApiResponse[{tools[], total}]` | 工具列表（分页 + 筛选） |
| `/api/tools/by-agent/{agent_id}` | GET | — | `ApiResponse[list[ToolInfo]]` | 获取某个智能体的工具列表 |
| `/api/tools/{tool_id}` | GET | — | `ApiResponse[ToolInfo]` | 获取工具详情 |
| `/api/tools` | POST | `ToolCreateRequest` | `ApiResponse[ToolInfo]` | 创建第三方工具 |
| `/api/tools/{tool_id}` | PUT | `ToolUpdateRequest` | `ApiResponse[ToolInfo]` | 更新工具 |
| `/api/tools/{tool_id}/toggle` | PATCH | — | `ApiResponse[ToolInfo]` | 切换工具启用/禁用 |
| `/api/tools/{tool_id}` | DELETE | — | `ApiResponse[None]` | 删除第三方工具（内置工具不可删除） |

共 **7 个接口**，均需 JWT 鉴权。

#### 内置工具种子数据（11 个）

`seed_builtin_tools()` 在 lifespan 阶段执行，幂等创建 11 个预置工具：

| 工具名称 | 分类 | 来源 | 说明 |
|---------|------|------|------|
| execute_code | code_execution | builtin | 代码执行（Python/Shell） |
| shell_command | dev_tools | builtin | Shell 命令执行 |
| http_request | network | builtin | HTTP/HTTPS 请求 |
| tavily_search | search | builtin | Tavily 互联网搜索 |
| web_scraper | search | builtin | 网页内容抓取 |
| read_file | file_management | builtin | 文件读取 |
| write_file | file_management | builtin | 文件写入 |
| sql_query | database | builtin | SQL 数据库查询 |
| get_datetime | utility | builtin | 日期时间获取 |
| image_generate | image | builtin | AI 图像生成 |
| text_embedding | ai | builtin | 文本向量化 |

### 4.23 Knowledge Base API — 知识库管理模块（v1.7.0 新增）

**文件：** `api/knowledge_base/`（11 个文件，包含 4 个子路由 + 状态机 + 观察者 + 调度器）

**路由前缀：** `/api/knowledge-bases`

**职责：** 完整的 RAG 知识库子系统——知识库 CRUD、文档上传与索引、知识图谱实体关系提取、分块管理。

#### 子模块路由

| 子路由 | 文件 | 前缀 | 接口数 | 说明 |
|--------|------|------|--------|------|
| kb_router | `kb_api.py` | `/api/knowledge-bases` | 10 | 知识库 CRUD + 统计 + 模型/提供商发现 + 重索引 |
| doc_router | `doc_api.py` | `/api/knowledge-bases/{kb_id}/documents` | 5 | 文档上传、列表、详情、删除、重试 |
| chunk_router | `chunk_api.py` | `/api/knowledge-bases/{kb_id}/documents/{doc_id}/chunks` | 5 | 分块列表、详情、更新、删除、批量操作 |
| graph_router | `graph_api.py` | `/api/knowledge-bases/{kb_id}/graph` | 3 | 实体/关系查询、实体详情、图谱重提取 |

#### 文档索引状态机（State 模式，`doc_state.py`）

实现了 8 种状态的文档索引生命周期：

```
Queued → Parsing → Chunking → Embedding → BM25 → Extracting → Indexed
                                                          ↘ Failed（任意阶段失败）
```

**关键类：**

```python
@dataclass
class IndexingContext:
    """状态模式的 Context 角色——持有当前状态、进度、中间产物。"""
    doc_id: str; kb_id: str; file_path: str; file_type: str; config: dict
    current_state: DocState | None = None
    status: str = "queued"; progress: int = 0
    documents: list; chunks: list; embeddings: list
    entities_count: int = 0; relations_count: int = 0

    async def transition_to(self, state, status, progress): ...

class DocState(ABC):
    """抽象状态接口。"""
    @abstractmethod
    async def handle(self, ctx, pipeline): ...

class QueuedState(DocState): ...    # → ParsingState
class ParsingState(DocState): ...   # → ChunkingState（调用文档加载器）
class ChunkingState(DocState): ...  # → EmbeddingState（调用切片策略）
class EmbeddingState(DocState): ... # → BM25State（调用嵌入模型）
class BM25State(DocState): ...      # → ExtractingState（写入向量库）
class ExtractingState(DocState): ... # → IndexedState（实体关系提取）
class IndexedState(DocState): ...   # 终态：索引完成
class FailedState(DocState): ...    # 终态：索引失败
```

#### 索引流水线（`doc_service.py`）

**`IndexingPipeline`** 作为模板方法模式的实现，持有所有 RAG 组件并通过状态机驱动文档处理：

```python
class IndexingPipeline:
    def __init__(self, loader_registry, chunk_registry, embedding_model,
                 vector_store, graph_service):
        self._observers: list[ProgressObserver] = []

    async def execute(self, task: IndexingTask): ...
    async def _run_state_machine(self, ctx: IndexingContext): ...
```

**观察者模式**：`ProgressObserver` (ABC) → `DatabaseProgressObserver` + `LoggingProgressObserver`，在索引进度变化时通知 UI 轮询。

**`IndexingScheduler`**（单例模式）：维护异步任务队列，控制最大并发索引数（`INDEXING_MAX_CONCURRENT`）。

#### 核心业务逻辑

**知识库 CRUD（`service.py`）：**
- `list_kbs()`: 分页列表 + 搜索
- `get_kb_stats()`: 聚合统计（文档数/分块数/实体数/关系数/存储大小）
- `create_kb()`: 创建知识库 + 自动创建向量库 collection
- `delete_kb()`: 级联删除文档 + 实体 + 关系 + 向量库 collection
- `reindex_kb()`: 更新索引配置 + 重建向量库 + 重新索引全部文档

**文档管理（`doc_service.py`）：**
- `upload_documents()`: 批量上传（最多 20 个文件）→ 入队索引
- `list_documents()`: 分页列表 + 状态筛选 + 搜索
- `get_document()`: 详情含 8 阶段流水线状态
- `delete_document()`: 级联删除向量 + 源文件
- `retry_document()`: 重试失败文档

**知识图谱（`graph_service.py`）：**
- `GraphExtractionService` 使用 `langextract` 框架 + DeepSeek LLM 提取实体和关系
- 实体类型：人物、组织、产品、概念、算法、地点、时间、事件（8 种）
- 关系去重：按 (from_entity, to_entity, label) 三元组去重
- 失败容错：实体抽取失败不阻塞索引，文档仍标记为已索引

**分块管理（`chunk_service.py`）：**
- 支持单个分块的查看（含前后上下文）、更新（重嵌入）、删除
- 支持批量操作（save_all / delete）

#### 数据模型（`schemas.py`）

核心 `IndexConfigSchema` 包含 15 个索引配置字段：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| chunk_strategy | str | "recursive" | 切片策略（fixed/recursive/semantic/markdown） |
| chunk_size | int | 1000 | 切片大小 |
| chunk_overlap | int | 200 | 切片重叠 |
| embedding_model | str | "" | 嵌入模型名称 |
| embedding_dim | int | 1024 | 嵌入维度 |
| sparse_algo | str | "bm25" | 稀疏检索算法 |
| bm25_k1 | float | 1.2 | BM25 k1 参数 |
| bm25_b | float | 0.75 | BM25 b 参数 |
| entity_model | str | "" | 实体抽取模型 |
| relation_model | str | "" | 关系抽取模型 |
| enable_graph | bool | true | 是否启用图谱提取 |
| reranker_model | str | "" | 重排序模型 |
| enable_reranker | bool | false | 是否启用重排序 |
| top_k | int | 5 | 检索返回数量 |
| hybrid_alpha | float | 0.5 | 混合检索权重 |

### 4.24 Sandbox — 沙盒代码执行模块

**文件：** `agent/sandbox/`（v1.6.0 重构，新增 2 个文件）

#### `sandbox_manager.py` — 沙盒管理器（v1.6.0 新增）

`SandboxManager` 管理每用户的OpenSandbox 沙盒生命周期。

```python
class SandboxManager:
    def __init__(self, *, extra_domains: list[str] | None = None):
        self._sandboxes: dict[str, SandboxEntry] = {}  # user_id → SandboxEntry
        self._lock = threading.Lock()                  # 线程安全
        self._extra_domains = extra_domains or []
        self._cleanup_thread = None

    def get_or_create(self, user_id: str) -> SandboxSync:
        """获取或创建用户的沙盒（含健康检查 + 续期）。"""
        with self._lock:
            entry = self._sandboxes.get(user_id)
            if entry is not None:
                # 健康检查 + 续期
                if entry.sandbox.is_healthy():
                    entry.sandbox.renew()
                    entry.last_used = time.time()
                    return entry.sandbox
                # 不健康则重建
                entry.sandbox.kill()
            sandbox = _create_sandbox(extra_domains=self._extra_domains)
            self._sandboxes[user_id] = SandboxEntry(sandbox=sandbox, last_used=time.time())
            return sandbox

    def start_cleanup(self):
        """启动后台清理线程（daemon），定期清理过期沙盒。"""
        ...

    def shutdown(self):
        """关闭所有沙盒 + 停止清理线程。"""
        for entry in self._sandboxes.values():
            entry.sandbox.kill()
        self._sandboxes.clear()
```

**关键设计：**
- **每用户独立沙盒**：通过 `user_id` 键隔离
- **TTL 过期**：沙盒在 `SANDBOX_TTL_SECONDS` 秒无使用后自动 kill
- **健康检查**：复用前调用 `sandbox.is_healthy()`，不健康则重建
- **续期**：复用时调用 `sandbox.renew()` 刷新闲置超时
- **后台清理**：daemon 线程按 `SANDBOX_CLEANUP_INTERVAL` 间隔巡检过期沙盒
- **线程安全**：所有字典操作通过 `threading.Lock` 保护
- **graceful shutdown**：`shutdown()` 在 `shutdown_graph()` 中调用

#### `user_aware_sandbox_backend.py` — 用户感知沙盒后端（v1.6.0 新增）

```python
class UserAwareSandboxBackend(BaseSandbox):
    """在每次调用时从 LangGraph runtime context 提取 user_id，委托给 SandboxManager。"""

    def __init__(self, *, sandbox_manager: SandboxManager):
        self._sandbox_manager = sandbox_manager

    def _get_backend(self) -> OpenSandBoxBackend:
        from langgraph.config import get_runtime
        user_id = get_runtime().context.user_id
        sandbox = self._sandbox_manager.get_or_create(user_id)
        return OpenSandBoxBackend(sandbox=sandbox)

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        return self._get_backend().execute(command, timeout=timeout)

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        return self._get_backend().upload_files(files)

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        return self._get_backend().download_files(paths)
```

- 每次操作通过 `get_runtime().context.user_id` 动态获取当前用户
- 委托给 `SandboxManager.get_or_create()` 获取对应沙盒实例

#### `opensandbox_backend.py` — 底层沙盒封装（v1.6.0 无变更）

与 v1.5.0 实现一致：`execute()`、`upload_files()`、`download_files()` 均基于 OpenSandbox API。

#### `opensandbox_operate.py` — 沙盒创建辅助（v1.6.0 无实质变更）

沙盒创建迁移到 `SandboxManager._create_sandbox()` 内部，`opensandbox_operate.py` 保留供直接使用场景。

### 4.25 Middleware — 智能体中间件

**文件：** `agent/middleware/skill_sandbox_sync.py`（v1.6.0 新增）

**职责：** 在每次 Agent 调用前，将智能体的技能文件同步到用户的 OpenSandbox 沙盒中。

#### SkillSandboxSyncMiddleware

```python
class SkillSandboxSyncMiddleware(AgentMiddleware):
    """每次 Agent 调用前同步技能文件到沙盒。"""

    def __init__(self, *, sandbox_manager: SandboxManager):
        self._sandbox_manager = sandbox_manager
        self._synced_sandboxes: set[str] = set()  # 已同步的沙盒 ID（去重）

    async def abefore_agent(self, state, runtime):
        user_id = runtime.context.user_id
        sandbox = self._sandbox_manager.get_or_create(user_id)

        sandbox_id = sandbox.id()
        if sandbox_id in self._synced_sandboxes:
            return  # 同一沙盒已同步，跳过

        # 1. 从 /skills/{agent_id}/ 目录递归读取技能文件
        skills_path = f"/skills/{agent_id}/"  # 从 runtime 获取 agent_id
        files = _read_skills_from_filesystem(skills_path)

        # 2. 上传到沙盒的 /skills/ 路径
        sandbox_backend = OpenSandBoxBackend(sandbox=sandbox)
        sandbox_backend.upload_files(files)

        # 3. 从 SKILL.md frontmatter 提取 network-domains 并应用网络策略
        network_domains = _extract_network_domains(files)
        for domain in network_domains:
            sandbox.egress.allow(domain)

        self._synced_sandboxes.add(sandbox_id)
```

**设计要点：**
- **沙盒维度去重**：通过追踪已同步的 sandbox_id，同一沙盒仅同步一次（避免每次 Agent 调用重复上传）
- **网络策略自动应用**：从技能的 `SKILL.md` YAML frontmatter 中提取 `network-domains` 字段，自动添加到沙盒的 egress 白名单
- **技能隔离**：按 `agent_id` 区分技能目录，不同智能体的技能文件独立管理

---

### 4.26 核心工具层 — `core/` 模块（v1.7.0 扩展）

v1.7.0 在 `core/` 目录下新增装饰器库、分页迭代器和完整 RAG 基础设施。

#### 4.26.1 装饰器库 — `core/decorators.py`（v1.7.0 新增）

**职责：** 提供可复用的装饰器处理横切关注点，消除 API 层重复的 try/except 模板。

| 装饰器 | 签名 | 用途 |
|--------|------|------|
| `@handle_errors` | `(func=None, *, default_message)` | 统一错误处理：捕获 HTTPException → ApiResponse 格式 |
| `@cached(ttl)` | `(ttl: int = 60)` | API 响应缓存，通过 KeyValueStore 存储 |
| `@retry(max_attempts, backoff_factor)` | `(max_attempts=3, backoff_factor=2.0)` | 指数退避重试，跳过 HTTPException |
| `@log_call(level)` | `(level=logging.DEBUG)` | 自动函数调用日志 |

```python
@handle_errors
async def my_endpoint(...):
    result = await some_service(...)
    return ok(result)

@cached(ttl=300)
async def list_providers(...): ...

@retry(max_attempts=3)
async def call_external_api(...): ...
```

#### 4.26.2 分页迭代器 — `core/pagination.py`（v1.7.0 新增）

**职责：** 统一分页查询逻辑，消除 6+ 个 `list_*` 函数中的重复 offset/limit 代码。

```python
@dataclass
class PageResult:
    items: list; total: int; page: int; page_size: int
    total_pages: int; has_next: bool; has_prev: bool

class PageIterator:
    """封装 offset/limit + 总数查询 + 边界钳位。"""
    def __init__(self, db, query, page, page_size): ...
    async def get_page(self) -> PageResult: ...
```

#### 4.26.3 RAG 核心 — `core/rag/`（v1.7.0 新增，6 个文件）

**`embedding.py`** — 嵌入模型工厂：
- `_DashScopeEmbeddings` 类：适配 DashScope API（10 条/批限制、无 tiktoken 依赖）
- `get_embedding_model()` 工厂：DashScope / OpenAI 兼容两种后端

**`vector_store.py`** — 向量库抽象层（Strategy 模式）：
- `BaseVectorStore` (ABC)：`create_collection` / `add_documents` / `similarity_search` / `bm25_search` / `hybrid_search` 等 11 个抽象方法
- `MilvusVectorStore`：基于 pymilvus 3.0，HNSW COSINE 索引，collection 命名 `kb_{kb_id}`
- `ChromaVectorStore`：支持 PersistentClient 和 HttpClient，实现完整检索（similarity/bm25/hybrid）

**`loaders.py`** — 文档加载器策略/注册表（Strategy + Composite 模式）：
- `DocumentLoaderStrategy` (ABC) + 13 种具体策略：PDF（langchain-opendataloader + PyPDF fallback）、Word、Excel、PPT（python-pptx + unstructured fallback）、CSV、JSON、Markdown、HTML、Text、Image（OCR/Tesseract）
- `FallbackLoaderStrategy`（Composite）：按优先级依次尝试多个策略
- `DocumentLoaderRegistry`：文件类型 → 策略映射
- `create_default_loader_registry()`：预注册全部 13 种格式

**`splitters.py`** — 文本切片策略/注册表（Strategy 模式）：
- `ChunkStrategy` (ABC) + 5 种策略：Fixed（CharacterTextSplitter）、Recursive（RecursiveCharacterTextSplitter）、Semantic（SemanticChunker）、Markdown（MarkdownHeaderTextSplitter）、Agentic（LLM 驱动，存根）
- `ChunkStrategyRegistry`：策略名 → 策略映射
- `create_chunk_registry()`：条件注册（semantic 仅在 embedding 可用时注册）

**`bm25_index.py`** — BM25 关键词索引器，委托给 vector_store 的 bm25_search。

---

## 5. 数据存储设计

### 5.1 业务数据库 — SQLAlchemy ORM（v1.7.0：19 个模型）

#### User 模型 — `db/models/user.py`（不变）

```python
class User(Base):
    __tablename__ = "users"
    id: str (UUID, PK), username: str (unique), nickname: str
    password_hash: str, phone: str (unique), email: str (unique)
    avatar: str, workspace_id: str, is_active: bool
    created_at: datetime, updated_at: datetime
```

#### UserOAuth 模型 — `db/models/user_oauth.py`（不变）

`(provider, open_id)` 复合唯一约束，与 v1.5.0 一致。

#### LoginRecord 模型 — `db/models/login_record.py`（不变）

#### Conversation 模型 — `db/models/conversation.py`（不变）

#### McpTool 模型 — `db/models/mcp_tool.py`（不变）

#### McpInstallation 模型 — `db/models/mcp_installation.py`（不变）

#### Skill 模型 — `db/models/skill.py`（v1.6.0 变更）

```python
class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str]  # UUID PK
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # v1.6.0: String(128)→String(64)
    valid: Mapped[bool] = mapped_column(Boolean, default=False)                # v1.6.0: default=True→False
    source: Mapped[str | None] = mapped_column(String(32), nullable=True, default="local")  # v1.6.0: String(64)→String(32), 新增 default
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    license: Mapped[str | None] = mapped_column(String(64), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_errors: Mapped[str] = mapped_column(Text, default="")          # v1.6.0: dict|None (JSON)→str (Text)
    # v1.6.0 移除: user_id
    created_at: datetime, updated_at: datetime
```

#### Agent 模型 — `db/models/agent.py`（v1.6.0 重大重构）

```python
class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(16), default="sub")       # main / sub
    status: Mapped[str] = mapped_column(String(16), default="inactive") # active / inactive / error
    description: Mapped[str] = mapped_column(Text, default="")
    parent_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, default="")       # v1.6.0: 替代 prompts JSON列表
    files: Mapped[list] = mapped_column(JSON, default=list)
    provider_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # v1.6.0 新增
    model_id: Mapped[str | None] = mapped_column(String(36), nullable=True)     # v1.6.0 新增
    undeletable: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # v1.6.0 新增：关联表关系
    tool_links: Mapped[list[AgentTool]] = relationship(
        "AgentTool", back_populates="agent", cascade="all, delete-orphan"
    )
```

**v1.6.0 变更摘要：**

| v1.5.0 文档 | v1.6.0 实际代码 |
| --- | --- |
| `user_id` (String(36), index) | **已移除** |
| `tools` (JSON 列表) | **已移除** — 改用 `AgentTool` 关联表 |
| `skills` (JSON 列表) | **已移除** — 改用 `AgentSkill` 关联表 |
| `prompts` (JSON 列表) | **已移除** — 改用 `system_prompt` (Text) |
| — | **新增** `system_prompt` (Text) |
| — | **新增** `provider_id` (String(36)) |
| — | **新增** `model_id` (String(36)) |
| — | **新增** `tool_links` 关系映射 |

#### AgentFile 模型 — `db/models/agent_file.py`（不变）

#### AgentSkill 模型 — `db/models/agent_skill.py`（v1.6.0 新增）

```python
class AgentSkill(Base):
    __tablename__ = "agent_skills"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime]
```

- 复合主键 `(agent_id, skill_id)`，双方均设置 CASCADE 删除

#### AgentTool 模型 — `db/models/agent_tool.py`（v1.6.0 新增）

```python
class AgentTool(Base):
    __tablename__ = "agent_tools"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    tool_id: Mapped[str] = mapped_column(String(36), ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime]

    # 双向关系
    agent: Mapped[Agent] = relationship("Agent", back_populates="tool_links")
    tool: Mapped[Tool] = relationship("Tool", back_populates="agent_links")
```

- 复合主键 `(agent_id, tool_id)`，双方 CASCADE 删除，双向关系映射

#### Tool 模型 — `db/models/tool.py`（v1.6.0 新增）

```python
class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(64), default="")
    category: Mapped[str] = mapped_column(String(32), default="")
    source: Mapped[str] = mapped_column(String(16), default="third_party")  # builtin / third_party
    status: Mapped[str] = mapped_column(String(16), default="active")        # active / inactive
    version: Mapped[str] = mapped_column(String(16), default="1.0.0")
    author: Mapped[str] = mapped_column(String(64), default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    params: Mapped[list] = mapped_column(JSON, default=list)  # 参数定义列表
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    agent_links: Mapped[list[AgentTool]] = relationship("AgentTool", back_populates="tool", cascade="all, delete-orphan")
```

#### CronJob 模型 — `db/models/cron_job.py`（v1.6.0 新增）

```python
class CronJob(Base):
    __tablename__ = "cron_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    cron_expression: Mapped[str] = mapped_column(String(64), nullable=False)
    cron_label: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(16), default="active")  # active / paused / error
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)  # chat / tool / skill
    target: Mapped[str] = mapped_column(Text, nullable=False)            # 目标消息/工具名/技能名
    last_run: Mapped[datetime | None]
    next_run: Mapped[datetime | None]
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

#### KnowledgeBase 模型 — `db/models/knowledge_base.py`（v1.7.0 新增）

```python
class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="active")
    config: Mapped[dict] = mapped_column(JSON, default=dict)       # IndexConfigSchema
    tags: Mapped[list] = mapped_column(JSON, default=list)
    docs_count: Mapped[int] = mapped_column(Integer, default=0)
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)
    entities_count: Mapped[int] = mapped_column(Integer, default=0)
    relations_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime]; updated_at: Mapped[datetime]
```

#### KnowledgeBaseDocument 模型 — `db/models/knowledge_base_document.py`（v1.7.0 新增）

```python
class KnowledgeBaseDocument(Base):
    __tablename__ = "knowledge_base_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    kb_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)   # pdf / docx / pptx / xlsx / csv / json / md / html / txt
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued / parsing / chunking / embedding / bm25 / extracting / indexed / failed
    progress: Mapped[int] = mapped_column(Integer, default=0)
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)
    entities_count: Mapped[int] = mapped_column(Integer, default=0)
    relations_count: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(512), default="")
    uploaded_at: Mapped[datetime]
    indexed_at: Mapped[datetime | None]
    error_message: Mapped[str] = mapped_column(Text, default="")
```

#### KnowledgeBaseEntity 模型 — `db/models/knowledge_base_entity.py`（v1.7.0 新增）

```python
class KnowledgeBaseEntity(Base):
    __tablename__ = "knowledge_base_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    kb_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)   # 人物/组织/产品/概念/算法/地点/时间/事件
    mentions: Mapped[int] = mapped_column(Integer, default=1)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
```

#### KnowledgeBaseRelation 模型 — `db/models/knowledge_base_relation.py`（v1.7.0 新增）

```python
class KnowledgeBaseRelation(Base):
    __tablename__ = "knowledge_base_relations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    kb_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    from_entity: Mapped[str] = mapped_column(String(256), nullable=False)
    to_entity: Mapped[str] = mapped_column(String(256), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)  # 关系类型
    weight: Mapped[float] = mapped_column(Float, default=1.0)
```

#### Provider 模型 — `db/models/provider.py`（v1.6.0 变更）

与 v1.5.0 一致的结构，唯一变更：`api_key` 字段现在存储 **Fernet 加密后的密文**（不再明文），加密/解密通过 `core/security.py` 的 `encrypt_api_key()` / `decrypt_api_key()` 函数处理。

#### AIModel 模型 — `db/models/ai_model.py`（v1.6.0 无变更）

与 v1.5.0 一致。

### 5.2 数据库引擎 — `db/engine.py`（v1.6.0 更新）

v1.6.0 新增 **6 个迁移函数**（`_migrate_agents_drop_user_id`、`_migrate_agents_drop_skills`、`_migrate_skills_drop_user_id`、`_migrate_agents_drop_tools_column`、`_migrate_agents_rename_prompts`、`_migrate_agents_add_provider_model`），在 `init_db()` 的 `Base.metadata.create_all()` 之后执行，处理 SQLite 与 PostgreSQL 的不同 ALTER TABLE 策略。

### 5.3 KeyValueStore — 临时数据

`core/store.py` 不变。Redis 优先，不可用时自动降级为线程安全 MemoryStore。

### 5.4 LangGraph 持久化层

与 v1.5.0 一致，SQLite 和 PostgreSQL 双后端。

---

## 6. 安全设计

### 6.1 密码安全

前端 RSA 公钥加密 → 密文传输 → 后端 RSA 私钥解密 → bcrypt 哈希存储。流程不变。

### 6.2 JWT Token 双 Token 机制

Access Token (2h) + Refresh Token (7d)，流程不变。

### 6.3 Provider API Key 加密（v1.6.0 新增）

```
存储: Fernet 对称加密 → 密文写入 DB
读取: DB 密文 → Fernet 解密 → 运行时使用
```

- Fernet 密钥惰性生成，持久化到 `.fernet_key` 文件
- 存量明文 api_key 在 lifespan 阶段通过 `migrate_plaintext_api_keys()` 自动迁移

### 6.4 登录安全

失败锁定、验证码前置、短信限流，与 v1.5.0 一致。

---

## 7. API 接口总览与前后端对照

### 7.1 完整接口清单（v1.7.0：87+ 接口）

| 接口                              | 方法     | 模块           | 后端实现  | 说明                            |
| ------------------------------- | ------ | ------------ | ----- | ----------------------------- |
| `/api/chat`                     | POST   | agent        | ✅ 已实现 | 普通对话（含 JWT 鉴权 + Context + 用户感知沙盒） |
| `/api/chat/stream`              | POST   | agent        | ✅ 已实现 | 流式对话（SSE）                     |
| `/api/conversations`            | GET    | conversation | ✅ 已实现 | 对话列表                          |
| `/api/conversations/{thread_id}` | GET    | conversation | ✅ 已实现 | 对话消息详情                        |
| `/api/conversations/{thread_id}` | PATCH  | conversation | ✅ 已实现 | 重命名对话                         |
| `/api/conversations/{thread_id}` | DELETE | conversation | ✅ 已实现 | 删除对话 + 检查点                    |
| `/api/auth/public-key`          | GET    | auth         | ✅ 已实现 | 获取 RSA 公钥                     |
| `/api/auth/login/account`       | POST   | auth         | ✅ 已实现 | 账号密码登录                        |
| `/api/auth/login/phone`         | POST   | auth         | ✅ 已实现 | 手机验证码登录                       |
| `/api/auth/register/phone`      | POST   | auth         | ✅ 已实现 | 手机号注册                         |
| `/api/auth/register/email`      | POST   | auth         | ✅ 已实现 | 邮箱注册                          |
| `/api/auth/logout`              | POST   | auth         | ✅ 已实现 | 退出登录                          |
| `/api/auth/refresh`             | POST   | auth         | ✅ 已实现 | 刷新 Token                      |
| `/api/auth/fail-count`          | GET    | auth         | ✅ 已实现 | 查询登录失败次数                      |
| `/api/captcha/slide`            | GET    | captcha      | ✅ 已实现 | 获取滑动拼图                        |
| `/api/captcha/slide/verify`     | POST   | captcha      | ✅ 已实现 | 校验滑动拼图                        |
| `/api/captcha/image`            | GET    | captcha      | ✅ 已实现 | 获取图形验证码                       |
| `/api/captcha/image/verify`     | POST   | captcha      | ✅ 已实现 | 校验图形验证码                       |
| `/api/sms/send`                 | POST   | sms          | ✅ 已实现 | 发送短信验证码                       |
| `/api/email/send`               | POST   | email        | ✅ 已实现 | 发送邮箱验证码                       |
| `/api/oauth/auth-url`           | GET    | oauth        | ✅ 已实现 | 获取 OAuth 授权 URL               |
| `/api/oauth/callback`           | POST   | oauth        | ✅ 已实现 | OAuth 回调处理                    |
| `/api/mcp/tools`                | GET    | mcp          | ✅ 已实现 | MCP 工具列表                      |
| `/api/mcp/tools/{tool_id}`     | GET    | mcp          | ✅ 已实现 | MCP 工具详情                      |
| `/api/mcp/tools/{mcp_id}/install` | POST | mcp          | ✅ 已实现 | 安装 MCP 工具                     |
| `/api/mcp/tools/{tool_id}/uninstall` | DELETE | mcp      | ✅ 已实现 | 卸载 MCP 工具                     |
| `/api/skill/upload_skills`       | POST   | skill        | ✅ 已实现 | 上传技能压缩包                       |
| `/api/skill/list`                | GET    | skill        | ✅ 已实现 | 技能列表（含 5 个内置）              |
| `/api/skill/search`              | GET    | skill        | ✅ 已实现 | 搜索技能                          |
| `/api/skill`                     | POST   | skill        | ✅ 已实现 | 创建技能                          |
| `/api/skill/{skill_id}`          | GET    | skill        | ✅ 已实现 | 技能详情                          |
| `/api/skill/{skill_id}`          | PUT    | skill        | ✅ 已实现 | 更新技能                          |
| `/api/skill/{skill_id}/toggle`   | PATCH  | skill        | ✅ 已实现 | 切换技能启用/禁用                     |
| `/api/skill/batch`               | DELETE | skill        | ✅ 已实现 | 批量删除技能                        |
| `/api/skill/{skill_id}`          | DELETE | skill        | ✅ 已实现 | 删除单个技能                        |
| `/api/agents`                    | GET    | agents       | ✅ 已实现 | 智能体列表（首访自动创建默认智能体）       |
| `/api/agents/{agent_id}`         | GET    | agents       | ✅ 已实现 | 智能体详情（含技能列表）               |
| `/api/agents`                    | POST   | agents       | ✅ 已实现 | 创建智能体                         |
| `/api/agents/{agent_id}`         | PUT    | agents       | ✅ 已实现 | **v1.6.0 新增**：更新智能体          |
| `/api/agents/{agent_id}`         | DELETE | agents       | ✅ 已实现 | 删除智能体（级联删除子智能体 + 关联表）       |
| `/api/agents/{agent_id}/status`  | PATCH  | agents       | ✅ 已实现 | 切换智能体状态                       |
| `/api/agents/{agent_id}/clone`   | POST   | agents       | ✅ 已实现 | 克隆智能体                         |
| `/api/agents/{agent_id}/config`  | POST   | agents       | ✅ 已实现 | 添加配置项                         |
| `/api/agents/{agent_id}/config`  | DELETE | agents       | ✅ 已实现 | 移除配置项                         |
| `/api/agents/{agent_id}/config`  | PUT    | agents       | ✅ 已实现 | 更新配置项                         |
| `/api/agents/{agent_id}/file-descriptions` | GET | agents   | ✅ 已实现 | 文件描述列表                       |
| `/api/agents/{agent_id}/files/{filename}` | GET | agents    | ✅ 已实现 | 获取文件内容                        |
| `/api/agents/{agent_id}/files/{filename}` | PUT | agents    | ✅ 已实现 | 保存文件内容                        |
| `/api/agents/{agent_id}/skills`  | GET    | agents       | ✅ 已实现 | **v1.6.0 新增**：关联技能列表      |
| `/api/agents/{agent_id}/skills`  | POST   | agents       | ✅ 已实现 | **v1.6.0 新增**：添加技能          |
| `/api/agents/{agent_id}/skills/{skill_id}` | DELETE | agents | ✅ 已实现 | **v1.6.0 新增**：移除技能       |
| `/api/agents/{agent_id}/cron-jobs` | GET  | agents       | ✅ 已实现 | **v1.6.0 新增**：定时任务列表      |
| `/api/providers`                 | GET    | providers    | ✅ 已实现 | 提供商列表（含嵌套模型）                |
| `/api/providers`                 | POST   | providers    | ✅ 已实现 | 创建提供商（api_key 自动加密存储）         |
| `/api/providers/{provider_id}`   | PUT    | providers    | ✅ 已实现 | 更新提供商                         |
| `/api/providers/{provider_id}`   | DELETE | providers    | ✅ 已实现 | 删除提供商（级联删除模型）                |
| `/api/providers/{provider_id}/models` | POST | providers | ✅ 已实现 | 创建模型                          |
| `/api/providers/{provider_id}/models/{model_id}` | PUT | providers | ✅ 已实现 | 更新模型                |
| `/api/providers/{provider_id}/models/{model_id}` | DELETE | providers | ✅ 已实现 | 删除模型              |
| `/api/providers/{provider_id}/models/{model_id}/clone` | POST | providers | ✅ 已实现 | 克隆模型          |
| `/api/providers/{provider_id}/models/{model_id}/status` | PATCH | providers | ✅ 已实现 | 切换模型状态         |
| `/api/tools/list`                | GET    | tools        | ✅ 已实现 | **v1.6.0 新增**：工具列表          |
| `/api/tools/by-agent/{agent_id}` | GET    | tools        | ✅ 已实现 | **v1.6.0 新增**：智能体工具列表      |
| `/api/tools/{tool_id}`           | GET    | tools        | ✅ 已实现 | **v1.6.0 新增**：工具详情          |
| `/api/tools`                     | POST   | tools        | ✅ 已实现 | **v1.6.0 新增**：创建第三方工具      |
| `/api/tools/{tool_id}`           | PUT    | tools        | ✅ 已实现 | **v1.6.0 新增**：更新工具          |
| `/api/tools/{tool_id}/toggle`    | PATCH  | tools        | ✅ 已实现 | **v1.6.0 新增**：切换工具状态      |
| `/api/tools/{tool_id}`           | DELETE | tools        | ✅ 已实现 | **v1.6.0 新增**：删除工具          |
| `/api/knowledge-bases`           | GET    | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：知识库列表（分页+搜索） |
| `/api/knowledge-bases/stats`     | GET    | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：聚合统计          |
| `/api/knowledge-bases/available-models` | GET | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：可用模型筛选    |
| `/api/knowledge-bases/available-providers` | GET | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：可用提供商筛选 |
| `/api/knowledge-bases`           | POST   | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：创建知识库       |
| `/api/knowledge-bases/{kb_id}`   | GET    | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：知识库详情       |
| `/api/knowledge-bases/{kb_id}`   | PUT    | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：更新知识库       |
| `/api/knowledge-bases/{kb_id}`   | DELETE | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：删除知识库       |
| `/api/knowledge-bases/{kb_id}/indexing-activity` | GET | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：索引活动 |
| `/api/knowledge-bases/{kb_id}/reindex` | POST | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：重索引全部文档 |
| `/api/knowledge-bases/{kb_id}/documents/upload` | POST | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：上传文档（最多20个） |
| `/api/knowledge-bases/{kb_id}/documents` | GET | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：文档列表 |
| `/api/knowledge-bases/{kb_id}/documents/{doc_id}` | GET | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：文档详情+流水线状态 |
| `/api/knowledge-bases/{kb_id}/documents/{doc_id}` | DELETE | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：删除文档 |
| `/api/knowledge-bases/{kb_id}/documents/{doc_id}/retry` | POST | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：重试失败文档 |
| `/api/knowledge-bases/{kb_id}/documents/{doc_id}/chunks` | GET | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：分块列表 |
| `/api/knowledge-bases/{kb_id}/documents/{doc_id}/chunks/{chunk_id}` | GET | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：分块详情 |
| `/api/knowledge-bases/{kb_id}/documents/{doc_id}/chunks/{chunk_id}` | PUT | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：更新分块 |
| `/api/knowledge-bases/{kb_id}/documents/{doc_id}/chunks/{chunk_id}` | DELETE | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：删除分块 |
| `/api/knowledge-bases/{kb_id}/documents/{doc_id}/chunks/batch` | POST | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：批量操作分块 |
| `/api/knowledge-bases/{kb_id}/graph` | GET | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：实体+关系列表 |
| `/api/knowledge-bases/{kb_id}/graph/entities/{entity_id}` | GET | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：实体详情 |
| `/api/knowledge-bases/{kb_id}/graph/re-extract` | POST | knowledge_base | ✅ 已实现 | **v1.7.0 新增**：重提取图谱 |

共 **90 个接口**（v1.6.0 为 67 个，v1.7.0 新增 Knowledge Base API 23 个）。

### 7.2 统一响应格式

大部分接口使用 `ApiResponse<T>` 统一响应包装，与 v1.5.0 一致。

---

## 8. 数据流

### 8.1 普通对话（v1.6.0 更新）

```
前端 POST /api/chat {"message": "用户输入", "thread_id": "..." | null}
    ↓
JWT 鉴权（get_current_user_id 提取 user_id）
    ↓
构建 Context(server_info="ke_hermes_server", user_id=user_id)
    ↓
get_graph().ainvoke({"messages": [HumanMessage(...)]}, config=..., context=context)
    ↓
LangGraph 运行时 → SkillSandboxSyncMiddleware.abefore_agent()
    ├── SandboxManager.get_or_create(user_id) → 获取/创建用户沙盒
    ├── 从 /skills/{agent_id}/ 读取技能文件
    ├── 上传技能文件到沙盒 /skills/ 目录
    └── 提取 SKILL.md 中的 network-domains → 应用沙盒 egress 规则
    ↓
主智能体分析（DB 驱动的 system_prompt + 工具 + 子智能体）
    ├── 工具调用：UserAwareSandboxBackend → SandboxManager.get_or_create(user_id) → OpenSandboxBackend
    ├── 记忆读写：StoreBackend(namespace=(user_id,))
    └── 技能文件：FilesystemBackend(virtual_mode, root=SKILLS_ROOT)
    ↓
必要时委派子智能体（DB 动态加载的类型/模型/工具/技能）
    ↓
Checkpointer 自动写入检查点 → Store 持久化记忆更新
    ↓
新对话：create_conversation()
    ↓
ChatResponse → 前端保存 thread_id
```

### 8.2 模块依赖关系（v1.7.0 全图）

```
server.py
  ├── load_dotenv()           ← 加载 .env
  ├── Windows SelectorEventLoop monkeypatch  ← Windows 兼容
  ├── CORS 中间件
  ├── lifespan:
  │     ├── init_db()                  ← 自动建表 + 迁移函数（19 个模型）
  │     ├── seed_mcp_tools(session)    ← MCP 工具种子（12 个）
  │     ├── seed_builtin_skills(session) ← 内置技能种子（5 个）
  │     ├── seed_builtin_tools(session) ← 内置工具种子（11 个）
  │     ├── migrate_plaintext_api_keys(session) ← api_key 明文→加密迁移
  │     ├── _init_knowledge_base(app)  ← v1.7.0 新增：RAG 基础设施
  │     │     ├── get_embedding_model()          ← 嵌入模型工厂（DashScope / OpenAI）
  │     │     ├── VectorStore (Milvus / Chroma)  ← 双后端向量库
  │     │     ├── create_default_loader_registry() ← 13 种文档加载器
  │     │     ├── create_chunk_registry()        ← 5 种切片策略
  │     │     ├── GraphExtractionService          ← Langextract 图谱提取
  │     │     ├── IndexingPipeline                ← 索引流水线（模板方法）
  │     │     │     ├── DatabaseProgressObserver   ← 进度持久化（观察者）
  │     │     │     └── LoggingProgressObserver    ← 日志记录（观察者）
  │     │     └── IndexingScheduler               ← 异步任务队列（单例）
  │     ├── init_graph()               ← 检查点 + Store + SandboxManager + AgentBuilder
  │     │     ├── SandboxManager(extra_domains=...).start_cleanup()
  │     │     └── create_main_agent(checkpointer, store, sandbox_manager)
  │     │           └── AgentBuilder 建造者模式（v1.7.0 重构）
  │     │                 ├── with_agent_from_db()  → 查询活跃主智能体
  │     │                 ├── with_model()          → resolve_model() 动态加载
  │     │                 ├── with_tools()          → get_tool_registry() 解析
  │     │                 ├── with_system_prompt()  → 系统提示词
  │     │                 ├── with_subagents()      → 动态子智能体加载
  │     │                 ├── with_sandbox()        → UserAwareSandboxBackend
  │     │                 ├── with_backend()        → CompositeBackend 三层路由
  │     │                 │     ├── default → UserAwareSandboxBackend
  │     │                 │     ├── /memories/ → StoreBackend(namespace=(user_id,))
  │     │                 │     └── /skills/ → FilesystemBackend(virtual_mode)
  │     │                 ├── with_memory()         → 记忆路径
  │     │                 ├── with_middleware()      → SkillSandboxSyncMiddleware
  │     │                 └── build()               → create_deep_agent()
  │     ├── create_store()             ← Redis / MemoryStore
  │     ├── set_store()                ← 注入依赖
  │     ├── init_jwt()                 ← JWT 密钥持久化
  │     └── shutdown_graph()           ← 关闭 SandboxManager + 连接池
  └── api.router (16 个子模块)
        ├── agent_api.router (prefix="/api")
        ├── agents_api.router (prefix="/api/agents")
        ├── conversation_api.router (prefix="/api")
        ├── auth_api.router (prefix="/api/auth")
        ├── captcha_api.router (prefix="/api/captcha")
        ├── oauth_api.router (prefix="/api/oauth")
        ├── sms_api.router (prefix="/api/sms")
        ├── email_api.router (prefix="/api/email")
        ├── mcp_api.router (prefix="/api/mcp")
        ├── providers_api.router (prefix="/api/providers")
        ├── skill_api.router (prefix="/api/skill")
        ├── tools_api.router (prefix="/api/tools")
        ├── kb_api.router (prefix="/api/knowledge-bases")               ← v1.7.0 新增
        ├── doc_api.router (prefix="/api/knowledge-bases/{kb_id}")      ← v1.7.0 新增
        ├── graph_api.router (prefix="/api/knowledge-bases/{kb_id}")    ← v1.7.0 新增
        └── chunk_api.router (prefix="/api/knowledge-bases/{kb_id}")    ← v1.7.0 新增
```

---

## 9. 环境变量设计

| 变量名                          | 类型  | 默认值                                                   | 说明                              |
| ---------------------------- | --- | ----------------------------------------------------- | ------------------------------- |
| `DEEPSEEK_API_KEY`           | str | `""`                                                  | DeepSeek API 密钥（必填）             |
| `DEEPSEEK_MODEL`             | str | `"deepseek-v4-pro"`                                   | 默认主智能体 LLM 模型名称                |
| `DEEPSEEK_BASE_URL`          | str | `""`                                                  | DeepSeek API 地址                 |
| `DASHSCOPE_API_KEY`          | str | `""`                                                  | DashScope API 密钥（Qwen + Embedding） |
| `DASHSCOPE_EMBEDDING`        | str | `""`                                                  | 向量模型名称                          |
| `DASHSCOPE_BASE_URL`         | str | `""`                                                  | DashScope 兼容地址                  |
| `HOST`                       | str | `"127.0.0.1"`                                         | 服务监听地址                          |
| `PORT`                       | int | `8000`                                                | 服务监听端口                          |
| `TAVILY_API_KEY`             | str | `""`                                                  | Tavily 互联网搜索 API 密钥             |
| `OPENSANDBOX_DOMAIN`         | str | `"http://127.0.0.1:8080"`                             | OpenSandbox 沙盒服务地址              |
| `OPENSANDBOX_API_KEY`        | str | `""`                                                  | OpenSandbox API 密钥              |
| `SANDBOX_TTL_SECONDS`        | int | `1800`                                                | 每用户沙盒 TTL 秒数（v1.6.0 新增）       |
| `SANDBOX_CLEANUP_INTERVAL`   | int | `300`                                                 | 沙盒清理轮询间隔秒数（v1.6.0 新增）         |
| `SANDBOX_IMAGE`              | str | `"sandbox-registry...code-interpreter:v1.0.2"`        | 沙盒容器镜像（v1.6.0 新增）              |
| `SANDBOX_CPU`                | str | `"2"`                                                 | 沙盒 CPU 核数（v1.6.0 新增）           |
| `SANDBOX_MEMORY`             | str | `"3Gi"`                                               | 沙盒内存分配（v1.6.0 新增）              |
| `SANDBOX_IDLE_TIMEOUT_MINUTES` | int | `10`                                                | 沙盒闲置超时分钟数（v1.6.0 新增）           |
| `SANDBOX_ALLOWED_DOMAINS`    | str | `""`                                                  | 额外允许出站域名列表（v1.6.0 新增）          |
| `WORKSPACE`                  | str | `auto`                                                | 智能体工作目录（自动推导为 backend/workspace/） |
| `SKILLS_ROOT`                | str | `{WORKSPACE}/skills/`                                | 技能文件系统根目录（v1.6.0 新增）          |
| `DATABASE_BACKEND`           | str | `"sqlite"`                                            | 业务数据库后端（sqlite / postgres）      |
| `DATABASE_URL`               | str | `""`                                                  | 业务数据库连接字符串                      |
| `DATABASE_PATH`              | str | `""`                                                  | 业务数据库文件路径（SQLite）               |
| `CHECKPOINT_BACKEND`         | str | `"sqlite"`                                            | LangGraph 检查点后端（sqlite / postgres） |
| `CHECKPOINT_DB_URL`          | str | `"postgresql://127.0.0.1:5432/ke_hermes"`             | PostgreSQL 检查点 + Store 数据库连接串    |
| `CHECKPOINT_DB_PATH`         | str | `"./db/ke_hermes.db"`                                 | SQLite 检查点数据库文件路径                |
| `STORE_BACKEND`              | str | `"sqlite"`                                            | LangGraph Store 后端（sqlite / postgres） |
| `STORE_DB_URL`               | str | `"postgresql://127.0.0.1:5432/ke_hermes"`             | PostgreSQL Store 数据库连接串          |
| `STORE_DB_PATH`              | str | `"./db/ke_hermes.db"`                                 | SQLite Store 数据库文件路径             |
| `ENCRYPTION_KEY`             | str | `""`                                                  | Fernet 密钥，Provider API Key 加密（v1.6.0 新增） |
| `JWT_SECRET_KEY`             | str | `""`                                                  | JWT 签名密钥（缺省自动生成持久化）              |
| `JWT_ACCESS_EXPIRE`          | int | `7200`                                                | Access Token 有效期（秒）             |
| `JWT_REFRESH_EXPIRE`         | int | `604800`                                              | Refresh Token 有效期（秒）            |
| `RSA_KEY_SIZE`               | int | `2048`                                                | RSA 密钥长度                        |
| `LOGIN_MAX_FAILS`            | int | `5`                                                   | 登录失败锁定阈值                        |
| `LOGIN_LOCK_MINUTES`         | int | `30`                                                  | 锁定时间（分钟）                        |
| `SMS_DAILY_LIMIT`            | int | `5`                                                   | 短信每日上限                          |
| `CAPTCHA_EXPIRE`             | int | `300`                                                 | 验证码过期时间（秒）                      |
| `SLIDE_THRESHOLD`            | int | `8`                                                   | 滑动验证容差（像素）                      |
| `REDIS_URL`                  | str | `"redis://127.0.0.1:6379/0"`                          | Redis 连接地址                      |
| `OAUTH_GITHUB_CLIENT_ID`     | str | `""`                                                  | GitHub OAuth Client ID          |
| `OAUTH_GITHUB_CLIENT_SECRET` | str | `""`                                                  | GitHub OAuth Secret             |
| `OAUTH_GOOGLE_CLIENT_ID`     | str | `""`                                                  | Google OAuth Client ID          |
| `OAUTH_GOOGLE_CLIENT_SECRET` | str | `""`                                                  | Google OAuth Secret             |
| `OAUTH_WECHAT_CLIENT_ID`     | str | `""`                                                  | 微信 OAuth Client ID              |
| `OAUTH_WECHAT_CLIENT_SECRET` | str | `""`                                                  | 微信 OAuth Secret                 |
| `SMS_PROVIDER`               | str | `""`                                                  | 短信服务商 (aliyun/tencent)          |
| `SMS_ACCESS_KEY`             | str | `""`                                                  | 短信服务商 Access Key                |
| `SMS_SECRET_KEY`             | str | `""`                                                  | 短信服务商 Secret Key                |
| `SMS_SIGN_NAME`              | str | `""`                                                  | 短信签名                            |
| `SMS_TEMPLATE_CODE`          | str | `""`                                                  | 短信模板编号                          |
| `VECTOR_DB_BACKEND`          | str | `"chroma"`                                            | 向量库后端（milvus / chroma）（v1.7.0 新增） |
| `MILVUS_URI`                 | str | `""`                                                  | Milvus 连接 URI（v1.7.0 新增）       |
| `MILVUS_USER`                | str | `""`                                                  | Milvus 用户名（v1.7.0 新增）          |
| `MILVUS_PASSWORD`            | str | `""`                                                  | Milvus 密码（v1.7.0 新增）           |
| `MILVUS_DEFAULT_DB`          | str | `"default"`                                           | Milvus 默认数据库（v1.7.0 新增）       |
| `CHROMA_HOST`                | str | `"127.0.0.1"`                                         | Chroma 服务地址（v1.7.0 新增）        |
| `CHROMA_PORT`                | int | `8000`                                                | Chroma 服务端口（v1.7.0 新增）        |
| `CHROMA_PERSIST_DIR`         | str | `"./db/chroma"`                                       | Chroma 持久化目录（v1.7.0 新增）      |
| `DOC_STORE_BACKEND`          | str | `"local"`                                             | 文档存储后端（v1.7.0 新增）            |
| `DOC_UPLOAD_DIR`             | str | `"./uploads"`                                         | 文档上传目录（v1.7.0 新增）            |
| `GRAPH_STORE_BACKEND`        | str | `"sqlite"`                                            | 图谱存储后端（v1.7.0 新增）            |
| `DEFAULT_EMBEDDING_MODEL`    | str | `""`                                                  | 默认嵌入模型名称（v1.7.0 新增）         |
| `DEFAULT_EMBEDDING_DIM`      | int | `1024`                                                | 默认嵌入维度（v1.7.0 新增）            |
| `INDEXING_MAX_CONCURRENT`    | int | `3`                                                   | 最大并发索引数（v1.7.0 新增）           |
| `BM25_DEFAULT_K1`            | float | `1.2`                                                | BM25 k1 参数（v1.7.0 新增）          |
| `BM25_DEFAULT_B`             | float | `0.75`                                               | BM25 b 参数（v1.7.0 新增）           |

共 **66 个配置项**（v1.6.0 为 50 个，v1.7.0 新增 16 个：13 个向量库/存储 + 2 个 Embedding + 1 个索引并发）。

---

## 10. 关键设计决策

（前 16 条与 v1.5.0 一致，v1.6.0 新增以下条目）

### 10.17 SandboxManager 每用户沙盒管理（v1.6.0 新增）

从单个全局沙盒变更为 `SandboxManager` 管理的每用户沙盒池。设计原因：

1. **用户隔离**：不同用户的代码执行互不干扰
2. **资源控制**：每个沙盒独立配置 CPU/内存/闲置超时
3. **生命周期管理**：TTL 过期自动回收，健康检查确保可用性
4. **后台清理**：daemon 线程定期巡检，防止资源泄漏

### 10.18 UserAwareSandboxBackend 运行时用户路由（v1.6.0 新增）

`UserAwareSandboxBackend` 在每次文件/执行操作时从 LangGraph runtime context 提取 `user_id`，动态路由到正确的沙盒。与静态的单个沙盒映射不同，这种设计天然支持多用户并发场景。

### 10.19 数据库驱动的主智能体工厂（v1.6.0 新增）

主智能体构建从硬编码迁移到 `main_agent.py` 的 `create_main_agent()` 工厂函数，从数据库查询 Agent 配置、Provider/AIModel、工具注册表动态构建。益处：

- **热配置**：修改 Agent 配置无需重启服务（下次对话生效）
- **模型灵活**：每个智能体独立选择模型提供商和具体模型
- **工具动态**：内置 + 第三方工具均可通过 DB 配置启用/禁用

### 10.20 动态子智能体加载（v1.6.0 新增）

子智能体从静态 `research_subagent` 字典扩展为数据库驱动的 `subagents_operate.py` 动态加载器。益处：

- **可扩展**：通过 Agents API 创建新子智能体，无需修改代码
- **模型独立**：每个子智能体独立配置 Provider + AIModel
- **工具独立**：每个子智能体独立配置工具列表和 system_prompt

### 10.21 SkillSandboxSyncMiddleware 技能同步（v1.6.0 新增）

在每次 Agent 调用前，将智能体的技能文件从文件系统同步到用户沙盒。设计要点：

- **去重**：通过 sandbox_id 追踪已同步状态，避免重复上传
- **网络策略**：从 SKILL.md 的 `network-domains` 字段自动提取并应用到沙盒 egress
- **隔离**：按 agent_id 组织技能目录，不同智能体技能独立

### 10.22 Agent 模型重构：从 JSON 列到关联表（v1.6.0 新增）

`Agent` 模型的 `tools`/`skills` 从 JSON 字符串列表变更为 `AgentTool`/`AgentSkill` 多对多关联表。益处：

- **引用完整性**：关联表支持外键约束和级联删除
- **可查询**：支持按工具/技能过滤智能体、统计使用情况
- **元数据**：关联表可扩展（如添加 created_at、配置参数）

### 10.23 Provider API Key 加密（v1.6.0 新增）

Provider 的 api_key 使用 Fernet 对称加密存储。设计要点：

- **持久化密钥**：Fernet 密钥自动生成并保存到 `.fernet_key`，重启后可解密
- **明文迁移**：`migrate_plaintext_api_keys()` 在 lifespan 阶段自动将存量明文密钥加密
- **运行时解密**：`decrypt_api_key()` 在 `main_agent.py` 和 `subagents_operate.py` 的模型解析时被调用

### 10.24 AgentBuilder 建造者模式重构（v1.7.0 新增）

将原 118 行内联 `create_main_agent()` 函数分解为 `AgentBuilder` 的 9 步链式构建。设计原因：

1. **步骤可测试**：每个 `with_*` 步骤可独立单元测试
2. **依赖显式化**：步骤间前置条件通过运行时检查强制
3. **组合灵活**：可选择性调用步骤（如跳过子智能体加载），支持变体组合

### 10.25 文档索引状态机（v1.7.0 新增）

使用 GoF 状态模式实现 8 状态文档索引流水线（`doc_state.py`）。设计原因：

1. **阶段独立**：每个索引阶段（解析/切片/向量化/BM25/抽取）为独立状态类
2. **进度可追踪**：每个状态转换触发进度回调，前端实时展示 8 阶段进度条
3. **失败隔离**：非关键阶段（实体抽取）失败不阻塞索引，文档仍标记为已索引

### 10.26 观察者模式进度追踪（v1.7.0 新增）

`IndexingPipeline` 维护 `ProgressObserver` 列表（Database + Logging），状态转换时通知所有观察者。设计原因：

1. **职责分离**：进度持久化和日志输出为独立 Observer，IndexingPipeline 不感知
2. **可扩展**：新增 Observer（如 WebSocket 推送）无需修改 Pipeline

### 10.27 Milvus/Chroma 双向量库后端（v1.7.0 新增）

`BaseVectorStore` 抽象接口 + `MilvusVectorStore` / `ChromaVectorStore` 双实现。设计原因：

1. **开发/生产分离**：开发环境用 Chroma（零依赖），生产环境用 Milvus（高性能分布式）
2. **检索算法统一**：similarity_search / bm25_search / hybrid_search 统一接口
3. **Collection 命名规约**：`kb_{kb_id}` 模式确保知识库间数据隔离

### 10.28 Strategy + Registry 文档处理流水线（v1.7.0 新增）

13 种文档加载器 + 5 种切片策略均通过 Strategy 模式 + Registry 注册表管理。设计原因：

1. **开闭原则**：新增文件格式只需实现 `DocumentLoaderStrategy` + 注册
2. **Fallback 容错**：PDF 提供 open-dataloader → PyPDF 双策略 Fallback
3. **条件注册**：semantic 切片仅在 embedding 可用时注册，agentic 切片存根预留

### 10.29 装饰器库横切关注点（v1.7.0 新增）

`handle_errors` / `cached` / `retry` / `log_call` 四个装饰器统一处理横切关注点。设计原因：

1. **消除重复**：API 层 ~50 处重复 try/except 模板可通过 `@handle_errors` 消除
2. **弹性增强**：外部服务调用（OAuth/短信/邮件）通过 `@retry` 增加容错
3. **性能优化**：高频查询接口通过 `@cached` 减少数据库压力

---

## 11. 测试设计

### 11.1 测试分层

```
tests/
├── conftest.py                 # 公共 fixtures（AsyncClient + lifespan 管理）
├── test_loaders.py             # 文档加载器测试（v1.7.0 新增）
├── unit_tests/
│   ├── test_config.py          # Settings 类环境变量读取
│   ├── test_models.py          # LLM/Embeddings 实例导入
│   ├── test_agent.py           # graph 导出函数验证
│   ├── test_agent_service.py   # 智能体管理服务单元测试
│   ├── test_http_request.py    # HTTP 请求工具测试
│   └── test_tavily_search.py   # Tavily 搜索工具测试
└── integration_tests/
    ├── test_server.py          # FastAPI 实例 + 路由注册验证
    ├── test_agent_api.py       # Chat API 接口测试
    └── test_agents_api.py      # Agents API 集成测试
```

### 11.2 执行命令

```bash
pytest tests/ -v                    # 运行全部测试
pytest tests/unit_tests/ -v         # 仅单元测试
pytest tests/integration_tests/ -v  # 仅集成测试
```

---

## 12. 启动与部署

### 12.1 开发环境

```bash
cd backend
uv sync                    # 安装依赖
uv run python run.py       # 启动开发服务器
```

### 12.2 前置条件

1. Python >= 3.11
2. 虚拟环境已创建并安装依赖
3. `.env` 文件已配置必要的 API Key
4. Redis 服务（可选 — 不可用时自动降级为内存存储）
5. OpenSandbox 服务（可选 — 代码执行需沙盒运行中）
6. `workspace/` 目录（自动创建）
7. `.jwt_secret` / `.fernet_key`（自动生成并持久化）

### 12.3 API 文档

启动后访问 `http://127.0.0.1:8000/docs`，FastAPI 自动生成交互式 Swagger UI 文档。16 个功能模块共 90 个接口均自动注册。

---

## 13. 前后端实施差异与待实现项

### 13.1 前后端功能对照（v1.6.0）

| 功能模块       | 前端 v1.2.1 | 后端 v1.6.0 | 差异                                     |
| ---------- | --------- | --------- | -------------------------------------- |
| 智能体对话 (普通) | ✅ 已实现     | ✅ 已实现     | **一致**（后端 v1.6.0：JWT 鉴权 + Context + 用户感知沙盒 + 技能同步中间件 + DB 驱动主智能体 + 动态子智能体） |
| 智能体对话 (流式) | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 智能体管理     | ⬜         | ✅ 已实现     | **后端已实现**（16 接口 v1.6.0：增加更新 + 技能关联 + CronJob） |
| 对话历史 CRUD  | ⬜ 已设计     | ✅ 已实现     | **后端已实现**（4 接口）                     |
| 模型管理      | ⬜ 已设计     | ✅ 已实现     | **后端已实现**（9 接口 + api_key 加密）          |
| 知识库管理     | ⬜         | ✅ 已实现     | **后端已实现**（v1.7.0 新增：23 接口 + 8 状态机 + 图谱提取） |
| 工具管理      | ⬜         | ✅ 已实现     | **后端已实现**（7 接口 + 11 个预置工具） |
| 账号密码登录     | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 手机验证码登录    | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 手机号注册      | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 邮箱注册       | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 滑动拼图验证码    | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 图形验证码      | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 短信发送       | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| OAuth 登录   | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| Token 管理   | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| RSA 加密     | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| MCP 广场     | ⬜         | ✅ 已实现     | **后端已实现**（4 接口 + 12 种子工具）             |
| Skills 管理  | ⬜         | ✅ 已实现     | **后端已实现**（9 接口 + 5 内置技能）              |
| 邮箱验证码     | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 用户管理       | ⬜         | ⬜         | 前端无管理界面，后端无管理 API                      |

### 13.2 待实现项

| 优先级 | 模块       | 接口数 | 说明                           |
| --- | -------- | --- | ---------------------------- |
| P2  | 通知系统     | 2+  | 对接前端 TopBar 通知铃铛按钮           |
| P3  | 用户管理 API | 4+  | 用户信息编辑、头像上传、密码修改             |
| P3  | 邮件发送服务   | 1   | 邮箱验证码实际发送（当前仅开发模式）           |

### 13.3 从 v1.0.0 到 v1.7.0 的变更总结

| 项目       | v1.0.0 (初始)          | v1.7.0 (当前)                                                                                                                   |
| -------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| API 模块   | 1 (agent)            | 16 (agent + agents + auth + captcha + oauth + sms + email + conversation + mcp + providers + skill + tools + knowledge_base×4) |
| 数据模型     | 0                    | 19 (User + UserOAuth + LoginRecord + Conversation + Skill + McpTool + McpInstallation + Agent + AgentFile + AgentSkill + AgentTool + AIModel + Provider + Tool + CronJob + KnowledgeBase + KnowledgeBaseDocument + KnowledgeBaseEntity + KnowledgeBaseRelation) |
| Agent 架构 | 单智能体 + 无文件后端         | DB 驱动主智能体 + AgentBuilder 建造者模式 + 动态子智能体 + CompositeBackend（三层路由）+ SandboxManager 每用户沙盒 + SkillSandboxSyncMiddleware 技能同步 |
| LLM 模型  | 1 (DeepSeek)         | 1 fallback (DeepSeek) + 数据库驱动动态选择（Provider/AIModel 表）+ `resolve_model()` 外观      |
| 知识库      | 无                    | 完整 RAG 子系统：KB CRUD + 文档索引 8 状态机 + 知识图谱提取 + 分块管理 + Milvus/Chroma 双向量库 + 13 种文档加载器 + 5 种切片策略 |
| 设计模式     | 无显式应用                | Builder / State / Observer / Strategy / Template Method / Iterator / Decorator / Singleton / Factory / Proxy / Adapter / Composite / Facade |
| 文件后端     | 无                    | CompositeBackend（UserAwareSandboxBackend 代码执行 + StoreBackend 记忆存储 + FilesystemBackend 技能虚拟文件系统）             |
| 沙盒执行     | 无                    | SandboxManager 每用户沙盒池（TTL + 健康检查 + 后台清理）+ UserAwareSandboxBackend 运行时路由 + OpenSandboxBackend 底层封装        |
| 中间件      | 0                    | CORS + 依赖注入体系 + SkillSandboxSyncMiddleware（技能同步 + 网络策略）                                                     |
| 检查点后端    | 无                    | 双后端（SQLite + PostgreSQL），含 Store 持久化                                                                                        |
| 安全       | 无                    | RSA + JWT + bcrypt + Fernet + 登录锁定 + JWT 鉴权                                                            |
| 存储抽象     | 无                    | KeyValueStore（Redis + MemoryStore）                                                                                            |
| 核心工具层    | 无                    | 装饰器库（handle_errors / cached / retry / log_call）+ PageIterator 分页迭代器 + RAG 基础设施（嵌入/向量库/加载器/切片器/BM25） |
| 对话上下文    | 无                    | thread_id 多轮对话 + 对话历史 CRUD + 检查点/Store 持久化                                                                                |
| 智能体管理    | 无                    | 智能体 CRUD + 主/子层级 + 配置管理 + 文件操作 + 技能关联（关联表）+ CronJob + 克隆                                            |
| 模型管理     | 无                    | 提供商/模型 CRUD + 7 种模型类型 + 嵌套响应 + 克隆 + 状态切换 + api_key 加密                                                          |
| 工具管理     | 无                    | 工具 CRUD + 列表 + 切换 + 智能体关联 + 11 个内置种子工具                                                        |
| MCP 广场    | 无                    | 工具列表 + 详情 + 安装/卸载 + 12 个预置种子工具                                                                              |
| Skills 管理 | 无                    | 上传校验 + CRUD + 批量 + 启用/禁用 + 5 个内置种子技能                                                                          |
| 邮箱验证     | 无                    | 邮箱验证码发送 + 频率限制 + 开发模式                                                                                       |
| 外部依赖     | DeepSeek + DashScope | + bcrypt + cryptography + httpx + Pillow + redis(可选) + tavily + psycopg(可选) + python-multipart + opensandbox + opensandbox-code-interpreter + langchain-community + unstructured + pymilvus + chromadb + pypdf + docx2txt + tiktoken + transformers + langextract + jq + langchain-opendataloader-pdf + langchain-experimental + langchain-text-splitters |
| 环境变量     | 8                    | 66                                                                                                                             |
| API 接口   | 2                    | 90                                                                                                                             |


---

> 本文档 v1.7.0 基于实际代码实现更新。v1.7.0 重点新增：Knowledge Base 完整 RAG 子系统（23 接口 + 4 个 ORM 模型 + 文档索引 8 状态机 + 知识图谱提取 + Milvus/Chroma 双向量库 + 13 种文档加载器 + 5 种切片策略 + BM25 索引）、核心工具层（decorators.py 装饰器库、pagination.py 分页迭代器）、AgentBuilder 建造者模式重构 Agent 构建、Agent 共享工具模块（common.py）、Agent 模型简化为单一 DeepSeek 默认模型；数据模型从 15 个扩展到 19 个；API 子模块从 12 个扩展到 16 个；API 接口从 67 个扩展到 90 个；环境变量从 50 个扩展到 66 个。
