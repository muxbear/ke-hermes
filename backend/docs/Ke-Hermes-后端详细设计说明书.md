# Ke-Hermes 后端详细设计说明书 — v1.5.0


| 版本    | 日期         | 作者  | 变更说明                                                                                                                                                                                 |
| ----- | ---------- | --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1.0.0 | 2026-05-18 | -   | 后端详细设计初版：智能体架构、Chat API、流式对话                                                                                                                                                         |
| 1.2.0 | 2026-05-18 | -   | 对照前端 v1.2.0 详细设计，新增登录/注册/验证码/OAuth 模块完整设计方案，补充安全体系、数据存储、前后端接口对齐与差异分析                                                                                                                 |
| 1.2.1 | 2026-05-19 | -   | 完成 v1.2.0 全部模块编码实现；新增 KeyValueStore 存储抽象层（Redis + 内存降级）；文档对照实际代码更新（bcrypt/cryptography 替代 passlib、JWT 密钥持久化、验证码 Session Cookie、SMS 开发模式等）                                            |
| 1.2.2 | 2026-05-22 | -   | 文档对照实际代码更新：Agent 图重构为 init_graph/get_graph 生命周期模式、支持 PostgreSQL 检查点后端、FilesystemBackend 虚拟文件系统、internet_search 工具、Chat API 增加 thread_id 上下文管理、Windows 事件循环兼容、KeyValueStore 增加 ttl 方法 |
| 1.3.0 | 2026-05-26 | -   | 文档对照实际代码更新：Agent 图升级为 CompositeBackend + LangGraph Store + Context 上下文 + 子智能体系统；新增对话历史 CRUD 模块（Conversation API）；新增 qwen_llm 子智能体模型；配置模块扩展（DATABASE_BACKEND、STORE_BACKEND、WORKSPACE）；internet_search 工具迁移至子智能体中 |
| 1.4.0 | 2026-05-28 | -   | 文档对照实际代码更新：新增 MCP 广场模块（4 接口 + 种子数据 + 安装/卸载）；新增 Skills 技能管理模块（9 接口 + 上传校验 + 批量操作）；新增 Email 邮箱验证码模块；新增 ORM 模型（McpTool/McpInstallation/Skill）；新增预装 Workspace 技能（github/self-improvement）；更新路由注册链（6→9 子模块）、API 接口总数（21→30）、环境变量数量（38→39+） |
| 1.5.0 | 2026-06-05 | -   | 文档对照实际代码更新：新增智能体管理模块（Agents API，12 接口 + CRUD + 配置管理 + 文件操作）；新增模型管理模块（Providers API，9 接口 + 提供商/模型 CRUD + 克隆 + 状态切换）；新增 OpenSandbox 沙盒后端模块（代码执行 + 文件上下传）；新增 ORM 模型（Agent/AgentFile/AIModel/Provider）；Agent 图默认后端切换为 OpenSandboxBackend；更新路由注册链（9→11 子模块）、API 接口总数（30→51）、ORM 模型（7→11）、环境变量数量（39→41） |


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
  - 4.6 [子智能体模块 — agent/subagents](#46-子智能体模块--agentsubagents)
  - 4.7 [Chat API — 对话与流式接口](#47-chat-api--对话与流式接口)
  - 4.8 [Conversation API — 对话历史 CRUD](#48-conversation-api--对话历史-crud)
  - 4.9 [Auth API — 认证授权模块](#49-auth-api--认证授权模块)
  - 4.10 [Captcha API — 验证码模块](#410-captcha-api--验证码模块)
  - 4.11 [OAuth API — 第三方登录模块](#411-oauth-api--第三方登录模块)
  - 4.12 [SMS API — 短信服务模块](#412-sms-api--短信服务模块)
  - 4.13 [Email API — 邮箱验证码模块](#413-email-api--邮箱验证码模块)
  - 4.14 [MCP API — MCP 广场模块](#414-mcp-api--mcp-广场模块)
  - 4.15 [Skills API — 技能管理模块](#415-skills-api--技能管理模块)
  - 4.16 [Agents API — 智能体管理模块](#416-agents-api--智能体管理模块)
  - 4.17 [Providers API — 模型管理模块](#417-providers-api--模型管理模块)
  - 4.18 [Sandbox — 沙盒代码执行模块](#418-sandbox--沙盒代码执行模块)
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

本文档为 Ke-Hermes 后端的详细设计说明书 v1.5.0，对照实际代码实现编写。文档覆盖：

- **已实现模块**：智能体框架（含子智能体系统 + 互联网搜索工具 + OpenSandboxBackend 代码执行后端）、Chat API（普通对话 + SSE 流式 + thread_id 上下文管理）、Conversation API（对话历史 CRUD）、Agents API（智能体 CRUD + 配置管理 + 文件操作）、Providers API（提供商/模型 CRUD + 克隆 + 状态切换）、MCP 广场 API（工具列表/详情/安装/卸载 + 种子数据）、Skills 技能管理 API（CRUD + 上传校验 + 批量删除）、认证授权、验证码、OAuth 第三方登录、短信服务、邮箱验证码
- **基础设施**：KeyValueStore 存储抽象层（Redis + 内存降级）、RSA + JWT + bcrypt 安全体系、SQLAlchemy 异步 ORM（SQLite + PostgreSQL 双后端，11 个 ORM 模型）、LangGraph 检查点双后端（SQLite + PostgreSQL）+ LangGraph Store（Memory + PostgreSQL）、OpenSandbox 沙盒代码执行环境

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
| 沙盒代码执行        | opensandbox / opensandbox-code-interpreter       | >=0.1.2     | OpenSandbox 沙盒代码执行后端（v1.5.0 新增） |
| 密码哈希         | bcrypt                                           | >=4.0       | 密码哈希存储与校验                |
| JWT          | PyJWT                                            | >=2.8       | Token 签发与验证              |
| RSA 加密       | cryptography                                     | >=42.0      | RSA 密钥对生成与加解密            |
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
│   │   ├── config/
│   │   │   ├── __init__.py          # 导出 settings 实例
│   │   │   └── config.py            # Settings 配置类定义（含 WORKSPACE、DATABASE_BACKEND、STORE_BACKEND 等）
│   │   ├── models/
│   │   │   ├── __init__.py          # 导出 llm, qwen_llm, embeddings
│   │   │   ├── llm.py               # ChatOpenAI 实例（DeepSeek + Qwen 3.6 Plus）
│   │   │   └── em.py                # OpenAIEmbeddings 实例（DashScope）
│   │   ├── context/
│   │   │   ├── __init__.py          # 导出 Context
│   │   │   └── context.py           # Context 数据类（server_info + user_id）
│   │   ├── tools/
│   │   │   └── __init__.py          # 工具列表导出（当前为空，工具定义在子智能体中）
│   │   ├── subagents/
│   │   │   ├── __init__.py          # 导出 research_subagent
│   │   │   └── research_subagent.py # 研究子智能体（含 internet_search 工具 + qwen_llm）
│   │   ├── sandbox/
│   │   │   ├── opensandbox_backend.py  # OpenSandboxBackend 实现（代码执行 + 文件上下传）
│   │   │   └── opensandbox_operate.py  # 沙盒创建/连接辅助函数（同步 + 异步）
│   │   ├── utils/
│   │   │   └── __init__.py          # 辅助方法导出（预留）
│   │   └── graph.py                 # deepagents 智能体图定义（生命周期 + OpenSandboxBackend + Store + 子智能体）
│   │
│   ├── api/
│   │   ├── __init__.py              # 导出顶层 router（汇总 9 个子模块）
│   │   ├── deps.py                  # 依赖注入（get_db, get_store, get_client_ip, get_current_user_id）
│   │   ├── agent/
│   │   │   ├── __init__.py          # 导出 agent router
│   │   │   └── agent_api.py         # Chat API 路由与数据模型（含 Context 注入 + 对话记录创建）
│   │   ├── agents/
│   │   │   ├── __init__.py          # 导出 agents router（v1.5.0 新增）
│   │   │   ├── agents_api.py        # 智能体管理 API 路由（12 个接口）
│   │   │   ├── schemas.py           # 智能体管理请求/响应 Pydantic 模型
│   │   │   └── service.py           # 智能体管理业务逻辑（CRUD + 配置 + 文件）
│   │   ├── auth/
│   │   │   ├── __init__.py          # 导出 auth router
│   │   │   ├── auth_api.py          # 认证 API 路由（8 个接口）
│   │   │   ├── schemas.py           # 认证请求/响应 Pydantic 模型
│   │   │   └── service.py           # 认证业务逻辑（登录/注册/刷新）
│   │   ├── captcha/
│   │   │   ├── __init__.py          # 导出 captcha router
│   │   │   ├── captcha_api.py       # 验证码 API 路由（4 个接口，含 Session Cookie）
│   │   │   ├── schemas.py           # 验证码请求/响应 Pydantic 模型
│   │   │   └── service.py           # 验证码业务逻辑（Pillow 图片生成）
│   │   ├── conversation/
│   │   │   ├── __init__.py          # 导出 conversation router
│   │   │   └── conversation_api.py  # 对话历史 CRUD API（4 个接口：列表/详情/重命名/删除）
│   │   ├── oauth/
│   │   │   ├── __init__.py          # 导出 oauth router
│   │   │   ├── oauth_api.py         # OAuth API 路由（2 个接口）
│   │   │   ├── schemas.py           # OAuth 请求/响应 Pydantic 模型
│   │   │   └── service.py           # OAuth 业务逻辑（GitHub/Google/微信）
│   │   ├── providers/
│   │   │   ├── __init__.py          # 导出 providers router（v1.5.0 新增）
│   │   │   ├── providers_api.py     # 模型管理 API 路由（9 个接口）
│   │   │   ├── schemas.py           # 提供商/模型请求/响应 Pydantic 模型
│   │   │   └── service.py           # 提供商/模型业务逻辑（CRUD + 克隆 + 状态切换）
│   │   └── sms/
│   │       ├── __init__.py          # 导出 sms router
│   │       ├── sms_api.py           # 短信 API 路由（1 个接口）
│   │       └── service.py           # 短信发送业务逻辑（含 SendSmsRequest 模型）
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── engine.py                # SQLAlchemy async engine + sessionmaker + init_db（DATABASE_BACKEND 双后端）
│   │   ├── base.py                  # DeclarativeBase
│   │   └── models/
│   │       ├── __init__.py          # 导出所有 model（共 11 个）
│   │       ├── user.py              # User 模型
│   │       ├── user_oauth.py        # UserOAuth 第三方绑定模型
│   │       ├── login_record.py      # LoginRecord 登录记录模型
│   │       ├── conversation.py      # Conversation 对话记录模型
│   │       ├── skill.py             # Skill 技能模型（v1.4.0 新增）
│   │       ├── mcp_tool.py          # McpTool MCP 工具模型（v1.4.0 新增）
│   │       ├── mcp_installation.py  # McpInstallation 安装记录模型（v1.4.0 新增）
│   │       ├── agent.py             # Agent 智能体模型（v1.5.0 新增）
│   │       ├── agent_file.py        # AgentFile 智能体文件模型（v1.5.0 新增）
│   │       ├── ai_model.py          # AIModel 模型元数据模型（v1.5.0 新增）
│   │       └── provider.py          # Provider 模型提供商模型（v1.5.0 新增）
│   │   └── seeds/
│   │       └── mcp_tools_seed.json   # MCP 工具种子数据（v1.4.0 新增）
│   │
│   └── core/
│       ├── __init__.py
│       ├── security.py              # bcrypt 密码哈希、cryptography RSA 加解密、PyJWT Token 签发/验证
│       ├── store.py                 # KeyValueStore 抽象 + RedisStore / MemoryStore 实现
│       └── response.py              # 统一响应格式 ApiResponse[T]
│
├── db/                              # SQLite 数据库文件目录
│   └── ke-hermes.db                 # 开发环境 SQLite 数据库文件（业务 + 检查点共用）
│
├── workspace/                       # 智能体工作目录
│   ├── memories/AGENT.md            # Agent 持久化记忆文件
│   └── skills/                      # 已安装的技能目录（v1.4.0）
│       ├── github/                  # GitHub 集成技能
│       └── self-improvement/        # 自我改进技能（含 hooks/scripts/references）
│
├── tests/
│   ├── conftest.py                  # 测试公共 fixtures
│   ├── unit_tests/
│   │   ├── test_config.py           # 配置模块测试
│   │   ├── test_models.py           # 模型实例测试
│   │   └── test_agent.py            # 智能体导出测试
│   └── integration_tests/
│       ├── test_server.py           # 服务启动测试
│       └── test_agent_api.py        # Chat API 接口测试
│
├── docs/
│   ├── requirements.md              # 需求文档
│   └── Ke-Hermes-后端详细设计说明书.md  # 本文件
│
├── .env                             # 环境变量配置（不入库）
├── .env.example                     # 环境变量示例
├── .jwt_secret                      # JWT 签名密钥持久化文件（自动生成）
├── pyproject.toml                   # 项目元数据与依赖
├── run.py                           # 开发启动脚本
└── langgraph.json                   # LangGraph CLI 配置
```

---

## 4. 模块详细设计

### 4.1 服务入口 — `server.py`

**职责：** 创建 FastAPI 应用实例，加载环境变量，初始化基础设施，注册所有 API 路由。

**v1.3.0 完整实现：**

```python
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    # uvicorn hardcodes ProactorEventLoop on Windows, bypassing the
    # event loop policy.  Monkeypatch it so psycopg can work.
    import uvicorn.loops.asyncio as _uvicorn_loops

    _uvicorn_loops.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

load_dotenv()                     # 必须在业务导入之前

from api import router
from api.deps import set_store
from api.mcp.service import seed_mcp_tools
from core.store import create_store
from db.engine import init_db
from agent.graph import init_graph, shutdown_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()               # 1. 创建业务数据库表
    await seed_mcp_tools()        # 2. MCP 工具种子数据初始化（v1.4.0 新增）
    await init_graph()            # 3. 初始化 Agent（检查点 + Store + LLM + 子智能体 + Backend）
    store = await create_store()   # 4. 初始化 KeyValueStore（Redis 或内存降级）
    set_store(store)
    from core.security import _get_jwt_secret as init_jwt
    init_jwt()                    # 5. 预初始化 JWT secret
    yield
    await shutdown_graph()        # 6. 关闭检查点连接池（PostgreSQL）


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

**启动时的基础设施初始化顺序：**

1. `init_db()` → SQLAlchemy 自动建表（`Base.metadata.create_all`）
2. `seed_mcp_tools()` → MCP 工具种子数据初始化（v1.4.0 新增）
3. `init_graph()` → 根据 `CHECKPOINT_BACKEND` 创建检查点后端 + LangGraph Store + LLM + 子智能体 + OpenSandboxBackend（沙盒代码执行） + CompositeBackend
4. `create_store()` → 尝试连接 Redis，失败则降级为 `MemoryStore`
5. `set_store(store)` → 注入到 FastAPI 依赖注入系统
6. `init_jwt()` → 读取或生成持久化 JWT 签名密钥
7. (关闭时) `shutdown_graph()` → 关闭 PostgreSQL 连接池

**Windows 兼容性：** `uvicorn` 在 Windows 上硬编码了 `ProactorEventLoop`，与 `psycopg` 不兼容。server.py 在导入链顶部通过 monkeypatch 强制使用 `SelectorEventLoop`，确保 PostgreSQL 驱动在 Windows 下正常工作。

**路由注册链：**

```
api/__init__.py → 汇总所有子模块 router
  ├── api/agent/        → agent_api.router        (prefix="/api")               ← 已实现
  ├── api/agents/       → agents_api.router       (prefix="/api/agents")        ← v1.5.0 新增
  ├── api/auth/         → auth_api.router         (prefix="/api/auth")          ← 已实现
  ├── api/captcha/      → captcha_api.router      (prefix="/api/captcha")       ← 已实现
  ├── api/oauth/        → oauth_api.router        (prefix="/api/oauth")         ← 已实现
  ├── api/sms/          → sms_api.router          (prefix="/api/sms")           ← 已实现
  ├── api/conversation/ → conversation_api.router (prefix="/api")               ← v1.3.0 新增
  ├── api/email/        → email_api.router        (prefix="/api/email")         ← v1.4.0 新增
  ├── api/mcp/          → mcp_api.router          (prefix="/api/mcp")           ← v1.4.0 新增
  ├── api/providers/    → providers_api.router    (prefix="/api/providers")     ← v1.5.0 新增
  └── api/skill/        → skill_api.router        (prefix="/api/skill")         ← v1.4.0 新增
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

#### `config.py` — Settings 类（v1.3.0 扩展）

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

    # config.py lives at backend/src/agent/config/ — four levels up to backend/
    backend_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    )
    return os.path.join(backend_root, "workspace")


class Settings(BaseSettings):
    # ---- LLM (DeepSeek) ----
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL")

    # ---- Embeddings (DashScope) ----
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY")
    DASHSCOPE_EMBEDDING: str = os.getenv("DASHSCOPE_EMBEDDING")
    DASHSCOPE_BASE_URL: str = os.getenv("DASHSCOPE_BASE_URL")

    # ---- Tavily ----
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY")

    # ---- Server ----
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = os.getenv("PORT", 8000)

    # ---- OpenSandBox ----
    OPENSANDBOX_DOMAIN: str = os.getenv("OPENSANDBOX_DOMAIN", "http://127.0.0.1:8080")
    OPENSANDBOX_API_KEY: str = os.getenv("OPENSANDBOX_API_KEY", "")

    # ---- Workspace ----
    WORKSPACE: str = Field(default_factory=get_default_workspace)

    @field_validator("WORKSPACE", mode="before")
    @classmethod
    def _workspace_use_default_when_empty(cls, value: object) -> str:
        if value is None or (isinstance(value, str) and not value.strip()):
            return get_default_workspace()
        return str(value)

    # ---- Database ----
    DATABASE_BACKEND: str = os.getenv("DATABASE_BACKEND", "sqlite")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH")

    # ---- Checkpoint Database ----
    CHECKPOINT_BACKEND: str = os.getenv("CHECKPOINT_BACKEND", "sqlite")
    CHECKPOINT_DB_URL: str = os.getenv("CHECKPOINT_DB_URL", "postgresql://127.0.0.1:5432/ke_hermes")
    CHECKPOINT_DB_PATH: str = os.getenv("CHECKPOINT_DB_PATH", "./db/ke_hermes.db")

    # ---- Store Database ----
    STORE_BACKEND: str = os.getenv("STORE_BACKEND", "sqlite")
    STORE_DB_URL: str = os.getenv("STORE_DB_URL", "postgresql://127.0.0.1:5432/ke_hermes")
    STORE_DB_PATH: str = os.getenv("STORE_DB_PATH", "./db/ke_hermes.db")

    # ---- JWT ----
    JWT_SECRET_KEY: str = ""
    JWT_ACCESS_EXPIRE: int = os.getenv("JWT_ACCESS_EXPIRE", 7200)
    JWT_REFRESH_EXPIRE: int = os.getenv("JWT_REFRESH_EXPIRE", 604800)

    # ---- RSA ----
    RSA_KEY_SIZE: int = os.getenv("RSA_KEY_SIZE", 2048)

    # ---- Rate Limit ----
    LOGIN_MAX_FAILS: int = os.getenv("LOGIN_MAX_FAILS", 5)
    LOGIN_LOCK_MINUTES: int = os.getenv("LOGIN_LOCK_MINUTES", 30)
    SMS_DAILY_LIMIT: int = os.getenv("SMS_DAILY_LIMIT", 5)

    # ---- Captcha ----
    CAPTCHA_EXPIRE: int = os.getenv("CAPTCHA_EXPIRE", 300)
    SLIDE_THRESHOLD: int = os.getenv("SLIDE_THRESHOLD", 8)

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

**v1.3.0 新增/变更配置项：**

| 配置项               | 说明                                                |
| ---------------- | ------------------------------------------------- |
| `WORKSPACE`      | 智能体工作目录路径，通过 `get_default_workspace()` 自动推导，支持环境变量覆盖 |
| `DATABASE_BACKEND` | 业务数据库后端选择（`sqlite` / `postgres`）                  |
| `DATABASE_PATH`  | SQLite 业务数据库文件路径                                  |
| `STORE_BACKEND`  | LangGraph Store 后端选择（`sqlite` / `postgres`）        |
| `STORE_DB_URL`   | PostgreSQL Store 数据库连接串                            |
| `STORE_DB_PATH`  | SQLite Store 数据库文件路径                               |
| `CHECKPOINT_DB_PATH` | 默认值变更为 `./db/ke_hermes.db`（与业务数据库共用文件）             |

**v1.5.0 新增配置项：**

| 配置项                  | 说明                               |
| ------------------- | -------------------------------- |
| `OPENSANDBOX_DOMAIN` | OpenSandbox 沙盒服务地址（默认 http://127.0.0.1:8080） |
| `OPENSANDBOX_API_KEY` | OpenSandbox API 密钥（默认空）           |

### 4.3 模型模块 — `agent/models`

**职责：** 创建 LLM 和向量模型实例。v1.3.0 新增 `qwen_llm` 子智能体专用模型。

#### `llm.py` — DeepSeek + Qwen 双模型

```python
from langchain_openai import ChatOpenAI
from agent.config import settings

llm = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    extra_body={"thinking": {"type": "disabled"}}  # 关闭 DeepSeek 思考过程
)

qwen_llm = ChatOpenAI(
    model="qwen3.6-plus",
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.DASHSCOPE_BASE_URL
)

__all__ = ["llm", "qwen_llm"]
```

- **`llm`**（主智能体）：DeepSeek 模型，通过 `extra_body` 关闭思考过程以加速响应
- **`qwen_llm`**（子智能体）：Qwen 3.6 Plus 模型，通过 DashScope 兼容接口调用，用于研究子智能体

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

#### 模块导出

```python
# agent/models/__init__.py
from agent.models.llm import llm, qwen_llm
from agent.models.em import embeddings

__all__ = ["llm", "qwen_llm", "embeddings"]
```

### 4.4 上下文模块 — `agent/context`

**职责：** 定义传递到 Agent 图中的运行时上下文数据结构。v1.3.0 新增。

#### `context.py`

```python
from dataclasses import dataclass

@dataclass
class Context:
    server_info: str
    user_id: str
```

- **`server_info`**：服务端标识字符串（当前固定为 `"ke_hermes_server"`）
- **`user_id`**：当前请求用户的 ID（从 JWT Token 中提取），用于 Backend namespace 路由和记忆隔离

Context 实例在每次 Chat API 调用时创建，通过 `get_graph().ainvoke()` 的 `context` 参数传入 Agent 图。

### 4.5 智能体图 — `agent/graph.py`（v1.3.0 重构）

**职责：** 管理 Agent 图的完整生命周期（初始化 → 运行 → 关闭），支持双检查点后端（SQLite / PostgreSQL）+ 双 Store 后端（InMemory / PostgreSQL），集成子智能体系统、OpenSandboxBackend 代码执行后端和 CompositeBackend。

#### 生命周期架构

```python
import aiosqlite
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.store.memory import InMemoryStore
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

from agent.config import settings
from agent.models.llm import llm
from agent.subagents import research_subagent
from agent.context.context import Context
from agent.sandbox.opensandbox_backend import OpenSandBoxBackend
from agent.sandbox.opensandbox_operate import create_sandboxsync

_graph = None
_conn_pool = None
_checkpointer = None
_store = None

WORKSPACE = settings.WORKSPACE
MEMORIES = os.path.join(WORKSPACE, "memories")

def get_graph():
    if _graph is None:
        raise RuntimeError("Graph not initialized. Call init_graph() first.")
    return _graph

def get_checkpointer():
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized. Call init_graph() first.")
    return _checkpointer

async def init_graph():
    global _graph, _conn_pool, _checkpointer, _store
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
        raise ValueError(
            f"Unknown CHECKPOINT_BACKEND: '{backend}'. Expected 'sqlite' or 'postgres'."
        )

    subagents = [research_subagent]

    # 创建 OpenSandbox 沙盒（用于代码执行）
    sandbox = create_sandboxsync()
    sandbox_backend = OpenSandBoxBackend(sandbox=sandbox)

    _graph = create_deep_agent(
        name="main-agent",
        model=llm,
        checkpointer=_checkpointer,
        store=_store,
        context_schema=Context,
        memory=["/memories/AGENT.md"],
        backend=CompositeBackend(
            default=sandbox_backend,         # 默认路由：OpenSandbox 代码执行后端
            routes={
                "/memories/": StoreBackend(
                    namespace=lambda ctx: (ctx.runtime.context.user_id,),
                ),
            }
        ),
        subagents=subagents,
        system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求委派对应的子智能体进行处理。",
    )

async def shutdown_graph():
    global _conn_pool
    if _conn_pool is not None:
        await _conn_pool.close()
        _conn_pool = None

__all__ = ["get_graph", "get_checkpointer", "init_graph", "shutdown_graph"]
```

#### v1.3.0 架构变更要点

**1. CompositeBackend（v1.5.0 更新）：**

| 路由               | Backend                 | namespace                          | 说明                  |
| ---------------- | ----------------------- | ---------------------------------- | ------------------- |
| `/memories/`     | `StoreBackend`          | `(user_id,)`                       | 用户级记忆隔离，存储在 LangGraph Store |
| default (其他路径)   | `OpenSandBoxBackend`     | —                                  | OpenSandbox 沙盒代码执行后端 |

- `CompositeBackend` 支持按路径前缀路由到不同的 Backend
- **v1.5.0 变更**：默认后端从 `StoreBackend` 切换为 `OpenSandBoxBackend`，提供真实的 Shell 命令执行和文件系统操作能力
- `StoreBackend` 仅用于 `/memories/` 路径，将记忆数据持久化到 LangGraph Store 中
- namespace 通过 `ctx.runtime.context` 访问运行时 Context 字段实现多租户隔离

**2. LangGraph Store 集成：**


| Store 后端       | 实现类                 | 适用场景         |
| ------------- | ------------------- | ------------ |
| `InMemoryStore` | SQLite 后端使用，内存级存储   | 开发环境         |
| `AsyncPostgresStore` | PostgreSQL 后端使用，持久化 | 生产环境 / 多实例部署 |

- Store 与 Checkpointer 共用同一个连接池（PostgreSQL 模式）
- `_store.setup()` 自动创建 Store 数据表和迁移记录表

**3. 子智能体系统：** 主智能体 `system_prompt` 引导将用户需求委派给子智能体处理。详见 [4.6 子智能体模块](#46-子智能体模块--agentsubagents)。

**4. Context 注入：** `context_schema=Context` 使 Agent 图运行时能访问 `Context` 字段，用于 Backend namespace 动态路由。

**5. 记忆系统：** `memory=["/memories/AGENT.md"]` 让 Agent 自动从 `/memories/AGENT.md` 加载持久化记忆。

**6. get_checkpointer()：** 导出检查点实例供 Conversation API 删除对话时清除 checkpoints。

#### 检查点双后端设计


| 后端         | CHECKPOINT_BACKEND | 实现类                  | 连接管理                                   | 适用场景         |
| ---------- | ------------------ | -------------------- | -------------------------------------- | ------------ |
| SQLite     | `sqlite`           | `AsyncSqliteSaver`   | `aiosqlite.connect()` 持久连接             | 开发环境 / 单机部署  |
| PostgreSQL | `postgres`         | `AsyncPostgresSaver` | `psycopg_pool.AsyncConnectionPool` 连接池 | 生产环境 / 多实例部署 |


- SQLite 后端：检查点数据库文件位于 `CHECKPOINT_DB_PATH`（默认 `./db/ke_hermes.db`），Store 使用 `InMemoryStore`
- PostgreSQL 后端：检查点和 Store 共用 `AsyncConnectionPool` 连接池，使用 `dict_row` 行工厂，启动时自动执行 `checkpointer.setup()` + `store.setup()` 创建所需表结构
- `shutdown_graph()` 在应用关闭时释放 PostgreSQL 连接池资源

### 4.6 子智能体模块 — `agent/subagents`

**职责：** 定义子智能体配置，供主智能体委派任务。v1.3.0 新增。

#### `research_subagent.py` — 研究子智能体

```python
from agent.models import qwen_llm
from tavily import TavilyClient
from deepagents import create_deep_agent
from agent.config import settings

tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

research_subagent = {
    "name": "research-agent",
    "description": "使用网络搜索进行深入研究并综合分析结果",
    "tools": [internet_search],
    "model": qwen_llm,
    "system_prompt": """你是一位严谨的研究员。你的职责是：
    1. 将研究问题分解为可搜索的查询词
    2. 使用 internet_search 查找相关信息
    3. 将研究结果综合为全面但简洁的摘要
    4. 提出论断时引用来源
    ...
    """,
}
```

**设计要点：**

- 子智能体以字典配置形式定义，包含 `name`、`description`、`tools`、`model`、`system_prompt`
- `internet_search` 工具直接定义在子智能体文件中（不再使用独立的 `agent/tools/internet_search.py`），基于 Tavily API
- 子智能体使用独立的 `qwen_llm` 模型，与主智能体的 DeepSeek 模型解耦，便于灵活替换和成本控制
- `research_subagent` 在 `init_graph()` 中通过 `subagents=[research_subagent]` 注册到主智能体

**子智能体调用流程：** 用户消息 → 主智能体分析 → 委派 `research-agent` → 子智能体执行（Tavily 搜索 + Qwen 模型分析）→ 结果返回主智能体 → 综合回复用户

#### 模块导出

```python
# agent/subagents/__init__.py
from .research_subagent import research_subagent

__all__ = ["research_subagent"]
```

**`agent/tools/__init__.py`** 当前导出空列表（`__all__ = []`），工具均定义在各自子智能体中。

### 4.7 Chat API — 对话与流式接口（v1.3.0 更新）

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

#### `/api/chat` — 普通对话（v1.3.0 更新）

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

    # 新对话自动创建记录
    if is_new:
        await create_conversation(db, user_id, thread_id, req.message)

    final_message = result["messages"][-1]
    return ChatResponse(
        response=final_message.content,
        thread_id=thread_id
    )
```

**v1.3.0 变更：**

1. **JWT 鉴权**：通过 `get_current_user_id` 依赖注入提取用户 ID，替代硬编码 `user_id`
2. **Context 注入**：构建 `Context(server_info=..., user_id=...)` 传入 Agent 图，用于 Backend namespace 路由
3. **对话记录创建**：新对话（`is_new`）自动调用 `create_conversation()` 写入数据库，标题取消息前 30 字符
4. `ChatRequest.user_id` 字段标注 TODO，实际以 JWT 提取值为准

#### `/api/chat/stream` — 流式对话

流式逻辑与普通对话一致，核心差异在于使用 `astream_events(v2)` 过滤 `on_chat_model_stream` 事件逐 token 推送。流式结束和新对话记录创建同样通过 `is_new` 判断。

#### thread_id 上下文管理


| 场景   | thread_id 行为                              |
| ---- | ----------------------------------------- |
| 新对话  | 前端不传 thread_id → 后端自动生成 UUID7             |
| 续接对话 | 前端传入上次返回的 thread_id → LangGraph 从检查点恢复上下文 |
| 流式结尾 | SSE 流最后一条消息返回 thread_id，前端保存用于后续请求        |


### 4.8 Conversation API — 对话历史 CRUD

**文件：** `api/conversation/conversation_api.py`（v1.3.0 新增）

**路由前缀：** `/api`

#### 接口总览

| 接口                              | 方法     | 请求体             | 响应体                                    | 说明            |
| ------------------------------- | ------ | --------------- | -------------------------------------- | ------------- |
| `/api/conversations`            | GET    | —               | `{code, data: [{thread_id, title, updated_at}]}` | 获取当前用户的对话列表   |
| `/api/conversations/{thread_id}` | GET    | —               | `{code, data: {thread_id, title, messages}}` | 获取某个对话的消息列表   |
| `/api/conversations/{thread_id}` | PATCH  | `{title: str}`  | `{code, data: {thread_id, title}}`     | 重命名对话         |
| `/api/conversations/{thread_id}` | DELETE | —               | `{code, data: null}`                   | 删除对话（含 DB 记录和检查点） |

#### 数据模型

```python
class ConversationItem(BaseModel):
    thread_id: str
    title: str
    updated_at: str

class MessageItem(BaseModel):
    role: str       # "user" | "assistant" | "system" | "tool"
    content: str

class ConversationDetail(BaseModel):
    thread_id: str
    title: str
    messages: list[MessageItem]

class RenameRequest(BaseModel):
    title: str
```

#### 业务逻辑

**列表查询（GET /api/conversations）：**
- 按 `user_id` 过滤，`updated_at` 倒序排列
- 返回 `thread_id`、`title`、`updated_at`

**消息详情（GET /api/conversations/{thread_id}）：**
- 校验归属（404 / 403）
- 从 LangGraph `aget_state()` 恢复消息列表
- `_message_to_dict()` 适配器将 LangChain 消息对象转为前端友好的 `{role, content}` 格式，过滤 tool 消息

**重命名（PATCH /api/conversations/{thread_id}）：**
- 校验归属后更新 `title` 字段

**删除（DELETE /api/conversations/{thread_id}）：**
- 先调用 `get_checkpointer().adelete_thread(thread_id)` 清除 LangGraph 检查点数据
- 再删除数据库中的 Conversation 记录
- 检查点不存在时忽略错误（处理新对话无消息的场景）

#### 辅助函数

```python
async def create_conversation(
    db: AsyncSession,
    user_id: str,
    thread_id: str,
    title: str
):
    """创建对话记录，供 chat 端点在新对话时调用"""
    conv = Conversation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        thread_id=thread_id,
        title=title[:30] if len(title) > 30 else title,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv
```

### 4.9 Auth API — 认证授权模块（已实现）

**文件：** `api/auth/auth_api.py`、`schemas.py`、`service.py`

**路由前缀：** `/api/auth`

**前端对齐：** 对应前端 `src/services/authApi.ts` 全部 8 个接口。

#### 数据模型 — `api/auth/schemas.py`

```python
class AccountLoginRequest(BaseModel):
    account: str = Field(min_length=2, max_length=64)
    password: str                            # RSA 加密后的密文
    captchaTicket: str | None = None
    captchaRandstr: str | None = None

class PhoneLoginRequest(BaseModel):
    phone: str = Field(pattern=r'^1[3-9]\d{9}$')
    smsCode: str = Field(min_length=4, max_length=6)

class RegisterRequest(BaseModel):
    phone: str = Field(pattern=r'^1[3-9]\d{9}$')
    smsCode: str = Field(min_length=4, max_length=6)
    nickname: str = Field(min_length=1, max_length=32)
    password: str
    agreedProtocolVersion: str

class EmailRegisterRequest(BaseModel):
    email: EmailStr
    emailCode: str
    nickname: str = Field(min_length=1, max_length=32)
    password: str
    agreedProtocolVersion: str

class AuthTokens(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int = 7200

class AuthResponse(BaseModel):
    tokens: AuthTokens
    user: UserInfo
    needProtocolAgreement: str | None = None

class RefreshRequest(BaseModel):
    refreshToken: str
```

#### API 接口


| 接口                         | 方法   | 请求体                    | 响应体                 | 说明              |
| -------------------------- | ---- | ---------------------- | ------------------- | --------------- |
| `/api/auth/public-key`     | GET  | —                      | `PublicKeyResponse` | 获取 RSA 公钥       |
| `/api/auth/login/account`  | POST | `AccountLoginRequest`  | `AuthResponse`      | 账号密码登录          |
| `/api/auth/login/phone`    | POST | `PhoneLoginRequest`    | `AuthResponse`      | 手机验证码登录         |
| `/api/auth/register/phone` | POST | `RegisterRequest`      | `AuthResponse`      | 手机号注册           |
| `/api/auth/register/email` | POST | `EmailRegisterRequest` | `AuthResponse`      | 邮箱注册            |
| `/api/auth/logout`         | POST | —                      | `ApiResponse[None]` | 退出登录（Token 失效）  |
| `/api/auth/refresh`        | POST | `RefreshRequest`       | `AuthResponse`      | 刷新 Access Token |
| `/api/auth/fail-count`     | GET  | `?account=xxx`         | `LoginFailInfo`     | 查询登录失败次数        |


#### 业务逻辑 — `api/auth/service.py`

**账号密码登录：**
1. 检查登录失败次数 → 是否被锁定（LOGIN_MAX_FAILS=5, LOCK_MINUTES=30）
2. RSA 私钥解密密码（密文 Base64 → cryptography 解密 → UTF-8 明文）
3. 查询用户（account 匹配 username/phone/email 任一字段，OR 查询）
4. bcrypt 验证密码哈希
5. 成功 → 清除失败计数, 签发 JWT Token 对, 插入 LoginRecord(success=True)
6. 失败 → 递增失败计数, 插入 LoginRecord(success=False), 检查是否达到锁定阈值

**手机号登录：** 校验 SMS → 查用户（无则自动创建）→ 签发 Token

**手机号/邮箱注册：** 校验验证码 → 检查重复 → RSA 解密密码 → bcrypt 哈希 → 创建 User → 签发 Token

**Token 刷新：** decode_token(refreshToken, "refresh") → 从数据库按 user_id 查询 → 签发新 Token 对

### 4.10 Captcha API — 验证码模块（已实现）

**文件：** `api/captcha/captcha_api.py`、`schemas.py`、`service.py`

**路由前缀：** `/api/captcha`

#### API 接口


| 接口                          | 方法   | 请求体                  | 响应体                   | 说明            |
| --------------------------- | ---- | -------------------- | --------------------- | ------------- |
| `/api/captcha/slide`        | GET  | —                    | `SlidePuzzleData`     | 获取滑动拼图数据      |
| `/api/captcha/slide/verify` | POST | `SlideVerifyRequest` | `SlideVerifyResponse` | 校验滑动拼图        |
| `/api/captcha/image`        | GET  | —                    | `ImageCaptchaData`    | 获取图形验证码（降级方案） |
| `/api/captcha/image/verify` | POST | `ImageVerifyRequest` | `{success: bool}`     | 校验图形验证码       |


**v1.2.1 增强：** 滑动拼图使用 HTTP-only Session Cookie（`captcha_session`）关联请求与验证，防止会话伪造。

### 4.11 OAuth API — 第三方登录模块（已实现）

**文件：** `api/oauth/oauth_api.py`、`schemas.py`、`service.py`

**路由前缀：** `/api/oauth`

#### API 接口


| 接口                    | 方法   | 请求体                    | 响应体                 | 说明                   |
| --------------------- | ---- | ---------------------- | ------------------- | -------------------- |
| `/api/oauth/auth-url` | GET  | `?provider=github`     | `{authUrl: string}` | 获取第三方授权跳转 URL        |
| `/api/oauth/callback` | POST | `OAuthCallbackRequest` | `AuthResponse`      | 处理 OAuth 回调并返回 Token |


**支持的平台：** GitHub、Google、微信（均 OAuth 2.0）

### 4.12 SMS API — 短信服务模块（已实现）

**文件：** `api/sms/sms_api.py`、`service.py`

**路由前缀：** `/api/sms`

| 接口              | 方法   | 请求体              | 响应体                 | 说明               |
| --------------- | ---- | ---------------- | ------------------- | ---------------- |
| `/api/sms/send` | POST | `SendSmsRequest` | `ApiResponse[None]` | 发送短信验证码（需先过滑动验证） |


**开发模式：** 未配置 `SMS_PROVIDER` 时，验证码仅记录日志并返回 `{"devCode": "6位数字"}` 到响应体。

### 4.13 Email API — 邮箱验证码模块

**文件：** `api/email/email_api.py`、`service.py`（v1.4.0 新增）

**路由前缀：** `/api/email`

| 接口 | 方法 | 请求体 | 响应体 | 说明 |
|------|------|--------|--------|------|
| `/api/email/send` | POST | `SendEmailRequest` | `ApiResponse[None]` | 发送邮箱验证码（需先过滑动验证） |

**请求模型：**

```python
class SendEmailRequest(BaseModel):
    email: EmailStr
    captchaTicket: str | None = None
    captchaRandstr: str | None = None
```

**业务逻辑（`api/email/service.py`）：**
1. 校验 captcha ticket（可选，传入时验证）
2. 检查日发送频率限制（`email:daily:{email}:{date}` Key，默认每日 5 条）
3. 生成 6 位数字验证码 → 存储到 KeyValueStore（TTL 300s）
4. 生产环境通过邮件服务发送；开发模式返回 `{"devCode": "6位数字"}`

### 4.14 MCP API — MCP 广场模块

**文件：** `api/mcp/mcp_api.py`、`schemas.py`、`service.py`（v1.4.0 新增）

**路由前缀：** `/api/mcp`

#### API 接口

| 接口 | 方法 | 请求体 | 响应体 | 说明 |
|------|------|--------|--------|------|
| `/api/mcp/tools` | GET | query: category?, search?, sort? | `ApiResponse[{tools[], total}]` | MCP 工具列表（支持分类/搜索/排序） |
| `/api/mcp/tools/{tool_id}` | GET | — | `ApiResponse[tool]` | MCP 工具详情 |
| `/api/mcp/tools/{mcp_id}/install` | POST | `InstallMcpRequest` | `ApiResponse[installation]` | 安装 MCP 工具 |
| `/api/mcp/tools/{tool_id}/uninstall` | DELETE | — | `ApiResponse[None]` | 卸载 MCP 工具 |

#### 数据模型（`api/mcp/schemas.py`）

```python
class McpConfigFieldSchema(BaseModel):
    name: str; label: str
    type: Literal['string', 'number', 'boolean', 'select']
    required: bool = False; default: Any = None
    options: list[str] | None = None; description: str | None = None

class McpToolResponse(BaseModel):
    id: str; name: str; description: str; icon: str
    author: str; version: str; license: str; repository: str
    installs: int; rating: float; category: str; tags: list[str]
    features: list[str]; official: bool
    config_schema: list[McpConfigFieldSchema]
    installed: bool = False  # 当前用户是否已安装
    created_at: str; updated_at: str

class InstallMcpRequest(BaseModel):
    mcp_id: str
    config: dict | None = None
```

#### 业务逻辑（`api/mcp/service.py`）

**列表查询：**
- 支持 `category` 分类筛选（code_execution/search/data_analysis/file_management/notification/database/dev_tools/collaboration/container/custom）
- 支持 `search` 关键字搜索（名称 + 描述模糊匹配）
- 支持 `sort` 排序（installs/rating/updated_at）
- 每个工具附加当前用户安装状态（`installed` 字段）

**安装/卸载：**
- `install_mcp_tool()`: 检查是否已安装 → 写入 `McpInstallation` 表
- `uninstall_mcp_tool()`: 验证安装记录归属 → 删除

**种子数据（`api/mcp/service.py:seed_mcp_tools()`）：**
- 从 `db/seeds/mcp_tools_seed.json` 读取 12 个官方 MCP 工具定义
- 幂等操作：按 `name` 字段检查，已存在则跳过
- 在 `server.py` lifespan startup 阶段自动调用

**12 个预置工具：**

| 工具名称 | 分类 | 安装量 | 评分 |
|---------|------|--------|------|
| 代码解释器 | code_execution | 12500 | 4.8 |
| Shell 执行器 | dev_tools | 8900 | 4.5 |
| 网络搜索 | search | 15000 | 4.9 |
| 数据分析器 | data_analysis | 6700 | 4.3 |
| 文件管理器 | file_management | 9800 | 4.6 |
| 通知中心 | notification | 5400 | 4.2 |
| 数据库浏览器 | database | 7200 | 4.4 |
| 开发工具包 | dev_tools | 11000 | 4.7 |
| 团队协作 | collaboration | 4300 | 4.1 |
| Docker 运行时 | container | 6100 | 4.3 |
| 自定义桥接 | custom | 3200 | 3.9 |
| 知识库 | search | 8500 | 4.5 |

### 4.15 Skills API — 技能管理模块

**文件：** `api/skill/skill_api.py`、`schemas.py`、`service.py`（v1.4.0 新增）

**路由前缀：** `/api/skill`

#### API 接口

| 接口 | 方法 | 请求体 | 响应体 | 说明 |
|------|------|--------|--------|------|
| `/api/skill/upload_skills` | POST | FormData (file) | `SkillsUploadResponse` | 上传技能压缩包并校验安装 |
| `/api/skill/list` | GET | query: category?, page?, page_size? | `SkillListResponse` | 分页技能列表 |
| `/api/skill/search` | GET | query: name | `SkillListResponse` | 按名称模糊搜索 |
| `/api/skill` | POST | `SkillCreateRequest` | `ApiResponse[SkillInfo]` | 手动创建技能 |
| `/api/skill/{skill_id}` | GET | — | `ApiResponse[SkillInfo]` | 获取技能详情 |
| `/api/skill/{skill_id}` | PUT | `SkillUpdateRequest` | `ApiResponse[SkillInfo]` | 更新技能 |
| `/api/skill/{skill_id}/toggle` | PATCH | `SkillToggleRequest` | `ApiResponse[SkillInfo]` | 启用/禁用切换 |
| `/api/skill/batch` | DELETE | `SkillBatchDeleteRequest` | `SkillDeleteResponse` | 批量删除技能 |
| `/api/skill/{skill_id}` | DELETE | — | `ApiResponse[None]` | 删除单个技能 |

#### 数据模型（`api/skill/schemas.py`）

```python
class SkillValidationError(BaseModel):
    field: str; message: str

class SkillUploadResult(BaseModel):
    name: str; valid: bool; errors: list[SkillValidationError]

class SkillInfo(BaseModel):
    id: str; name: str; description: str | None; icon: str | None
    category: str | None; prompt: str | None; enabled: bool
    is_builtin: bool; source: str | None; license: str | None
    user_id: str | None; validation_errors: list | None
    created_at: str; updated_at: str

class SkillCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None; icon: str | None = None
    category: str | None = None; prompt: str | None = None

class SkillBatchDeleteRequest(BaseModel):
    ids: list[str]
```

#### 核心业务逻辑（`api/skill/service.py`）

**上传校验流程（`process_skills_upload()`）：**
1. 接收 zip/tar.gz/tar.bz2/tar.xz 格式压缩包
2. 解压到临时目录，防止路径遍历攻击（`_is_safe_path()` 校验）
3. 遍历每个子目录，验证是否为合法技能包：
   - 必须包含 `SKILL.md` 文件
   - 解析 YAML Frontmatter（`---` 分隔）
   - 校验必需字段：`name`、`description`、`prompt`
4. 有效技能安装到 `workspace/skills/` 目录 + 写入数据库
5. 返回 `SkillsUploadResponse`（总数/有效/无效/跳过统计 + 逐条校验结果）

**技能操作：**
- `list_skills()`: 分页查询，支持 `category` 筛选
- `search_skills()`: 按 `name` 模糊搜索
- `toggle_skill_enabled()`: 乐观更新（先改状态 → 失败回滚）
- `delete_skills_batch()`: 批量删除，每条返回成功/失败结果
- `update_skill()`: 按 skill_id 更新字段，仅 `is_builtin=true` 时禁止修改核心字段

**分类体系（5 类）：** search / code / creative / analysis / tools / custom

#### 预安装技能

`workspace/skills/` 目录下预装两个技能：
- **github/**: GitHub 集成技能（含 SKILL.md + hooks）
- **self-improvement/**: 自我改进技能（含 hooks + scripts + references）

---

### 4.16 Agents API — 智能体管理模块

**文件：** `api/agents/agents_api.py`、`schemas.py`、`service.py`（v1.5.0 新增）

**路由前缀：** `/api/agents`

#### API 接口

| 接口 | 方法 | 请求体 | 响应体 | 说明 |
|------|------|--------|--------|------|
| `/api/agents` | GET | — | `ApiResponse[AgentListResponse]` | 获取当前用户所有智能体（首访自动创建默认主智能体） |
| `/api/agents/{agent_id}` | GET | — | `ApiResponse[AgentInfo]` | 获取单个智能体详情（含子智能体列表） |
| `/api/agents` | POST | `AgentCreateRequest` | `ApiResponse[AgentInfo]` | 创建新智能体（主智能体或子智能体） |
| `/api/agents/{agent_id}` | DELETE | — | `ApiResponse[None]` | 删除智能体（主智能体级联删除子智能体） |
| `/api/agents/{agent_id}/status` | PATCH | — | `ApiResponse[AgentInfo]` | 切换智能体激活/停用状态 |
| `/api/agents/{agent_id}/clone` | POST | — | `ApiResponse[AgentInfo]` | 克隆智能体（名称去重，含文件内容） |
| `/api/agents/{agent_id}/config` | POST | `AgentConfigRequest` | `ApiResponse[AgentInfo]` | 添加配置项（tool/skill/prompt/file/subagent） |
| `/api/agents/{agent_id}/config` | DELETE | `AgentConfigRequest` | `ApiResponse[AgentInfo]` | 移除配置项（subagent 类型会删除子智能体） |
| `/api/agents/{agent_id}/config` | PUT | `AgentConfigUpdateRequest` | `ApiResponse[AgentInfo]` | 更新配置项（文件重命名/修改描述） |
| `/api/agents/{agent_id}/file-descriptions` | GET | — | `ApiResponse[list[dict]]` | 获取智能体所有文件的描述列表 |
| `/api/agents/{agent_id}/files/{filename}` | GET | — | `ApiResponse[AgentFileContent]` | 获取文件内容（首访自动创建空记录） |
| `/api/agents/{agent_id}/files/{filename}` | PUT | `AgentFileUpdateRequest` | `ApiResponse[AgentFileContent]` | 保存文件内容（upsert） |

共 **12 个接口**，均需 JWT 鉴权。

#### 数据模型（`api/agents/schemas.py`）

```python
class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    parent_id: str | None = None  # 非空则表示创建子智能体

class AgentConfigRequest(BaseModel):
    type: str   # tool | skill | prompt | file | subagent
    value: str
    description: str = ""

class AgentInfo(BaseModel):
    id: str; name: str; type: str; status: str
    description: str
    tools: list[str]; skills: list[str]
    prompts: list[str]; files: list[str]
    sub_agents: list[str] = []    # 子智能体 ID 列表
    parent_id: str | None = None
    last_active: str | None = None
    call_count: int = 0
    undeletable: bool = False
    created_at: datetime; updated_at: datetime

class AgentFileContent(BaseModel):
    filename: str; content: str
    description: str = ""
    created_at: datetime; updated_at: datetime

class AgentFileUpdateRequest(BaseModel):
    content: str

class AgentConfigUpdateRequest(BaseModel):
    type: str       # tool | skill | prompt | file
    value: str      # 当前名称（用于定位）
    new_value: str = ""  # 新文件名（空则不重命名）
    description: str = ""
```

#### 核心业务逻辑（`api/agents/service.py`）

**智能体 CRUD：**
- `list_agents()`: 查询当前用户所有智能体，计算每个智能体的子智能体列表。首次访问时自动创建默认主智能体（名称"主智能体"，预置 tools/skills/files，标记 undeletable）
- `get_agent()`: 按 agent_id + user_id 查询，含子智能体 ID 列表
- `create_agent()`: 创建智能体。若含 parent_id 则创建子智能体（需验证父智能体存在）；否则创建主智能体（每用户限一个）。名称在用户范围内唯一
- `delete_agent()`: 删除智能体（undeletable 的不可删除）。主智能体级联删除所有子智能体
- `toggle_agent_status()`: 切换 active ↔ inactive（error 状态恢复为 inactive）
- `clone_agent()`: 深拷贝智能体，名称自动追加"(副本)"避免重复，状态置为 inactive，同时克隆 `AgentFile` 表中的文件内容

**配置管理：**
- `add_agent_config()`: 向智能体的 tools/skills/prompts/files 列表追加项。子智能体类型（subagent）仅主智能体可添加，实际调用 `create_agent()` 创建子智能体。文件类型同步创建 `AgentFile` 记录
- `remove_agent_config()`: 从列表中移除项。子智能体类型会调用 `delete_agent()` 删除子智能体。文件类型同步清理 `AgentFile` 表
- `update_agent_config()`: 文件重命名（同步更新 agent.files 和 AgentFile.filename）或修改描述

**文件操作：**
- `get_agent_file()`: 读取文件内容，首访自动创建空 AgentFile 记录
- `save_agent_file()`: 保存文件内容（upsert）
- `list_agent_file_descriptions()`: 返回 `[{filename, description}]` 列表

**默认智能体配置：**

| 类别 | 预设项 |
|------|--------|
| 文件 | AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, MEMORY.md |
| 工具 | web_search, file_reader, code_executor |
| 技能 | code_analysis, debugging, optimization |

---

### 4.17 Providers API — 模型管理模块

**文件：** `api/providers/providers_api.py`、`schemas.py`、`service.py`（v1.5.0 新增）

**路由前缀：** `/api/providers`

#### API 接口

| 接口 | 方法 | 请求体 | 响应体 | 说明 |
|------|------|--------|--------|------|
| `/api/providers` | GET | — | `ApiResponse[list[ProviderResponse]]` | 获取所有提供商（含嵌套模型列表） |
| `/api/providers` | POST | `ProviderCreateRequest` | `ApiResponse[ProviderResponse]` | 创建提供商 |
| `/api/providers/{provider_id}` | PUT | `ProviderUpdateRequest` | `ApiResponse[ProviderResponse]` | 更新提供商 |
| `/api/providers/{provider_id}` | DELETE | — | `ApiResponse[None]` | 删除提供商（级联删除模型） |
| `/api/providers/{provider_id}/models` | POST | `ModelCreateRequest` | `ApiResponse[ModelResponse]` | 在提供商下创建模型 |
| `/api/providers/{provider_id}/models/{model_id}` | PUT | `ModelUpdateRequest` | `ApiResponse[ModelResponse]` | 更新模型信息 |
| `/api/providers/{provider_id}/models/{model_id}` | DELETE | — | `ApiResponse[None]` | 删除模型 |
| `/api/providers/{provider_id}/models/{model_id}/clone` | POST | — | `ApiResponse[ModelResponse]` | 克隆模型（名称追加"-clone"） |
| `/api/providers/{provider_id}/models/{model_id}/status` | PATCH | — | `ApiResponse[ModelResponse]` | 切换模型状态 |

共 **9 个接口**，均需 JWT 鉴权。

#### 数据模型（`api/providers/schemas.py`）

```python
class ModelParamSchema(BaseModel):
    """单个模型默认参数。"""
    key: str; label: str
    value: float | str
    min: float | None = None; max: float | None = None
    step: float | None = None
    type: str  # number | text | select
    options: list[str] | None = None

class ModelCreateRequest(BaseModel):
    name: str; display_name: str
    type: str            # llm | vision | audio | video | embedding | image-gen | speech
    status: str = "active"
    context_window: int | None = None
    description: str = ""
    release_date: str | None = None
    params: list[ModelParamSchema] = []

class ModelResponse(BaseModel):
    id: str; name: str; display_name: str
    type: str; status: str
    context_window: int | None; call_count: int
    description: str; release_date: str | None
    params: list[ModelParamSchema]
    used_by_agents: list[str]
    created_at: datetime; updated_at: datetime

class ProviderCreateRequest(BaseModel):
    name: str; logo: str = "🤖"
    api_base: str; api_key: str = ""
    description: str = ""; website: str = ""

class ProviderResponse(BaseModel):
    id: str; name: str; logo: str; status: str
    api_base: str; api_key: str
    description: str; website: str
    models: list[ModelResponse] = []  # 嵌套模型列表
    created_at: datetime; updated_at: datetime
```

#### 核心业务逻辑（`api/providers/service.py`）

- `list_providers()`: 查询当前用户所有提供商，按创建时间排序，每个提供商嵌套其下所有模型
- `create_provider()`: 创建提供商，名称全局唯一
- `update_provider()`: 按 provider_id + user_id 校验归属后更新
- `delete_provider()`: 先级联删除提供商下所有 AIModel 记录，再删除 Provider
- `create_model()`: 在指定提供商下创建模型，params 存储为 JSON
- `update_model()`: 更新模型全部字段（含 call_count 和 used_by_agents）
- `delete_model()`: 删除模型
- `clone_model()`: 克隆模型，name 追加"-clone"，display_name 追加"(副本)"，call_count 清零
- `toggle_model_status()`: 切换 active ↔ inactive

---

### 4.18 Sandbox — 沙盒代码执行模块

**文件：** `agent/sandbox/opensandbox_backend.py`、`opensandbox_operate.py`（v1.5.0 新增）

#### OpenSandBoxBackend

`OpenSandBoxBackend` 继承 `BaseSandbox`，实现 `SandboxBackendProtocol` 协议，为 DeepAgents 提供真实的代码执行和文件操作能力。

```python
class OpenSandBoxBackend(BaseSandbox):
    def __init__(self, *, sandbox: SandboxSync, timeout: int = 30 * 60, sync_polling_interval=0.1):
        ...

    def id(self) -> str:           # 返回沙盒唯一标识符
        ...

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        # 通过 OpenSandbox API 执行 Shell 命令
        # 返回: {output, exit_code, truncated}
        ...

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        # 从沙盒下载文件（路径必须以 / 开头）
        # 支持文件不存在检测和错误分类
        ...

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        # 批量上传文件到沙盒
        ...
```

**关键设计：**

- **代码执行**：使用 `self._sandbox.commands.run(command)` 执行 Shell 命令，返回 stdout + stderr 合并输出和退出码
- **超时处理**：命令超时时捕获异常，返回 exit_code=124
- **文件下载**：`download_files()` 执行前检查文件是否存在，返回分类错误信息（file_not_found / read_error / check_error）
- **文件上传**：`upload_files()` 先将 bytes 解码为 UTF-8 字符串，再通过 `WriteEntry` 批量写入沙盒
- 基类 `BaseSandbox` 提供文件系统操作的标准实现

#### 沙盒生命周期管理（`opensandbox_operate.py`）

| 函数 | 类型 | 说明 |
|------|------|------|
| `create_sandboxsync()` | 同步 | 创建或连接到已有沙盒，返回 `SandboxSync` 实例 |
| `create_sandbox()` | 异步 | 异步版本，返回 `Sandbox` 实例 |
| `list_running_sandbox()` | — | 列出所有运行中的沙盒（待实现） |

**沙盒创建配置：**
- **镜像**：`sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:v1.0.2`
- **资源**：CPU 2 核 / Memory 3Gi
- **超时**：10 分钟无使用自动停止
- **网络策略**：默认拒绝出站，仅放行 pypi.org 和 *.github.com
- **入口**：`/opt/opensandbox/code-interpreter.sh`，环境变量 `PYTHON_VERSION=3.11`

**配置来源**（`ConnectionConfigSync` / `ConnectionConfig`）：
- `domain`: 从 `settings.OPENSANDBOX_DOMAIN` 读取
- `api_key`: 从 `settings.OPENSANDBOX_API_KEY` 读取
- `use_server_proxy=True`, `request_timeout=60s`
- HTTP 连接池限制：最大 20 连接

---

## 5. 数据存储设计

### 5.1 业务数据库 — SQLAlchemy ORM

#### User 模型 — `db/models/user.py`

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    nickname: Mapped[str] = mapped_column(String(64), default="")
    password_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=True)
    avatar: Mapped[str] = mapped_column(String(256), default="")
    workspace_id: Mapped[str] = mapped_column(String(36), default="default")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### UserOAuth 模型 — `db/models/user_oauth.py`

```python
class UserOAuth(Base):
    __tablename__ = "user_oauths"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    open_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("provider", "open_id", name="uq_oauth_provider_openid"),
    )
```

#### LoginRecord 模型 — `db/models/login_record.py`

```python
class LoginRecord(Base):
    __tablename__ = "login_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip: Mapped[str] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

#### Conversation 模型 — `db/models/conversation.py`（v1.3.0 新增）

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    thread_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="新对话")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

- `user_id` 与 `thread_id` 分离：一个用户可拥有多个对话线程
- `updated_at` 自动更新，用于前端列表排序
- 业务数据库 `DATABASE_BACKEND` 支持 `sqlite` 和 `postgres` 双后端切换

#### Skill 模型 — `db/models/skill.py` (v1.4.0 新增)

```python
class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    valid: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    license: Mapped[str | None] = mapped_column(String(64), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    validation_errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at / updated_at: datetime 自动时间戳
```

- `source`: 来源标记（upload/manual/repo）
- `validation_errors`: JSON 字段存储校验错误列表
- `is_builtin`: 内置技能不可删除

#### McpTool 模型 — `db/models/mcp_tool.py` (v1.4.0 新增)

```python
class McpTool(Base):
    __tablename__ = "mcp_tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(256), nullable=True)
    author: Mapped[str | None]; version: Mapped[str | None]; license: Mapped[str | None]
    repository: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=0)
    installs: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)         # JSON 数组
    features: Mapped[list] = mapped_column(JSON, default=list)     # JSON 数组
    official: Mapped[bool] = mapped_column(Boolean, default=False)
    config_schema: Mapped[list] = mapped_column(JSON, default=list) # JSON 数组
    created_at / updated_at: datetime 自动时间戳
```

#### McpInstallation 模型 — `db/models/mcp_installation.py` (v1.4.0 新增)

```python
class McpInstallation(Base):
    __tablename__ = "mcp_installations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    mcp_tool_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: datetime

    __table_args__ = (
        UniqueConstraint("user_id", "mcp_tool_id", name="uq_user_mcp"),
    )
```

- 复合唯一约束：同一用户不能重复安装同一工具

#### Agent 模型 — `db/models/agent.py` (v1.5.0 新增)

```python
class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(16), default="sub")       # main / sub
    status: Mapped[str] = mapped_column(String(16), default="inactive") # active / inactive / error
    description: Mapped[str] = mapped_column(Text, default="")
    parent_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tools: Mapped[list] = mapped_column(JSON, default=list)            # 工具名称列表
    skills: Mapped[list] = mapped_column(JSON, default=list)           # 技能名称列表
    prompts: Mapped[list] = mapped_column(JSON, default=list)          # 提示词列表
    files: Mapped[list] = mapped_column(JSON, default=list)            # 文件名称列表
    undeletable: Mapped[bool] = mapped_column(Boolean, default=False)   # 是否不可删除
    created_at: Mapped[datetime]; updated_at: Mapped[datetime]
```

- `parent_id = NULL` 表示主智能体，非空表示子智能体（指向父智能体）
- `tools/skills/prompts/files` 均为 JSON 数组，存储配置项名称的字符串列表
- `undeletable`: 默认主智能体标记为 True，防止误删

#### AgentFile 模型 — `db/models/agent_file.py` (v1.5.0 新增)

```python
class AgentFile(Base):
    __tablename__ = "agent_files"
    __table_args__ = (UniqueConstraint("agent_id", "filename", name="uq_agent_file"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"),
                                          nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")              # Markdown/文本内容
    description: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime]; updated_at: Mapped[datetime]
```

- `(agent_id, filename)` 复合唯一约束：同一智能体下文件名唯一
- `agent_id` 外键关联 `agents.id`，级联删除
- `content` 存储 Markdown/文本文件内容，`description` 存储文件用途描述

#### Provider 模型 — `db/models/provider.py` (v1.5.0 新增)

```python
class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    logo: Mapped[str] = mapped_column(String(16), default="🤖")        # emoji 图标
    status: Mapped[str] = mapped_column(String(16), default="unconfigured") # connected/error/unconfigured
    api_base: Mapped[str] = mapped_column(String(512), nullable=False)  # API 基础 URL
    api_key: Mapped[str] = mapped_column(String(512), default="")       # API 密钥
    description: Mapped[str] = mapped_column(Text, default="")
    website: Mapped[str] = mapped_column(String(512), default="")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime]; updated_at: Mapped[datetime]
```

- `name` 全局唯一，`user_id` 索引支持多用户隔离
- `logo` 使用短 emoji 字符串（如 "🤖"、"🔷"），前端直接渲染
- `status` 三种状态：connected（已连接）、error（连接失败）、unconfigured（未配置）
- `api_key` 明文存储，生产环境建议加密

#### AIModel 模型 — `db/models/ai_model.py` (v1.5.0 新增)

```python
class AIModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    provider_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)          # 机器名（如 gpt-4o）
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)  # 展示名（如 GPT-4o）
    type: Mapped[str] = mapped_column(String(16), nullable=False)           # llm/vision/audio/video/embedding/image-gen/speech
    status: Mapped[str] = mapped_column(String(16), default="active")      # active/beta/deprecated
    context_window: Mapped[int | None] = mapped_column(Integer, nullable=True)
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    release_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    params: Mapped[list] = mapped_column(JSON, default=list)               # 默认参数列表
    used_by_agents: Mapped[list] = mapped_column(JSON, default=list)        # 使用此模型的智能体名列表
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime]; updated_at: Mapped[datetime]
```

- `provider_id` 关联 `providers` 表（非外键约束，由业务层保证一致性）
- `type` 支持 7 种模型类型：llm / vision / audio / video / embedding / image-gen / speech
- `status` 三种：active（活跃）、beta（测试版）、deprecated（已弃用）
- `params` 为 JSON 数组，每项含 `{key, label, value, min, max, step, type, options}`
- `used_by_agents` 为 JSON 数组，记录使用此模型的智能体名称
- `context_window` 和 `release_date` 为可选的元数据字段

### 5.2 数据库引擎 — `db/engine.py`（v1.3.0 更新）

```python
from agent.config import settings

async_engine = None
if settings.DATABASE_BACKEND == "sqlite":
    async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
elif settings.DATABASE_BACKEND == "postgres":
    async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
else:
    raise Exception("DATABASE_BACKEND must be sqlite or postgres.")
```

引擎创建时根据 `DATABASE_BACKEND` 选择对应驱动，`get_db()` 生成器提供请求级会话管理（自动提交/回滚/关闭）。

### 5.3 KeyValueStore — 临时数据

`core/store.py` 定义 `KeyValueStore` 抽象基类，实现 `RedisStore`（Redis 可用时）和 `MemoryStore`（Redis 不可用时自动降级）。


| 方法                     | 说明                 |
| ---------------------- | ------------------ |
| `get(key)`             | 获取值（过期自动返回 None）   |
| `set(key, value, ttl)` | 设置值 + TTL（秒）       |
| `delete(key)`          | 删除键                |
| `exists(key)`          | 检查键是否存在            |
| `incr(key)`            | 自增计数器              |
| `ttl(key)`             | 查询剩余过期时间（秒），-2=不存在 |

**Key 命名规范与用途：**


| Key 模式                     | 内容                   | TTL    | 用途               |
| -------------------------- | -------------------- | ------ | ---------------- |
| `captcha:slide:{session}`  | `{gap_x}:{y}`        | 300s   | 滑动拼图缺口坐标         |
| `captcha:ticket:{ticket}`  | `{randstr}`          | 300s   | 滑动验证通过票据         |
| `captcha:image:{key}`      | `{code}`             | 300s   | 图形验证码正确答案        |
| `sms:{phone}`              | `{code}`             | 300s   | 短信验证码            |
| `email:{email}`            | `{code}`             | 300s   | 邮箱验证码            |
| `sms:daily:{phone}:{date}` | `{count}`            | 86400s | 短信日发送计数          |
| `oauth:state:{state}`      | `{provider}`         | 600s   | OAuth CSRF state |
| `login:fail:{account}`     | `{count}:{until_ts}` | 1800s  | 登录失败次数与锁定时间      |


### 5.4 LangGraph 持久化层

| 组件        | SQLite 后端             | PostgreSQL 后端              | 用途           |
| --------- | --------------------- | -------------------------- | ------------ |
| Checkpointer | `AsyncSqliteSaver`     | `AsyncPostgresSaver`        | 对话状态检查点，支持多轮对话 |
| Store     | `InMemoryStore`        | `AsyncPostgresStore`        | 长期记忆/文件存储    |

- SQLite 模式：检查点持久化到文件，Store 为内存级（重启丢失）
- PostgreSQL 模式：检查点和 Store 共用同一 `AsyncConnectionPool`，均持久化到数据库

---

## 6. 安全设计

### 6.1 密码安全

```
前端：RSA 公钥加密 → 密文传输 → 后端：RSA 私钥解密 → bcrypt 哈希存储
```

- RSA 密钥对惰性生成（首次使用时 `_ensure_keys()`），密钥长度由 `RSA_KEY_SIZE` 配置（默认 2048）
- `cryptography` 库 PKCS1v15 padding 解密
- `bcrypt` 库哈希存储

### 6.2 JWT Token 双 Token 机制


| Token 类型      | 有效期  | 用途               | 刷新策略           |
| ------------- | ---- | ---------------- | -------------- |
| Access Token  | 2 小时 | 请求鉴权（Bearer 头）   | 过期后用 Refresh 换 |
| Refresh Token | 7 天  | 换取新 Access Token | 前端存储，过期需重新登录   |


JWT 密钥在首次启动时自动生成 32 字节 hex 随机密钥并持久化到 `.jwt_secret` 文件，确保服务重启后已有 Token 仍有效。

### 6.3 登录安全

- **失败锁定**：同一 account 连续失败 5 次 → 锁定 30 分钟
- **验证码前置**：登录/注册前需通过滑动拼图验证码
- **短信限流**：同一手机号每日最多 5 条
- **密码不进日志**：日志中间件过滤请求体中的 password 字段

### 6.4 请求安全

- CORS 白名单（生产环境限制 allow_origins）
- Authorization Bearer 头校验（`get_current_user_id` 依赖注入）
- Chat API 和 Conversation API 均需 JWT 鉴权

---

## 7. API 接口总览与前后端对照

### 7.1 完整接口清单


| 接口                              | 方法     | 模块           | 后端实现  | 说明                            |
| ------------------------------- | ------ | ------------ | ----- | ----------------------------- |
| `/api/chat`                     | POST   | agent        | ✅ 已实现 | 普通对话（含 JWT 鉴权 + Context）      |
| `/api/chat/stream`              | POST   | agent        | ✅ 已实现 | 流式对话（SSE）                     |
| `/api/conversations`            | GET    | conversation | ✅ 已实现 | 对话列表（v1.3.0 新增）               |
| `/api/conversations/{thread_id}` | GET    | conversation | ✅ 已实现 | 对话消息详情（v1.3.0 新增）             |
| `/api/conversations/{thread_id}` | PATCH  | conversation | ✅ 已实现 | 重命名对话（v1.3.0 新增）              |
| `/api/conversations/{thread_id}` | DELETE | conversation | ✅ 已实现 | 删除对话 + 检查点（v1.3.0 新增）          |
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
| `/api/email/send`               | POST   | email        | ✅ 已实现 | 发送邮箱验证码（v1.4.0 新增）           |
| `/api/oauth/auth-url`           | GET    | oauth        | ✅ 已实现 | 获取 OAuth 授权 URL               |
| `/api/oauth/callback`           | POST   | oauth        | ✅ 已实现 | OAuth 回调处理                    |
| `/api/mcp/tools`                | GET    | mcp          | ✅ 已实现 | MCP 工具列表（v1.4.0 新增）          |
| `/api/mcp/tools/{tool_id}`     | GET    | mcp          | ✅ 已实现 | MCP 工具详情（v1.4.0 新增）          |
| `/api/mcp/tools/{mcp_id}/install` | POST | mcp          | ✅ 已实现 | 安装 MCP 工具（v1.4.0 新增）         |
| `/api/mcp/tools/{tool_id}/uninstall` | DELETE | mcp      | ✅ 已实现 | 卸载 MCP 工具（v1.4.0 新增）         |
| `/api/skill/upload_skills`       | POST   | skill        | ✅ 已实现 | 上传技能压缩包（v1.4.0 新增）           |
| `/api/skill/list`                | GET    | skill        | ✅ 已实现 | 技能列表（v1.4.0 新增）              |
| `/api/skill/search`              | GET    | skill        | ✅ 已实现 | 搜索技能（v1.4.0 新增）              |
| `/api/skill`                     | POST   | skill        | ✅ 已实现 | 创建技能（v1.4.0 新增）              |
| `/api/skill/{skill_id}`          | GET    | skill        | ✅ 已实现 | 技能详情（v1.4.0 新增）              |
| `/api/skill/{skill_id}`          | PUT    | skill        | ✅ 已实现 | 更新技能（v1.4.0 新增）              |
| `/api/skill/{skill_id}/toggle`   | PATCH  | skill        | ✅ 已实现 | 切换技能启用/禁用（v1.4.0 新增）         |
| `/api/skill/batch`               | DELETE | skill        | ✅ 已实现 | 批量删除技能（v1.4.0 新增）            |
| `/api/skill/{skill_id}`          | DELETE | skill        | ✅ 已实现 | 删除单个技能（v1.4.0 新增）            |
| `/api/agents`                    | GET    | agents       | ✅ 已实现 | 智能体列表（v1.5.0 新增，首访自动创建默认智能体） |
| `/api/agents/{agent_id}`         | GET    | agents       | ✅ 已实现 | 智能体详情（v1.5.0 新增）             |
| `/api/agents`                    | POST   | agents       | ✅ 已实现 | 创建智能体（v1.5.0 新增）             |
| `/api/agents/{agent_id}`         | DELETE | agents       | ✅ 已实现 | 删除智能体（v1.5.0 新增，主智能体级联删除子智能体）       |
| `/api/agents/{agent_id}/status`  | PATCH  | agents       | ✅ 已实现 | 切换智能体状态（v1.5.0 新增）           |
| `/api/agents/{agent_id}/clone`   | POST   | agents       | ✅ 已实现 | 克隆智能体（v1.5.0 新增）             |
| `/api/agents/{agent_id}/config`  | POST   | agents       | ✅ 已实现 | 添加配置项（v1.5.0 新增）             |
| `/api/agents/{agent_id}/config`  | DELETE | agents       | ✅ 已实现 | 移除配置项（v1.5.0 新增）             |
| `/api/agents/{agent_id}/config`  | PUT    | agents       | ✅ 已实现 | 更新配置项（v1.5.0 新增）             |
| `/api/agents/{agent_id}/file-descriptions` | GET | agents   | ✅ 已实现 | 文件描述列表（v1.5.0 新增）           |
| `/api/agents/{agent_id}/files/{filename}` | GET | agents    | ✅ 已实现 | 获取文件内容（v1.5.0 新增）            |
| `/api/agents/{agent_id}/files/{filename}` | PUT | agents    | ✅ 已实现 | 保存文件内容（v1.5.0 新增）            |
| `/api/providers`                 | GET    | providers    | ✅ 已实现 | 提供商列表（v1.5.0 新增，含嵌套模型）       |
| `/api/providers`                 | POST   | providers    | ✅ 已实现 | 创建提供商（v1.5.0 新增）             |
| `/api/providers/{provider_id}`   | PUT    | providers    | ✅ 已实现 | 更新提供商（v1.5.0 新增）             |
| `/api/providers/{provider_id}`   | DELETE | providers    | ✅ 已实现 | 删除提供商（v1.5.0 新增，级联删除模型）       |
| `/api/providers/{provider_id}/models` | POST | providers | ✅ 已实现 | 创建模型（v1.5.0 新增）              |
| `/api/providers/{provider_id}/models/{model_id}` | PUT | providers | ✅ 已实现 | 更新模型（v1.5.0 新增）    |
| `/api/providers/{provider_id}/models/{model_id}` | DELETE | providers | ✅ 已实现 | 删除模型（v1.5.0 新增）  |
| `/api/providers/{provider_id}/models/{model_id}/clone` | POST | providers | ✅ 已实现 | 克隆模型（v1.5.0 新增） |
| `/api/providers/{provider_id}/models/{model_id}/status` | PATCH | providers | ✅ 已实现 | 切换模型状态（v1.5.0 新增） |


共 **51 个接口**（v1.4.0 为 30 个，v1.5.0 新增 12 个 Agents + 9 个 Providers 接口）。

### 7.2 统一响应格式

大部分接口使用 `ApiResponse<T>` 统一响应包装：

```python
class ApiResponse(BaseModel, Generic[T]):
    code: int = 0           # 0=成功
    data: T | None = None
    message: str = "ok"
    requestId: str
    timestamp: int
```

Conversation API 的列表/详情/重命名/删除接口使用自定义响应格式（`{"code": 0, "data": ...}`），保持与前端约定一致。

---

## 8. 数据流

### 8.1 普通对话（v1.3.0 更新）

```
前端 POST /api/chat {"message": "用户输入", "thread_id": "..." | null}
    ↓
JWT 鉴权（get_current_user_id 提取 user_id）
    ↓
agent_api.py → ChatRequest 校验
    ↓
is_new = not req.thread_id
thread_id = req.thread_id or uuid7()
构建 Context(server_info="ke_hermes_server", user_id=user_id)
    ↓
get_graph().ainvoke({"messages": [HumanMessage(...)]}, config=..., context=context)
    ↓
LangGraph 从检查点恢复上下文 → 主智能体分析 → 必要时委派子智能体（research-agent）
    ↓
子智能体执行（Tavily 搜索 + Qwen LLM 分析）→ 结果返回主智能体
    ↓
AsyncSqliteSaver / AsyncPostgresSaver 自动写入新检查点
Store 持久化 /memories/ 文件更新
    ↓
取 result["messages"][-1].content → AIMessage
    ↓
新对话：create_conversation(db, user_id, thread_id, title=message[:30])
    ↓
ChatResponse {"response": "智能体回复", "thread_id": "..."}
    ↓
前端保存 thread_id 用于后续对话
```

### 8.2 流式对话

```
前端 POST /api/chat/stream {"message": "用户输入", "thread_id": "..." | null}
    ↓
（鉴权 + Context 注入同普通对话）
    ↓
get_graph().astream_events(..., version="v2")
    ↓
过滤 on_chat_model_stream → 逐 token SSE 推送
    ↓
最后推送 thread_id + 新对话自动创建（create_conversation）
```

### 8.3 账号密码登录

```
前端 GET /api/auth/public-key → RSA 公钥 → JSEncrypt 加密 → POST /api/auth/login/account

后端：
  auth/service.py → 检查锁定 → RSA 解密 → 数据库查用户 → bcrypt 验证 → JWT 签发
  → AuthResponse { tokens: {accessToken, refreshToken}, user: {...} }
```

### 8.4 模块依赖关系（v1.3.0 全图）

```
server.py
  ├── load_dotenv()           ← 加载 .env
  ├── Windows SelectorEventLoop monkeypatch  ← Windows 兼容
  ├── CORS 中间件
  ├── lifespan:
  │     ├── init_db()         ← 自动建表（业务库，DATABASE_BACKEND 双后端，11 个模型）
  │     ├── seed_mcp_tools()  ← MCP 工具种子数据（v1.4.0）
  │     ├── init_graph()      ← 检查点 + Store + Agent + 子智能体 + OpenSandboxBackend + CompositeBackend
  │     ├── create_store()    ← Redis / MemoryStore
  │     ├── set_store()       ← 注入依赖
  │     ├── init_jwt()        ← JWT 密钥持久化
  │     └── shutdown_graph()  ← 关闭连接池
  └── api.router
        ├── agent_api.router (prefix="/api")
        │     ├── get_current_user_id → JWT 鉴权
        │     ├── get_graph() / get_checkpointer() → agent.graph
        │     │     ├── agent.models.llm (DeepSeek, 主智能体)
        │     │     ├── agent.models.qwen_llm (Qwen 3.6 Plus, 子智能体)
        │     │     ├── agent.subagents.research_subagent (Tavily + Qwen)
        │     │     ├── agent.sandbox.opensandbox_backend (OpenSandBoxBackend 代码执行)
        │     │     ├── agent.sandbox.opensandbox_operate (沙盒创建/连接)
        │     │     ├── agent.context.Context (server_info + user_id)
        │     │     ├── AsyncSqliteSaver / AsyncPostgresSaver (检查点)
        │     │     ├── InMemoryStore / AsyncPostgresStore (LangGraph Store)
        │     │     ├── CompositeBackend (OpenSandboxBackend default + StoreBackend 路由)
        │     │     └── agent.config.settings
        │     └── api.conversation.create_conversation → DB
        ├── agents_api.router (prefix="/api/agents")      ← v1.5.0 新增
        │     ├── get_current_user_id → JWT 鉴权
        │     ├── get_db() → SQLAlchemy
        │     └── Agent / AgentFile ORM 模型
        ├── conversation_api.router (prefix="/api")  ← v1.3.0 新增
        │     ├── get_current_user_id → JWT 鉴权
        │     ├── get_db() → SQLAlchemy
        │     ├── get_graph().aget_state() → 消息恢复
        │     └── get_checkpointer().adelete_thread() → 检查点清除
        ├── auth_api.router (prefix="/api/auth")
        ├── captcha_api.router (prefix="/api/captcha")
        ├── oauth_api.router (prefix="/api/oauth")
        ├── sms_api.router (prefix="/api/sms")
        ├── email_api.router (prefix="/api/email")         ← v1.4.0 新增
        │     └── captcha ticket 校验 + KeyValueStore
        ├── mcp_api.router (prefix="/api/mcp")             ← v1.4.0 新增
        │     ├── get_current_user_id → JWT 鉴权
        │     ├── get_db() → SQLAlchemy
        │     └── seed_mcp_tools() → lifespan startup
        ├── providers_api.router (prefix="/api/providers")  ← v1.5.0 新增
        │     ├── get_current_user_id → JWT 鉴权
        │     ├── get_db() → SQLAlchemy
        │     └── Provider / AIModel ORM 模型
        └── skill_api.router (prefix="/api/skill")         ← v1.4.0 新增
              ├── get_db() → SQLAlchemy
              └── workspace/skills/ 文件系统
```

---

## 9. 环境变量设计

所有配置通过 `.env` 文件管理。


| 变量名                          | 类型  | 默认值                                                   | 说明                              |
| ---------------------------- | --- | ----------------------------------------------------- | ------------------------------- |
| `DEEPSEEK_API_KEY`           | str | `""`                                                  | DeepSeek API 密钥（必填）             |
| `DEEPSEEK_MODEL`             | str | `"deepseek-v4-pro"`                                   | 主智能体 LLM 模型名称                   |
| `DEEPSEEK_BASE_URL`          | str | `"https://api.deepseek.com/v1"`                       | DeepSeek API 地址                 |
| `DASHSCOPE_API_KEY`          | str | `""`                                                  | DashScope API 密钥（Qwen + Embedding） |
| `DASHSCOPE_EMBEDDING`        | str | `"text-embedding-v4"`                                 | 向量模型名称                          |
| `DASHSCOPE_BASE_URL`         | str | `"https://dashscope.aliyuncs.com/compatible-mode/v1"` | DashScope 兼容地址                  |
| `HOST`                       | str | `"127.0.0.1"`                                         | 服务监听地址                          |
| `PORT`                       | int | `8000`                                                | 服务监听端口                          |
| `OPENSANDBOX_DOMAIN`         | str | `"http://127.0.0.1:8080"`                             | OpenSandbox 沙盒服务地址（v1.5.0 新增）   |
| `OPENSANDBOX_API_KEY`        | str | `""`                                                  | OpenSandbox API 密钥（v1.5.0 新增）     |
| `WORKSPACE`                  | str | `auto`                                                | 智能体工作目录（自动推导为 backend/workspace/） |
| `TAVILY_API_KEY`             | str | `""`                                                  | Tavily 互联网搜索 API 密钥             |
| `DATABASE_BACKEND`           | str | `"sqlite"`                                            | 业务数据库后端（sqlite / postgres）      |
| `DATABASE_URL`               | str | `""`                                                  | 业务数据库连接字符串                      |
| `DATABASE_PATH`              | str | `""`                                                  | 业务数据库文件路径（SQLite）               |
| `CHECKPOINT_BACKEND`         | str | `"sqlite"`                                            | LangGraph 检查点后端（sqlite / postgres） |
| `CHECKPOINT_DB_URL`          | str | `"postgresql://127.0.0.1:5432/ke_hermes"`             | PostgreSQL 检查点 + Store 数据库连接串    |
| `CHECKPOINT_DB_PATH`         | str | `"./db/ke_hermes.db"`                                 | SQLite 检查点数据库文件路径                |
| `STORE_BACKEND`              | str | `"sqlite"`                                            | LangGraph Store 后端（sqlite / postgres） |
| `STORE_DB_URL`               | str | `"postgresql://127.0.0.1:5432/ke_hermes"`             | PostgreSQL Store 数据库连接串          |
| `STORE_DB_PATH`              | str | `"./db/ke_hermes.db"`                                 | SQLite Store 数据库文件路径             |
| `JWT_SECRET_KEY`             | str | `""`                                                  | JWT 签名密钥（缺省自动生成持久化）              |
| `JWT_ACCESS_EXPIRE`          | int | `7200`                                                | Access Token 有效期（秒）             |
| `JWT_REFRESH_EXPIRE`         | int | `604800`                                              | Refresh Token 有效期（秒）            |
| `RSA_KEY_SIZE`               | int | `2048`                                                | RSA 密钥长度                        |
| `LOGIN_MAX_FAILS`            | int | `5`                                                   | 登录失败锁定阈值                        |
| `LOGIN_LOCK_MINUTES`         | int | `30`                                                  | 锁定时间（分钟）                        |
| `SMS_DAILY_LIMIT`            | int | `5`                                                   | 短信每日上限                          |
| `CAPTCHA_EXPIRE`             | int | `300`                                                 | 验证码过期时间（秒）                      |
| `SLIDE_THRESHOLD`            | int | `5`                                                   | 滑动验证容差（像素）                      |
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


---

## 10. 关键设计决策

### 10.1 load_dotenv 调用时序

`load_dotenv()` 在 `server.py` 最顶部调用，位于所有业务模块导入之前。原因：Python 导入链在模块级立即执行，导入链触发 `ChatOpenAI` 和 `OpenAIEmbeddings` 实例创建，这两个实例在初始化时需要读取 API Key。若 `load_dotenv()` 在导入之后执行，实例创建时环境变量为空，会报认证错误。

### 10.2 模型实例模块级创建

LLM 和 Embeddings 实例在模块级（而非函数内）创建，所有请求共享同一实例。`ChatOpenAI` 和 `OpenAIEmbeddings` 内部管理连接池和客户端对象，模块级创建避免重复初始化开销。

### 10.3 OpenAI 兼容协议调用

DeepSeek 和 DashScope 均提供 OpenAI API 兼容接口，`langchain-openai` 的 `ChatOpenAI` 和 `OpenAIEmbeddings` 通过设置 `base_url` 参数即可调用这些服务，无需引入各自专用 SDK。

### 10.4 SSE 流式响应格式

流式接口使用 SSE 协议，每条事件格式为 `data: {"token": "..."}\n\n`。选择 `fetch` + `ReadableStream` 而非浏览器原生 `EventSource`，因为 `EventSource` 仅支持 GET 请求，而对话需要 POST 发送用户消息。

### 10.5 统一响应格式 ApiResponse

所有接口返回统一的 `ApiResponse<T>` 包装，确保前端可以通过同一拦截器处理。Conversation API 使用自定义 `{"code": 0, "data": ...}` 格式保持前端约定一致。

### 10.6 SQLite 开发 + PostgreSQL 生产

开发环境使用 SQLite（零配置），生产环境切换 PostgreSQL（通过 `DATABASE_BACKEND` 和 `CHECKPOINT_BACKEND` 环境变量）。通过 `DATABASE_BACKEND` 适配业务数据库，`CHECKPOINT_BACKEND` 适配 LangGraph 检查点和 Store。

### 10.7 RSA 前端加密 + bcrypt 后端存储

密码传输使用 RSA 非对称加密（前端 JSEncrypt 公钥加密，后端 `cryptography` 库私钥解密），存储使用 `bcrypt` 库单向哈希。

### 10.8 KeyValueStore 抽象层

所有临时数据通过 `KeyValueStore` 抽象接口操作，不直接依赖 Redis。当 Redis 不可用时自动降级为线程安全的 `MemoryStore`。

### 10.9 JWT 密钥持久化

JWT 签名密钥在首次启动时自动生成并持久化到 `.jwt_secret` 文件。后续重启从文件读取，确保已签发的 Token 在服务重启后仍然有效。

### 10.10 Agent 图生命周期管理

Agent 图通过 `init_graph()` / `get_graph()` / `get_checkpointer()` / `shutdown_graph()` 生命周期模式管理。原因：

1. **异步初始化**：检查点和 Store 需要 `await` 初始化
2. **资源清理**：PostgreSQL 连接池需要在应用关闭时释放
3. **FastAPI lifespan 集成**：初始化在 lifespan startup 阶段完成

### 10.11 检查点和 Store 双后端设计

通过 `CHECKPOINT_BACKEND` 环境变量选择 LangGraph 持久化后端：

- **SQLite**（默认）：`AsyncSqliteSaver` + `InMemoryStore`，适合开发/单机部署
- **PostgreSQL**：`AsyncPostgresSaver` + `AsyncPostgresStore` + `AsyncConnectionPool`，适合生产/多实例部署

检查点和 Store 在 PostgreSQL 模式下共用同一连接池。

### 10.12 thread_id 上下文管理

- 前端首次对话不传 `thread_id` → 后端生成 UUID7
- 前端保存返回的 `thread_id`，后续携带同一 ID → LangGraph 从检查点恢复
- 流式 SSE 结束时推送 `thread_id`

### 10.13 CompositeBackend 与多租户隔离（v1.3.0 新增，v1.5.0 更新）

`CompositeBackend` 按路径前缀路由到不同的 Backend：

- `/memories/` → `StoreBackend(namespace=(user_id,))`：用户级记忆隔离
- default → `OpenSandBoxBackend`：OpenSandbox 沙盒代码执行后端（v1.5.0 从 StoreBackend 切换）

namespace 通过 `ctx.runtime.context` 动态获取，实现多用户数据隔离。

### 10.14 子智能体架构（v1.3.0 新增）

### 10.14 子智能体架构（v1.3.0 新增）

主智能体（DeepSeek）负责分析用户需求并委派任务，子智能体（research-agent，Qwen 3.6 Plus）负责执行具体任务（网络搜索 + 分析）。益处：

- **模型解耦**：主/子智能体使用不同模型，灵活替换和成本控制
- **职责分离**：主智能体专注对话理解与委派，子智能体专注领域任务
- **扩展性**：新增子智能体只需添加配置字典，无需修改图结构

### 10.15 对话历史 CRUD（v1.3.0 新增）

Conversation API 实现对话的完整生命周期管理：

- 对话记录存储在业务数据库中（`Conversation` 模型）
- 消息内容从 LangGraph checkpoints 恢复（`get_graph().aget_state()`）
- 删除对话时同步清除 DB 记录和 LangGraph checkpoints（`checkpointer.adelete_thread()`）

### 10.16 OpenSandbox 沙盒代码执行（v1.5.0 新增）

Agent 图默认后端从 `StoreBackend` 切换为 `OpenSandBoxBackend`，为智能体提供真实的代码执行能力。设计要点：

- **`OpenSandBoxBackend`** 实现 `BaseSandbox` 协议，封装 OpenSandbox 的 `commands.run()` / `files.read()` / `files.write()` API
- 沙盒在 `init_graph()` 时通过 `create_sandboxsync()` 创建，与 Agent 图生命周期一致
- 沙盒配置网络策略（默认 deny + pypi.org/github.com 白名单），10 分钟闲置自动回收
- 文件上下传支持路径遍历校验（绝对路径 + 文件存在性检查 + 错误分类）

### 10.17 智能体管理 API（v1.5.0 新增）

Agents API 实现智能体的完整生命周期管理：

- **主/子智能体层级**：`parent_id` 字段建立父子关系，主智能体级联删除子智能体
- **默认智能体**：新用户首次访问 `GET /api/agents` 时自动创建默认主智能体（预置 tools/skills/files，标记 undeletable）
- **配置管理**：tools/skills/prompts/files 以 JSON 数组存储，支持添加/移除/更新
- **文件管理**：AgentFile 表独立存储文件内容，通过 `(agent_id, filename)` 唯一约束保证一致性
- **克隆机制**：深拷贝智能体配置 + 文件内容，名称自动去重

### 10.18 模型管理 API（v1.5.0 新增）

Providers API 实现提供商和模型的完整 CRUD 管理：

- **两级层级**：Provider → Model，API 响应中提供商嵌套其下所有模型列表
- **模型类型**：支持 7 种类型（llm / vision / audio / video / embedding / image-gen / speech）
- **参数管理**：模型默认参数以 JSON 数组存储，支持 number / text / select 三种参数类型
- **状态管理**：模型支持 active / beta / deprecated 三种状态，提供商支持 connected / error / unconfigured 三种状态
- **克隆**：克隆模型时 name 追加 "-clone"，display_name 追加 "(副本)"，call_count 清零

---

## 11. 测试设计

### 11.1 测试分层

```
tests/
├── conftest.py                 # 公共 fixtures（AsyncClient + lifespan 管理）
├── unit_tests/
│   ├── test_config.py          # Settings 类环境变量读取（3 个用例）
│   ├── test_models.py          # LLM/Embeddings 实例导入（3 个用例）
│   ├── test_agent.py           # graph 导出函数验证（2 个用例）
│   └── test_agent_service.py   # 智能体管理服务单元测试（v1.5.0 新增）
└── integration_tests/
    ├── test_server.py          # FastAPI 实例 + 路由注册验证（3 个用例）
    ├── test_agent_api.py       # Chat API 接口测试（5 个用例，含 skipif 条件跳过）
    └── test_agents_api.py      # Agents API 集成测试（v1.5.0 新增）
```

### 11.2 测试配置

```python
# conftest.py
@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):  # triggers init_db + init_graph
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
```

- `conftest.py` 通过 `app.router.lifespan_context(app)` 手动触发 lifespan，确保数据库和 Agent 图在测试前完成初始化
- 需要真实 API Key 的用例使用 `pytest.mark.skipif` 条件跳过

### 11.3 执行命令

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
# 1. 创建虚拟环境并安装依赖
uv venv
uv pip install -e .

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 DEEPSEEK_API_KEY、DASHSCOPE_API_KEY、TAVILY_API_KEY 等

# 3. 启动服务
uv run python run.py
```

### 12.2 前置条件

1. Python >= 3.11
2. 虚拟环境已创建并安装依赖
3. `.env` 文件已配置必要的 API Key
4. Redis 服务（可选 — 不可用时自动降级为内存存储）
5. SQLite 数据库文件（自动创建于 `db/ke-hermes.db`）
6. `workspace/` 目录（自动创建）

### 12.3 API 文档

启动后访问 `http://127.0.0.1:8000/docs`，FastAPI 自动生成交互式 Swagger UI 文档。11 个功能模块共 51 个接口均自动注册。

---

## 13. 前后端实施差异与待实现项

### 13.1 前后端功能对照（v1.5.0）


| 功能模块       | 前端 v1.2.1 | 后端 v1.5.0 | 差异                                     |
| ---------- | --------- | --------- | -------------------------------------- |
| 智能体对话 (普通) | ✅ 已实现     | ✅ 已实现     | **一致**（后端已加 JWT 鉴权 + Context + 子智能体委派 + OpenSandbox 代码执行） |
| 智能体对话 (流式) | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 智能体管理     | ⬜         | ✅ 已实现     | **后端已实现**（CRUD + 配置 + 文件，12 接口, v1.5.0 新增） |
| 对话历史 CRUD  | ⬜ 已设计     | ✅ 已实现     | **后端已实现**（列表/详情/重命名/删除）               |
| 模型管理      | ⬜ 已设计     | ✅ 已实现     | **后端已实现**（提供商/模型 CRUD + 克隆 + 状态，9 接口, v1.5.0 新增） |
| 账号密码登录     | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 手机验证码登录    | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 手机号注册      | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 邮箱注册       | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 滑动拼图验证码    | ✅ 已实现     | ✅ 已实现     | **一致**（Session Cookie 关联）             |
| 图形验证码      | ✅ 已实现     | ✅ 已实现     | **一致**                                 |
| 短信发送       | ✅ 已实现     | ✅ 已实现     | **一致**（开发模式返回 devCode）                 |
| OAuth 登录   | ✅ 已实现     | ✅ 已实现     | **一致**（GitHub/Google/微信）               |
| Token 管理   | ✅ 已实现     | ✅ 已实现     | **一致**（双 Token + 自动刷新 + JWT 鉴权）       |
| RSA 加密     | ✅ 已实现     | ✅ 已实现     | **一致**（前端 JSEncrypt / 后端 cryptography） |
| MCP 广场     | ⬜         | ✅ 已实现     | **后端已实现**（v1.4.0 新增）                   |
| Skills 管理  | ⬜         | ✅ 已实现     | **后端已实现**（v1.4.0 新增）                   |
| 邮箱验证码     | ✅ 已实现     | ✅ 已实现     | **一致**（v1.4.0 新增）                      |
| 用户管理       | ⬜         | ⬜         | 前端无管理界面，后端无管理 API                      |


### 13.2 待实现项


| 优先级 | 模块       | 接口数 | 说明                           |
| --- | -------- | --- | ---------------------------- |
| P2  | 通知系统     | 2+  | 对接前端 TopBar 通知铃铛按钮           |
| P3  | 用户管理 API | 4+  | 用户信息编辑、头像上传、密码修改             |
| P3  | 邮件发送服务   | 1   | 邮箱验证码实际发送（当前仅开发模式）           |


### 13.3 从 v1.0.0 到 v1.5.0 的变更总结


| 项目       | v1.0.0 (初始)          | v1.5.0 (当前)                                                                                                                   |
| -------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| API 模块   | 1 (agent)            | 11 (agent + agents + auth + captcha + oauth + sms + email + conversation + mcp + providers + skill)                          |
| 数据模型     | 0                    | 11 (User + UserOAuth + LoginRecord + Conversation + Skill + McpTool + McpInstallation + Agent + AgentFile + Provider + AIModel) |
| Agent 架构 | 单智能体 + 无文件后端         | 主智能体 + 子智能体（research-agent）+ CompositeBackend（OpenSandboxBackend default + StoreBackend 路由）+ LangGraph Store + Context   |
| LLM 模型  | 1 (DeepSeek)         | 2 (DeepSeek 主智能体 + Qwen 3.6 Plus 子智能体)                                                                                      |
| 文件后端     | 无                    | CompositeBackend（OpenSandboxBackend 代码执行 + StoreBackend 记忆存储）                                                              |
| 沙盒执行     | 无                    | OpenSandbox（Shell 命令执行 + 文件上下传 + 网络策略 + 资源限制）                                                                            |
| 中间件      | 0                    | CORS + 依赖注入体系（get_db/get_store/get_client_ip/get_current_user_id）                                                            |
| 检查点后端    | 无                    | 双后端（SQLite + PostgreSQL），含 Store 持久化                                                                                        |
| 安全       | 无                    | RSA + JWT + bcrypt + 登录锁定 + JWT 鉴权（Chat + Agents + Conversation + MCP + Providers + Skill API）                            |
| 存储抽象     | 无                    | KeyValueStore（Redis + MemoryStore）                                                                                            |
| 对话上下文    | 无                    | thread_id 多轮对话 + 对话历史 CRUD + 检查点/Store 持久化                                                                                |
| 智能体管理    | 无                    | 智能体 CRUD + 主/子层级 + 配置管理 + 文件操作 + 克隆（v1.5.0 新增）                                                                          |
| 模型管理     | 无                    | 提供商/模型 CRUD + 7 种模型类型 + 嵌套响应 + 克隆 + 状态切换（v1.5.0 新增）                                                                    |
| MCP 广场    | 无                    | 工具列表（分类/搜索/排序）+ 详情 + 安装/卸载 + 12 个预置种子工具（v1.4.0 新增）                                                                    |
| Skills 管理 | 无                    | 上传校验（zip/tar）+ CRUD + 批量删除 + 启用/禁用切换 + 文件系统安装（v1.4.0 新增）                                                              |
| 邮箱验证     | 无                    | 邮箱验证码发送 + 频率限制 + 开发模式（v1.4.0 新增）                                                                                       |
| 外部依赖     | DeepSeek + DashScope | + bcrypt + cryptography + httpx + Pillow + redis(可选) + tavily + psycopg(可选) + python-multipart + opensandbox + opensandbox-code-interpreter |
| 环境变量     | 8                    | 41                                                                                                                             |
| API 接口   | 2                    | 51                                                                                                                             |


---

> 本文档 v1.5.0 基于实际代码实现更新。v1.5.0 重点新增了智能体管理模块（Agents API，12 接口 + CRUD + 配置管理 + 文件操作）、模型管理模块（Providers API，9 接口 + 提供商/模型 CRUD + 克隆 + 状态切换）、OpenSandbox 沙盒后端模块（代码执行 + 文件上下传）；数据模型从 7 个扩展到 11 个（新增 Agent/AgentFile/Provider/AIModel）；Agent 图默认后端从 StoreBackend 切换为 OpenSandboxBackend；API 接口从 30 个扩展到 51 个；API 子模块从 9 个扩展到 11 个。
