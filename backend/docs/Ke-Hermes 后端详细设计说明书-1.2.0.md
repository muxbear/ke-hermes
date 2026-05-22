# Ke-Hermes 后端详细设计说明书 — v1.2.1

| 版本    | 日期         | 作者  | 变更说明                                         |
| ----- | ---------- | --- | -------------------------------------------- |
| 1.0.0 | 2026-05-18 | -   | 后端详细设计初版：智能体架构、Chat API、流式对话              |
| 1.2.0 | 2026-05-18 | -   | 对照前端 v1.2.0 详细设计，新增登录/注册/验证码/OAuth 模块完整设计方案，补充安全体系、数据存储、前后端接口对齐与差异分析 |
| 1.2.1 | 2026-05-19 | -   | 完成 v1.2.0 全部模块编码实现；新增 KeyValueStore 存储抽象层（Redis + 内存降级）；文档对照实际代码更新（bcrypt/cryptography 替代 passlib、JWT 密钥持久化、验证码 Session Cookie、SMS 开发模式等） |

---

## 目录

1. [概述](#1-概述)
2. [技术栈](#2-技术栈)
3. [目录结构](#3-目录结构)
4. [模块详细设计](#4-模块详细设计)
   - 4.1 [服务入口 — server.py](#41-服务入口--serverpy)
   - 4.2 [配置模块 — agent/config](#42-配置模块--agentconfig)
   - 4.3 [模型模块 — agent/models](#43-模型模块--agentmodels)
   - 4.4 [智能体图 — agent/graph.py](#44-智能体图--agentgraphpy)
   - 4.5 [Chat API — 对话与流式接口](#45-chat-api--对话与流式接口)
   - 4.6 [Auth API — 认证授权模块](#46-auth-api--认证授权模块)
   - 4.7 [Captcha API — 验证码模块](#47-captcha-api--验证码模块)
   - 4.8 [OAuth API — 第三方登录模块](#48-oauth-api--第三方登录模块)
   - 4.9 [SMS API — 短信服务模块](#49-sms-api--短信服务模块)
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

本文档为 Ke-Hermes 后端的详细设计说明书 v1.2.1，对照实际代码实现编写。文档覆盖：

- **已实现模块**：智能体框架、Chat API（普通对话 + SSE 流式）、认证授权、验证码、OAuth 第三方登录、短信服务
- **基础设施**：KeyValueStore 存储抽象层（Redis + 内存降级）、RSA + JWT + bcrypt 安全体系、SQLAlchemy 异步 ORM

文档供后端开发人员编码实现、代码审查和后期维护使用。

### 1.2 技术栈

| 组件          | 技术/框架              | 版本要求         | 用途                    |
| ----------- | ------------------ | ------------ | --------------------- |
| Web 框架      | FastAPI            | >=0.100.0    | HTTP API 路由与请求处理      |
| ASGI 服务器    | uvicorn            | >=0.20.0     | 服务运行与部署              |
| 智能体框架       | deepagents         | >=0.6.1      | 智能体图构建               |
| LLM/模型调用    | langchain-openai   | >=1.2.0      | DeepSeek/DashScope 模型调用 |
| 配置管理        | pydantic-settings  | >=2.0.0      | 环境变量配置类              |
| 环境加载        | python-dotenv      | >=1.0.1      | .env 文件加载             |
| 图执行引擎       | langgraph          | >=1.0.0      | 智能体图状态机运行            |
| 密码哈希        | bcrypt             | >=4.0        | 密码哈希存储与校验            |
| JWT          | PyJWT              | >=2.8        | Token 签发与验证           |
| RSA 加密      | cryptography       | >=42.0       | RSA 密钥对生成与加解密         |
| 数据校验        | pydantic           | >=2.0        | 请求/响应模型定义            |
| 异步数据库       | SQLAlchemy[asyncio] | >=2.0        | ORM + 连接池             |
| 异步 SQLite 驱动 | aiosqlite          | >=0.20       | 开发环境数据库驱动             |
| 数据库          | SQLite / PostgreSQL | —            | 开发环境 / 生产环境           |
| 验证码生成       | Pillow             | >=10.0       | 图形验证码图片生成            |
| 键值存储        | redis (可选)         | >=5.0        | Redis 缓存存储；不可用时自动降级为内存存储 |
| OAuth        | httpx              | >=0.27       | 第三方 OAuth API 调用       |
| Python      | CPython            | >=3.11,<4.0  | 运行环境                  |

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
│   │   ├── __init__.py              # 导出 graph
│   │   ├── config/
│   │   │   ├── __init__.py          # 导出 settings 实例
│   │   │   └── config.py            # Settings 配置类定义
│   │   ├── models/
│   │   │   ├── __init__.py          # 导出 llm, embeddings
│   │   │   ├── llm.py               # ChatOpenAI 实例（DeepSeek）
│   │   │   └── em.py                # OpenAIEmbeddings 实例（DashScope）
│   │   ├── tools/
│   │   │   └── __init__.py          # 工具列表导出（预留）
│   │   ├── utils/
│   │   │   └── __init__.py          # 辅助方法导出（预留）
│   │   └── graph.py                 # deepagents 智能体图定义
│   │
│   ├── api/
│   │   ├── __init__.py              # 导出顶层 router（汇总 5 个子模块）
│   │   ├── deps.py                  # 依赖注入（get_db, get_store, get_client_ip）
│   │   ├── agent/
│   │   │   ├── __init__.py          # 导出 agent router
│   │   │   └── agent_api.py         # 智能体 API 路由与数据模型
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
│   │   ├── oauth/
│   │   │   ├── __init__.py          # 导出 oauth router
│   │   │   ├── oauth_api.py         # OAuth API 路由（2 个接口）
│   │   │   ├── schemas.py           # OAuth 请求/响应 Pydantic 模型
│   │   │   └── service.py           # OAuth 业务逻辑（GitHub/Google/微信）
│   │   └── sms/
│   │       ├── __init__.py          # 导出 sms router
│   │       ├── sms_api.py           # 短信 API 路由（1 个接口）
│   │       └── service.py           # 短信发送业务逻辑（含 SendSmsRequest 模型）
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── engine.py                # SQLAlchemy async engine + sessionmaker + init_db
│   │   ├── base.py                  # DeclarativeBase
│   │   └── models/
│   │       ├── __init__.py          # 导出所有 model
│   │       ├── user.py              # User 模型
│   │       ├── user_oauth.py        # UserOAuth 第三方绑定模型
│   │       └── login_record.py      # LoginRecord 登录记录模型
│   │
│   └── core/
│       ├── __init__.py
│       ├── security.py              # bcrypt 密码哈希、cryptography RSA 加解密、PyJWT Token 签发/验证
│       ├── store.py                 # KeyValueStore 抽象 + RedisStore / MemoryStore 实现
│       └── response.py              # 统一响应格式 ApiResponse[T]
│
├── db/                              # SQLite 数据库文件目录
│   └── ke-hermes.db                 # 开发环境 SQLite 数据库文件
│
├── tests/
│   ├── conftest.py                  # 测试公共 fixtures
│   ├── unit_tests/
│   │   ├── test_config.py           # 配置模块测试
│   │   ├── test_models.py           # 模型实例测试
│   │   ├── test_agent.py            # 智能体导出测试
│   │   ├── test_security.py         # JWT/RSA/密码哈希测试
│   │   └── test_auth_service.py     # 认证业务逻辑测试
│   └── integration_tests/
│       ├── test_server.py           # 服务启动测试
│       ├── test_agent_api.py        # Chat API 接口测试
│       ├── test_auth_api.py         # 认证 API 接口测试
│       ├── test_captcha_api.py      # 验证码 API 接口测试
│       └── test_oauth_api.py        # OAuth API 接口测试
│
├── docs/
│   ├── requirements.md              # 需求文档
│   ├── test_plan.md                 # 测试规划文档
│   ├── design.md                    # 原设计说明书（当前实现）
│   └── Ke-Hermes 后端详细设计说明书-1.2.1.md  # 本文件
│
├── .env                             # 环境变量配置（不入库）
├── .env.example                     # 环境变量示例
├── .jwt_secret                      # JWT 签名密钥持久化文件（自动生成）
└── pyproject.toml                   # 项目元数据与依赖
```

---

## 4. 模块详细设计

### 4.1 服务入口 — `server.py`

**职责：** 创建 FastAPI 应用实例，加载环境变量，初始化基础设施，注册所有 API 路由。

**v1.2.1 完整实现：**

```python
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

load_dotenv()                     # 必须在业务导入之前

from api import router
from api.deps import set_store
from core.store import create_store
from db.engine import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()               # 启动时创建数据库表
    store = await create_store()   # 初始化 KeyValueStore（Redis 或内存降级）
    set_store(store)
    from core.security import _get_jwt_secret as init_jwt
    init_jwt()                    # 预初始化 JWT secret，确保重启后不变
    yield


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
2. `create_store()` → 尝试连接 Redis，失败则降级为 `MemoryStore`
3. `set_store(store)` → 注入到 FastAPI 依赖注入系统
4. `init_jwt()` → 读取或生成持久化 JWT 签名密钥

**路由注册链：**

```
api/__init__.py → 汇总所有子模块 router
  ├── api/agent/   → agent_api.router  (prefix="/api")      ← 已实现
  ├── api/auth/    → auth_api.router   (prefix="/api/auth") ← 已实现
  ├── api/captcha/ → captcha_api.router(prefix="/api/captcha")← 已实现
  ├── api/oauth/   → oauth_api.router  (prefix="/api/oauth")← 已实现
  └── api/sms/     → sms_api.router    (prefix="/api/sms")  ← 已实现
        ↓
server.py → app.include_router(router)
```

**启动命令：**

```bash
cd backend
uvicorn src.server:app --host 127.0.0.1 --port 8000
```

### 4.2 配置模块 — `agent/config`

**职责：** 集中管理所有环境变量配置。

#### `config.py` — Settings 类（v1.2.0 扩展）

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ---- LLM ----
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # ---- Embeddings ----
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_EMBEDDING: str = "text-embedding-v4"
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ---- Server ----
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # ---- Database ----
    DATABASE_URL: str = ""                                          # 必填，如 sqlite+aiosqlite:///./db/ke-hermes.db

    # ---- JWT ----
    JWT_SECRET_KEY: str = ""             # HS256 签名密钥（缺省自动生成 RSA 密钥对）
    JWT_ACCESS_EXPIRE: int = 7200        # Access Token 有效期（秒）
    JWT_REFRESH_EXPIRE: int = 604800     # Refresh Token 有效期（秒，7 天）

    # ---- RSA ----
    RSA_KEY_SIZE: int = 2048             # RSA 密钥长度

    # ---- Rate Limit ----
    LOGIN_MAX_FAILS: int = 5             # 登录失败锁定阈值
    LOGIN_LOCK_MINUTES: int = 30         # 锁定时间（分钟）
    SMS_DAILY_LIMIT: int = 5             # 短信每日上限

    # ---- Captcha ----
    CAPTCHA_EXPIRE: int = 300            # 验证码过期时间（秒）
    SLIDE_THRESHOLD: int = 5             # 滑动验证容差（像素）

    # ---- OAuth ----
    OAUTH_GITHUB_CLIENT_ID: str = ""
    OAUTH_GITHUB_CLIENT_SECRET: str = ""
    OAUTH_GOOGLE_CLIENT_ID: str = ""
    OAUTH_GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_WECHAT_CLIENT_ID: str = ""
    OAUTH_WECHAT_CLIENT_SECRET: str = ""

    # ---- Redis ----
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # ---- SMS ----
    SMS_PROVIDER: str = ""               # aliyun / tencent
    SMS_ACCESS_KEY: str = ""
    SMS_SECRET_KEY: str = ""
    SMS_SIGN_NAME: str = ""
    SMS_TEMPLATE_CODE: str = ""
```

### 4.3 模型模块 — `agent/models`

**职责：** 创建 LLM 和向量模型实例（与 v1.0.0 保持一致，无变更）。

#### `llm.py` — DeepSeek ChatOpenAI

```python
from langchain_openai import ChatOpenAI
from agent.config import settings

llm = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)
```

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

### 4.4 智能体图 — `agent/graph.py`

与 v1.0.0 保持一致，无变更。

```python
from deepagents import create_deep_agent
from agent.models.llm import llm

graph = create_deep_agent(
    model=llm,
    system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求提供准确、有用的回答。",
)
```

### 4.5 Chat API — 对话与流式接口

**文件：** `api/agent/agent_api.py`（已实现）

**路由前缀：** `/api`

| 接口                | 方法   | 请求体                    | 响应体                           | 状态 |
| ----------------- | ---- | ---------------------- | ----------------------------- | -- |
| `/api/chat`       | POST | `{"message":"string"}` | `{"response":"string"}`       | 已实现 |
| `/api/chat/stream` | POST | `{"message":"string"}` | SSE `data:{"token":"..."}\n\n` | 已实现 |

#### 数据模型

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)    # 空字符串返回 422

class ChatResponse(BaseModel):
    response: str

class StreamToken(BaseModel):
    token: str
```

#### `/api/chat` — 普通对话

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=req.message)]}
    )
    final_message = result["messages"][-1]
    return ChatResponse(response=final_message.content)
```

**调用流程：** ChatRequest → `graph.ainvoke()` → DeepSeek LLM → 取最后 AIMessage → ChatResponse

#### `/api/chat/stream` — 流式对话

```python
@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_generator():
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=req.message)]},
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].text
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**调用流程：** ChatRequest → `graph.astream_events(v2)` → 过滤 `on_chat_model_stream` → 逐 token 以 SSE 推送

### 4.6 Auth API — 认证授权模块（已实现）

**文件：** `api/auth/auth_api.py`、`schemas.py`、`service.py`

**路由前缀：** `/api/auth`

**前端对齐：** 对应前端 `src/services/authApi.ts` 全部 8 个接口。

#### 数据模型 — `api/auth/schemas.py`

```python
from pydantic import BaseModel, Field, EmailStr

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
    password: str                            # RSA 加密后的密文
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

class UserInfo(BaseModel):
    id: str
    nickname: str
    avatar: str
    phone: str
    email: str
    workspaceId: str

class AuthResponse(BaseModel):
    tokens: AuthTokens
    user: UserInfo
    needProtocolAgreement: str | None = None

class RefreshRequest(BaseModel):
    refreshToken: str

class LoginFailInfo(BaseModel):
    failCount: int
    lockedUntil: int | None                # Unix timestamp, null 表示未锁定

class PublicKeyResponse(BaseModel):
    publicKey: str                         # PEM 格式 RSA 公钥
```

#### API 接口

| 接口                        | 方法   | 请求体                  | 响应体             | 说明              |
| ------------------------- | ---- | -------------------- | --------------- | --------------- |
| `/api/auth/public-key`    | GET  | —                    | `PublicKeyResponse` | 获取 RSA 公钥       |
| `/api/auth/login/account` | POST | `AccountLoginRequest` | `AuthResponse`    | 账号密码登录          |
| `/api/auth/login/phone`   | POST | `PhoneLoginRequest`   | `AuthResponse`    | 手机验证码登录         |
| `/api/auth/register/phone`| POST | `RegisterRequest`     | `AuthResponse`    | 手机号注册           |
| `/api/auth/register/email`| POST | `EmailRegisterRequest`| `AuthResponse`    | 邮箱注册            |
| `/api/auth/logout`        | POST | —                    | `ApiResponse[None]` | 退出登录（Token 失效）    |
| `/api/auth/refresh`       | POST | `RefreshRequest`      | `AuthResponse`    | 刷新 Access Token |
| `/api/auth/fail-count`    | GET  | `?account=xxx`       | `LoginFailInfo`   | 查询登录失败次数        |

#### 业务逻辑 — `api/auth/service.py`

**1. 账号密码登录流程：**

```
1. 检查登录失败次数 → 是否被锁定（LOGIN_MAX_FAILS=5, LOCK_MINUTES=30）
   状态存储：KeyValueStore 中 key=login:fail:{account} → "{count}:{until_ts}"
2. RSA 私钥解密密码（密文 Base64 → cryptography 解密 → UTF-8 明文）
3. 查询用户（account 匹配 username/phone/email 任一字段，OR 查询）
4. bcrypt 验证密码哈希
5. 成功 → 清除失败计数, 签发 JWT Token 对, 插入 LoginRecord(success=True)
   失败 → 递增失败计数, 插入 LoginRecord(success=False), 检查是否达到锁定阈值
```

**2. 手机号登录流程：**

```
1. 从 KeyValueStore 校验短信验证码（key=sms:{phone}），通过后删除
2. 查询或创建用户（phone 匹配；不存在则自动创建，nickname="User"+后4位）
3. 签发 JWT Token 对 → 返回 AuthResponse
```

**3. 手机号/邮箱注册流程：**
```
1. 校验短信/邮箱验证码 → 删除已使用的验证码
2. 检查 phone/email 是否已被注册（409 Conflict）
3. RSA 解密密码 → bcrypt 哈希存储
4. 创建 User 记录 → 签发 JWT Token 对 → 返回 AuthResponse
```

**4. Token 刷新：**
```
1. decode_token(refreshToken, expected_type="refresh") → 验证签名+类型+过期
2. 从数据库按 user_id 查询用户（用户不存在则 401）
3. 签发新的 Token 对 → 返回 AuthResponse
```

**3. Token 签发策略：**

```python
# core/security.py
import time
import jwt

def create_token_pair(user_id: str) -> TokenPair:
    secret = _get_jwt_secret()
    now = int(time.time())
    access_payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + settings.JWT_ACCESS_EXPIRE,   # 7200s
    }
    refresh_payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + settings.JWT_REFRESH_EXPIRE,  # 604800s
    }
    return TokenPair(
        accessToken=jwt.encode(access_payload, secret, algorithm="HS256"),
        refreshToken=jwt.encode(refresh_payload, secret, algorithm="HS256"),
        expiresIn=settings.JWT_ACCESS_EXPIRE,
    )
```

**JWT Secret 持久化策略：**
- 优先从 `JWT_SECRET_KEY` 环境变量读取
- 若为空，从项目根目录 `.jwt_secret` 文件读取
- 若文件不存在，自动生成 32 字节 hex 随机密钥并写入 `.jwt_secret`
- 确保服务器重启后已有 Token 仍然有效

**4. 依赖注入 — `api/deps.py`：**

```python
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from core.store import KeyValueStore
from db.engine import get_db as _get_db

_store: KeyValueStore | None = None

def set_store(store: KeyValueStore) -> None:
    global _store
    _store = store

async def get_store() -> KeyValueStore:
    assert _store is not None, "Store not initialized"
    return _store

async def get_db() -> AsyncSession:
    async for session in _get_db():
        yield session

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"
```

依赖注入提供三个核心函数：
- `get_db` — 异步数据库会话（自动提交/回滚）
- `get_store` — KeyValueStore 实例（Redis 或内存存储）
- `get_client_ip` — 客户端真实 IP（优先 X-Forwarded-For 头）

### 4.7 Captcha API — 验证码模块（已实现）

**文件：** `api/captcha/captcha_api.py`、`schemas.py`、`service.py`

**路由前缀：** `/api/captcha`

**前端对齐：** 对应前端 `src/services/captchaApi.ts`。
**v1.2.1 增强：** 使用 HTTP-only Session Cookie（`captcha_session`）关联滑动拼图请求与验证，防止会话伪造。

#### 数据模型 — `api/captcha/schemas.py`

```python
class SlidePuzzleData(BaseModel):
    bgImage: str       # Base64 背景图
    slideImage: str    # Base64 滑块图
    y: int             # 滑块 Y 坐标

class SlideVerifyRequest(BaseModel):
    distance: int      # 滑块拖动距离
    track: list[int]   # 拖动轨迹采样点
    ticket: str | None = None

class SlideVerifyResponse(BaseModel):
    success: bool
    ticket: str | None = None    # 一次性票据
    randstr: str | None = None   # 用于后续验证关联

class ImageCaptchaData(BaseModel):
    image: str         # Base64 图形验证码图片
    key: str           # Redis 中的验证 key

class ImageVerifyRequest(BaseModel):
    key: str
    code: str
```

#### API 接口

| 接口                           | 方法   | 请求体                | 响应体                 | 说明           |
| ---------------------------- | ---- | ------------------ | ------------------- | ------------ |
| `/api/captcha/slide`         | GET  | —                  | `SlidePuzzleData`    | 获取滑动拼图数据     |
| `/api/captcha/slide/verify`  | POST | `SlideVerifyRequest` | `SlideVerifyResponse` | 校验滑动拼图       |
| `/api/captcha/image`         | GET  | —                  | `ImageCaptchaData`   | 获取图形验证码（降级方案） |
| `/api/captcha/image/verify`  | POST | `ImageVerifyRequest` | `{success: bool}`    | 校验图形验证码      |

#### 业务逻辑 — `api/captcha/service.py`

**滑动拼图验证码：**

```
GET /api/captcha/slide:
  1. 生成随机 Y 坐标 + 缺口 X 坐标
  2. 使用 Pillow 合成背景图 + 缺口滑块图
  3. 正确答案存入 Redis: key=session_id → {x, y, expires=CAPTCHA_EXPIRE}
  4. 返回 bgImage(Base64), slideImage(Base64), y

POST /api/captcha/slide/verify:
  1. 从 Redis 取正确答案
  2. 比较 distance 与正确答案差值是否 < SLIDE_THRESHOLD
  3. 验证拖动轨迹（速度、加速度曲线防机器）
  4. 成功 → 生成 ticket(UUID) + randstr → 存入 Redis → 返回
```

**图形验证码（降级方案）：**

```
GET /api/captcha/image:
  1. 生成随机 4 位字母数字组合
  2. 使用 Pillow 绘制含干扰线/噪点的图片
  3. 正确答案存入 Redis: key=UUID → {code, expires=CAPTCHA_EXPIRE}
  4. 返回 image(Base64), key(UUID)

POST /api/captcha/image/verify:
  1. 从 Redis 按 key 取正确答案
  2. 不区分大小写比较
  3. 成功 → 删除 Redis key
```

### 4.8 OAuth API — 第三方登录模块（已实现）

**文件：** `api/oauth/oauth_api.py`、`schemas.py`、`service.py`

**路由前缀：** `/api/oauth`

**前端对齐：** 对应前端 `src/services/oauthApi.ts`。

#### 数据模型 — `api/oauth/schemas.py`

```python
class OAuthAuthUrlResponse(BaseModel):
    authUrl: str

class OAuthCallbackRequest(BaseModel):
    provider: str      # "github" | "google" | "wechat" | "weibo" | "qq"
    code: str          # OAuth 授权码
    state: str         # CSRF state
```

#### API 接口

| 接口                   | 方法   | 请求体                   | 响应体                 | 说明               |
| -------------------- | ---- | --------------------- | ------------------- | ---------------- |
| `/api/oauth/auth-url` | GET  | `?provider=github`     | `{authUrl: string}` | 获取第三方授权跳转 URL    |
| `/api/oauth/callback` | POST | `OAuthCallbackRequest` | `AuthResponse`       | 处理 OAuth 回调并返回 Token |

#### 业务逻辑 — `api/oauth/service.py`

**支持的第三方平台（v1.2.1 已实现 3 个）：**

| Provider | 授权方式        | 配置项                        | 状态 |
| -------- | ----------- | -------------------------- | -- |
| GitHub   | OAuth 2.0   | OAUTH_GITHUB_CLIENT_ID/SECRET | ✅ 已实现 |
| Google   | OAuth 2.0   | OAUTH_GOOGLE_CLIENT_ID/SECRET | ✅ 已实现 |
| 微信       | OAuth 2.0   | OAUTH_WECHAT_CLIENT_ID/SECRET | ✅ 已实现 |

**OAuth 流程：**

```
GET /api/oauth/auth-url?provider=github:
  1. 生成 CSRF state (UUID)
  2. state 存入 Redis → expire=600s
  3. 拼接授权 URL（含 client_id, redirect_uri, scope, state）
  4. 返回 { authUrl }

POST /api/oauth/callback:
  1. 验证 state（从 Redis 读取并对比，防 CSRF）
  2. 用 code 换取 access_token（httpx 调用 provider API）
  3. 用 access_token 获取用户信息（provider userinfo endpoint）
  4. 查询或创建用户（provider + openid 匹配）
  5. 签发 JWT Token 对 → 返回 AuthResponse
```

**OAuth 回调地址：** 前端页面 `/oauth/callback` → 解析 URL 参数 → 调用 `POST /api/oauth/callback`

### 4.9 SMS API — 短信服务模块（已实现）

**文件：** `api/sms/sms_api.py`、`service.py`

**路由前缀：** `/api/sms`
**v1.2.1 开发模式：** 未配置 `SMS_PROVIDER` 时，验证码仅记录日志并返回 `{"devCode": "6位数字"}` 到响应体，方便前端开发调试。

#### 数据模型

```python
class SendSmsRequest(BaseModel):
    phone: str = Field(pattern=r'^1[3-9]\d{9}$')
    captchaTicket: str       # 来自滑动验证码的 ticket
    captchaRandstr: str      # 来自滑动验证码的 randstr
```

#### API 接口

| 接口           | 方法   | 请求体            | 响应体                | 说明             |
| ------------ | ---- | -------------- | ------------------ | -------------- |
| `/api/sms/send` | POST | `SendSmsRequest` | `ApiResponse[None]` | 发送短信验证码（需先过滑动验证） |

#### 业务逻辑 — `api/sms/service.py`

```
POST /api/sms/send:
  1. 验证 captchaTicket + captchaRandstr（Redis 中查找，防机器调用）
  2. 检查当日发送次数 < SMS_DAILY_LIMIT (5)
  3. 生成 6 位随机数字验证码
  4. 调用短信服务商 API（阿里云/腾讯云）发送
  5. 验证码存入 Redis: key=sms:{phone} → {code, expires=300s}
  6. 递增当日发送计数器
  7. 删除已使用的 captcha ticket
```

---

## 5. 数据存储设计

### 5.1 SQLite / PostgreSQL — 持久化数据

#### User 模型 — `db/models/user.py`

```python
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    nickname: Mapped[str] = mapped_column(String(64), default="")
    password_hash: Mapped[str] = mapped_column(String(128), nullable=True)  # 手机号用户可为空
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=True)
    avatar: Mapped[str] = mapped_column(String(256), default="")
    workspace_id: Mapped[str] = mapped_column(String(36), default="default")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### OAuth 关联 — `db/models/user_oauth.py`

```python
class UserOAuth(Base):
    __tablename__ = "user_oauths"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)   # github/google/wechat/qq/weibo
    open_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("provider", "open_id", name="uq_oauth_provider_openid"),
    )
```

#### 登录记录 — `db/models/login_record.py`

```python
class LoginRecord(Base):
    __tablename__ = "login_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip: Mapped[str] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### 5.2 KeyValueStore — 临时数据（v1.2.1 核心基础组件）

`core/store.py` 定义了 `KeyValueStore` 抽象基类，提供统一的键值存储接口。使用策略模式实现了两种后端：

- **RedisStore**：Redis 可用时自动启用（连接 `REDIS_URL`）
- **MemoryStore**：Redis 不可用时自动降级为线程安全的内存存储（基于 `threading.Lock` + 惰性 TTL 淘汰）

这种设计确保开发环境无需安装 Redis 即可运行全部功能。

| 方法        | 说明             |
| --------- | -------------- |
| `get(key)` | 获取值（过期自动返回 None） |
| `set(key, value, ttl)` | 设置值 + TTL（秒）    |
| `delete(key)` | 删除键            |
| `exists(key)`   | 检查键是否存在        |
| `incr(key)` | 自增计数器          |

**Key 命名规范与用途：**

| Key 模式                    | 内容              | TTL | 用途              |
| ------------------------- | --------------- | --- | --------------- |
| `captcha:slide:{session}` | `{gap_x}:{y}`    | 300s | 滑动拼图缺口坐标       |
| `captcha:ticket:{ticket}` | `{randstr}`    | 300s | 滑动验证通过票据       |
| `captcha:image:{key}`     | `{code}`        | 300s | 图形验证码正确答案      |
| `sms:{phone}`             | `{code}`        | 300s | 短信验证码          |
| `email:{email}`           | `{code}`        | 300s | 邮箱验证码          |
| `sms:daily:{phone}:{date}`| `{count}`       | 86400s | 短信日发送计数        |
| `oauth:state:{state}`     | `{provider}`    | 600s | OAuth CSRF state |
| `login:fail:{account}`    | `{count}:{until_ts}` | 1800s | 登录失败次数与锁定时间   |

---

## 6. 安全设计

### 6.1 密码安全

```
前端：RSA 公钥加密 → 密文传输 → 后端：RSA 私钥解密 → bcrypt 哈希存储

流程：
  1. 前端 GET /api/auth/public-key → 获取 PEM 格式 RSA 公钥（SubjectPublicKeyInfo）
  2. 前端 JSEncrypt 加密密码
  3. POST 请求体 Base64 传输密文
  4. 后端 cryptography 库 RSA 私钥解密（PKCS1v15 padding）
  5. 后端 bcrypt 哈希后存入数据库
```

```python
# core/security.py
import bcrypt
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

# RSA 密钥对惰性生成（首次使用时触发）
_private_key: rsa.RSAPrivateKey | None = None

def _ensure_keys():
    if _private_key is None:
        _private_key = rsa.generate_private_key(65537, settings.RSA_KEY_SIZE)
        _public_key = _private_key.public_key()

def get_public_key() -> str:     # PEM SubjectPublicKeyInfo
def decrypt_password(encrypted_b64: str) -> str:  # Base64 → PKCS1v15 解密

# bcrypt 哈希
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

### 6.2 JWT Token 双 Token 机制

| Token 类型    | 有效期     | 用途              | 刷新策略          |
| ---------- | ------- | --------------- | ------------- |
| Access Token  | 2 小时    | 请求鉴权（Bearer 头）   | 过期后用 Refresh 换 |
| Refresh Token | 7 天     | 换取新 Access Token | 前端存储，过期需重新登录  |

### 6.3 登录安全

- **失败锁定**：同一 account 连续失败 5 次 → 锁定 30 分钟
- **密码不进日志**：日志中间件过滤请求体中的 password 字段
- **验证码前置**：登录/注册前需通过滑动拼图验证码，防止机器暴力破解
- **短信限流**：同一手机号每日最多 5 条，Redis 计数器

### 6.4 请求安全

- CORS 白名单（生产环境限制 allow_origins）
- Authorization Bearer 头校验
- 请求体大小限制（FastAPI 默认即可）
- rate limit 中间件（生产环境推荐 slowapi）

---

## 7. API 接口总览与前后端对照

### 7.1 完整接口清单

| 接口                            | 方法   | 模块      | 后端实现 | 前端调用                        |
| ----------------------------- | ---- | ------- | ---- | --------------------------- |
| `/api/chat`                   | POST | agent   | ✅ 已实现 | sendChatRequest (降级)        |
| `/api/chat/stream`            | POST | agent   | ✅ 已实现 | sendStreamRequest           |
| `/api/auth/public-key`        | GET  | auth    | ✅ 已实现 | authApi.getPublicKey        |
| `/api/auth/login/account`     | POST | auth    | ✅ 已实现 | authApi.accountLogin        |
| `/api/auth/login/phone`       | POST | auth    | ✅ 已实现 | authApi.phoneLogin          |
| `/api/auth/register/phone`    | POST | auth    | ✅ 已实现 | authApi.register            |
| `/api/auth/register/email`    | POST | auth    | ✅ 已实现 | authApi.emailRegister        |
| `/api/auth/logout`            | POST | auth    | ✅ 已实现 | authApi.logout              |
| `/api/auth/refresh`           | POST | auth    | ✅ 已实现 | authApi.refreshToken        |
| `/api/auth/fail-count`        | GET  | auth    | ✅ 已实现 | authApi.getFailCount        |
| `/api/captcha/slide`          | GET  | captcha | ✅ 已实现 | captchaApi.getSlidePuzzle   |
| `/api/captcha/slide/verify`   | POST | captcha | ✅ 已实现 | captchaApi.verifySlide      |
| `/api/captcha/image`          | GET  | captcha | ✅ 已实现 | captchaApi.getImageCaptcha  |
| `/api/captcha/image/verify`   | POST | captcha | ✅ 已实现 | captchaApi.verifyImageCaptcha |
| `/api/sms/send`               | POST | sms     | ✅ 已实现 | captchaApi.sendSms          |
| `/api/oauth/auth-url`         | GET  | oauth   | ✅ 已实现 | oauthApi.getAuthUrl         |
| `/api/oauth/callback`         | POST | oauth   | ✅ 已实现 | oauthApi.handleCallback     |

### 7.2 统一响应格式

所有接口使用统一响应包装（与前端 `ApiResponse<T>` 类型对应）：

```python
# core/response.py
from pydantic import BaseModel
from typing import Generic, TypeVar
import time, uuid

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    data: T | None = None
    message: str = "ok"
    requestId: str = ""
    timestamp: int = 0

def ok(data: T = None, message: str = "ok") -> ApiResponse[T]:
    return ApiResponse(
        code=0,
        data=data,
        message=message,
        requestId=str(uuid.uuid4()),
        timestamp=int(time.time()),
    )

def error(code: int, message: str) -> ApiResponse[None]:
    return ApiResponse(
        code=code,
        data=None,
        message=message,
        requestId=str(uuid.uuid4()),
        timestamp=int(time.time()),
    )
```

---

## 8. 数据流

### 8.1 普通对话

```
前端 POST /api/chat {"message": "用户输入"}
    ↓
agent_api.py → ChatRequest 校验 (min_length=1)
    ↓
graph.ainvoke({"messages": [HumanMessage(content="用户输入")]})
    ↓
deepagents 执行智能体图 → ChatOpenAI(DeepSeek) 生成回复
    ↓
取 result["messages"][-1].content → AIMessage
    ↓
ChatResponse {"response": "智能体回复"}
    ↓
前端接收 JSON 响应
```

### 8.2 流式对话

```
前端 POST /api/chat/stream {"message": "用户输入"}
    ↓
agent_api.py → ChatRequest 校验
    ↓
graph.astream_events({"messages": [HumanMessage(...)]}, version="v2")
    ↓
deepagents 逐事件执行 → on_chat_model_stream 事件
    ↓
提取 token → SSE: data: {"token": "..."}\n\n
    ↓
StreamingResponse(media_type="text/event-stream") 逐条推送
    ↓
前端 fetch + ReadableStream 解析 SSE token 流
```

### 8.3 账号密码登录

```
前端:
  1. GET /api/auth/public-key → 获取 RSA 公钥
  2. JSEncrypt 加密密码
  3. POST /api/auth/login/account { account, password(密文), captchaTicket?, captchaRandstr? }

后端:
  1. auth_api.py → AccountLoginRequest 校验
  2. auth/service.py:
     a. 从 KeyValueStore 查询 login:fail:{account} → 检查是否锁定
     b. RSA 私钥解密 password
     c. 数据库查询用户（username/phone/email 匹配）
     d. bcrypt 验证密码
     e. 成功 → 清除失败计数, 签发 JWT, 插入登录记录
     f. 失败 → 递增失败计数, 判断是否锁定
  3. 返回 AuthResponse { tokens: {accessToken, refreshToken}, user: {...} }
```

### 8.4 模块依赖关系（v1.2.1 全图）

```
server.py
  ├── load_dotenv()           ← 加载 .env
  ├── CORS 中间件
  ├── lifespan:
  │     ├── init_db()         ← 自动建表
  │     ├── create_store()    ← Redis / MemoryStore
  │     └── init_jwt()        ← JWT 密钥持久化
  └── api.router
        ├── agent_api.router (prefix="/api")
        │     └── agent.graph
        │           └── agent.models (llm + embeddings)
        │                 └── agent.config.settings
        ├── auth_api.router (prefix="/api/auth")
        │     ├── auth/service.py
        │     │     ├── core/security.py (RSA, JWT, bcrypt)
        │     │     ├── db/models/user.py → SQLAlchemy
        │     │     └── api.deps → core/store.py (KeyValueStore)
        │     └── api.deps (get_db, get_store, get_client_ip)
        ├── captcha_api.router (prefix="/api/captcha")
        │     ├── captcha/service.py
        │     │     ├── Pillow (图形生成)
        │     │     └── api.deps → core/store.py (KeyValueStore)
        │     └── Session Cookie (captcha_session)
        ├── oauth_api.router (prefix="/api/oauth")
        │     └── oauth/service.py
        │           ├── httpx (第三方 API 调用)
        │           ├── db/models/user.py + user_oauth.py → SQLAlchemy
        │           └── api.deps → core/store.py (KeyValueStore)
        └── sms_api.router (prefix="/api/sms")
              └── sms/service.py
                    ├── api.deps → core/store.py (KeyValueStore)
                    └── 短信服务商 SDK（可选）
```

---

## 9. 环境变量设计

所有配置通过 `.env` 文件管理，`python-dotenv` 在应用启动时加载。

| 变量名                          | 类型   | 默认值                                            | 说明                   |
| ---------------------------- | ---- | ---------------------------------------------- | -------------------- |
| `DEEPSEEK_API_KEY`           | str  | `""`                                           | DeepSeek API 密钥（必填）  |
| `DEEPSEEK_MODEL`             | str  | `"deepseek-v4-pro"`                            | LLM 模型名称             |
| `DEEPSEEK_BASE_URL`          | str  | `"https://api.deepseek.com/v1"`                | DeepSeek API 地址      |
| `DASHSCOPE_API_KEY`          | str  | `""`                                           | DashScope API 密钥     |
| `DASHSCOPE_EMBEDDING`        | str  | `"text-embedding-v4"`                          | 向量模型名称              |
| `DASHSCOPE_BASE_URL`         | str  | `"https://dashscope.aliyuncs.com/compatible-mode/v1"` | DashScope 兼容地址 |
| `HOST`                       | str  | `"127.0.0.1"`                                  | 服务监听地址              |
| `PORT`                       | int  | `8000`                                         | 服务监听端口              |
| `DATABASE_URL`               | str  | `"sqlite+aiosqlite:///./db/ke-hermes.db"`      | 数据库连接字符串（相对路径，文件位于 db/ 目录） |
| `JWT_SECRET_KEY`             | str  | `""`                                           | JWT 签名密钥（缺省自动生成 RSA） |
| `JWT_ACCESS_EXPIRE`          | int  | `7200`                                         | Access Token 有效期（秒）  |
| `JWT_REFRESH_EXPIRE`         | int  | `604800`                                       | Refresh Token 有效期（秒） |
| `RSA_KEY_SIZE`               | int  | `2048`                                         | RSA 密钥长度             |
| `LOGIN_MAX_FAILS`            | int  | `5`                                            | 登录失败锁定阈值            |
| `LOGIN_LOCK_MINUTES`         | int  | `30`                                           | 锁定时间（分钟）            |
| `SMS_DAILY_LIMIT`            | int  | `5`                                            | 短信每日上限              |
| `CAPTCHA_EXPIRE`             | int  | `300`                                          | 验证码过期时间（秒）          |
| `SLIDE_THRESHOLD`            | int  | `5`                                            | 滑动验证容差（像素）          |
| `REDIS_URL`                  | str  | `"redis://127.0.0.1:6379/0"`                   | Redis 连接地址           |
| `OAUTH_GITHUB_CLIENT_ID`     | str  | `""`                                           | GitHub OAuth Client ID   |
| `OAUTH_GITHUB_CLIENT_SECRET` | str  | `""`                                           | GitHub OAuth Secret     |
| `OAUTH_GOOGLE_CLIENT_ID`     | str  | `""`                                           | Google OAuth Client ID   |
| `OAUTH_GOOGLE_CLIENT_SECRET` | str  | `""`                                           | Google OAuth Secret     |
| `OAUTH_WECHAT_CLIENT_ID`     | str  | `""`                                           | 微信 OAuth Client ID     |
| `OAUTH_WECHAT_CLIENT_SECRET` | str  | `""`                                           | 微信 OAuth Secret       |
| `SMS_PROVIDER`               | str  | `""`                                           | 短信服务商 (aliyun/tencent)     |
| `SMS_ACCESS_KEY`             | str  | `""`                                           | 短信服务商 Access Key     |
| `SMS_SECRET_KEY`             | str  | `""`                                           | 短信服务商 Secret Key     |
| `SMS_SIGN_NAME`              | str  | `""`                                           | 短信签名                |
| `SMS_TEMPLATE_CODE`          | str  | `""`                                           | 短信模板编号              |

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

所有接口返回统一的 `ApiResponse<T>` 包装，确保前端可以通过同一拦截器处理。字段设计对齐前端 `ApiResponse<T>` 类型定义：`code`（0=成功）、`data`（泛型）、`message`（提示信息）、`requestId`（链路追踪）、`timestamp`（服务端时间戳）。

### 10.6 可编辑模式安装

项目通过 `uv pip install -e .` 以可编辑模式安装到虚拟环境，`pyproject.toml` 中 `[tool.setuptools.packages.find] where = ["src"]` 确保包发现路径指向 `src/`。

### 10.7 SQLite 开发 + PostgreSQL 生产

开发环境使用 SQLite（零配置，文件位于 `db/ke-hermes.db`），生产环境切换 PostgreSQL（通过 `DATABASE_URL` 环境变量配置）。SQLAlchemy 抽象了数据库差异，模型代码无需修改。

### 10.8 RSA 前端加密 + bcrypt 后端存储

密码传输使用 RSA 非对称加密（前端 JSEncrypt 公钥加密，后端 `cryptography` 库私钥解密），存储使用 `bcrypt` 库单向哈希。即使传输层被截获，攻击者也无法获得明文密码；即使数据库泄露，bcrypt 哈希也难以反向破解。

### 10.9 KeyValueStore 抽象层（v1.2.1 新增）

所有临时数据（验证码、短信码、OAuth state、登录失败计数）通过 `KeyValueStore` 抽象接口操作，不直接依赖 Redis。当 Redis 不可用时自动降级为线程安全的 `MemoryStore`，实现零依赖开发环境。通过 `create_store()` 工厂函数自动检测并选择后端，业务代码无需感知底层存储实现。

### 10.10 JWT 密钥持久化（v1.2.1 新增）

JWT 签名密钥在首次启动时自动生成并持久化到项目根目录 `.jwt_secret` 文件。后续重启从文件读取，确保已签发的 Token 在服务重启后仍然有效。也可通过 `JWT_SECRET_KEY` 环境变量显式指定密钥。

---

## 11. 测试设计

### 11.1 测试分层

```
tests/
├── conftest.py                 # [扩展] 添加 async test client, test db, redis mock
├── unit_tests/
│   ├── test_config.py          # Settings 类环境变量读取
│   ├── test_models.py          # LLM/Embeddings 实例导入
│   ├── test_agent.py           # graph 导出与基础调用
│   ├── test_security.py        # [新增] RSA 加解密、bcrypt 哈希、JWT 签发/验证
│   └── test_auth_service.py    # [新增] 登录逻辑、失败锁定、token 刷新
└── integration_tests/
    ├── test_server.py          # 服务启动测试
    ├── test_agent_api.py       # Chat API（/chat, /chat/stream）
    ├── test_auth_api.py        # [新增] Auth API 全接口
    ├── test_captcha_api.py     # [新增] Captcha API 全接口
    └── test_oauth_api.py       # [新增] OAuth API 全接口
```

### 11.2 关键测试用例设计

| 模块              | 用例数 | 覆盖要点                                        |
| --------------- | --- | ------------------------------------------- |
| test_security   | 6   | RSA 密钥生成、加密解密循环、密码哈希与校验、JWT 签发、JWT 验证、过期 Token 拒绝 |
| test_auth_service | 8   | 账号登录成功、密码错误、用户不存在、失败计数递增、5次锁定、锁定后拒绝、Token 刷新、登出 |
| test_auth_api   | 6   | POST /login/account 200、400/401、GET /public-key 200、POST /refresh、GET /fail-count |
| test_captcha_api | 4   | GET /slide 返回图片、POST /slide/verify 成功/失败、GET /image 返回验证码 |
| test_agent_api   | 4   | POST /chat 200、空 message 422、POST /chat/stream SSE、流式 token 完整性 |

### 11.3 测试配置

```python
# conftest.py — v1.2.0 扩展
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.server import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture
def redis_mock():
    # fakeredis 或 unittest.mock
    ...

@pytest.fixture
def test_db():
    # SQLite in-memory for testing
    ...
```

### 11.4 执行命令

```bash
pytest tests/ -v                    # 运行全部测试
pytest tests/unit_tests/ -v         # 仅单元测试
pytest tests/integration_tests/ -v  # 仅集成测试
pytest --cov=src tests/             # 覆盖率报告
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
# 编辑 .env，填写 DEEPSEEK_API_KEY

# 3. 启动 Redis（验证码/OAuth 需要）
redis-server                      # 或 docker run -d -p 6379:6379 redis

# 4. 启动服务
uvicorn src.server:app --host 127.0.0.1 --port 8000
```

### 12.2 前置条件

1. Python >= 3.11
2. 虚拟环境已创建并安装依赖
3. `.env` 文件已配置 `DEEPSEEK_API_KEY`
4. Redis 服务（可选 — 不可用时自动降级为内存存储）
5. SQLite 数据库文件（自动创建于 `db/ke-hermes.db`）

### 12.3 API 文档

启动后访问 `http://127.0.0.1:8000/docs`，FastAPI 自动生成交互式 Swagger UI 文档。auth/captcha/oauth/sms/agent 五个模块共 17 个接口均自动注册。

---

## 13. 前后端实施差异与待实现项

### 13.1 前后端功能对照（v1.2.1）

| 功能模块      | 前端 v1.2.1 | 后端 v1.2.1 | 差异                                |
| --------- | -------- | -------- | --------------------------------- |
| 智能体对话 (普通) | ✅ 已实现    | ✅ 已实现    | **一致**（前端 sendChatRequest 降级方案） |
| 智能体对话 (流式) | ✅ 已实现    | ✅ 已实现    | **一致**                           |
| 账号密码登录     | ✅ 已实现    | ✅ 已实现    | **一致**                           |
| 手机验证码登录    | ✅ 已实现    | ✅ 已实现    | **一致**                           |
| 手机号注册      | ✅ 已实现    | ✅ 已实现    | **一致**                           |
| 邮箱注册       | ✅ 已实现    | ✅ 已实现    | **一致**（EmailRegisterForm 提交为 TODO） |
| 滑动拼图验证码    | ✅ 已实现    | ✅ 已实现    | **一致**（后端使用 Session Cookie 关联） |
| 图形验证码      | ✅ 已实现    | ✅ 已实现    | **一致**                           |
| 短信发送       | ✅ 已实现    | ✅ 已实现    | **一致**（开发模式返回 devCode） |
| OAuth 登录   | ✅ 已实现    | ✅ 已实现    | **一致**（GitHub/Google/微信） |
| Token 管理   | ✅ 已实现    | ✅ 已实现    | **一致**（双 Token + 自动刷新 + 去重锁） |
| RSA 加密     | ✅ 已实现    | ✅ 已实现    | **一致**（前端 JSEncrypt / 后端 cryptography） |
| 模型切换       | ⬜ 已设计    | ⬜        | 前端 ChatHeader 模型选择器已实现下拉，后端无模型列表 API |
| 对话历史 CRUD  | ⬜ 已设计    | ⬜        | 前端 RightPanel 硬编码历史，后端无对话历史 API    |
| 用户管理       | ⬜        | ⬜        | 前端无管理界面，后端无管理 API                |

### 13.2 待实现项

| 优先级 | 模块          | 接口数 | 说明                    |
| --- | ----------- | --- | --------------------- |
| P2  | 模型列表 API    | 1   | 模型列表查询，对接前端 ChatHeader 模型选择器 |
| P2  | 对话历史 CRUD   | 4+  | 对话历史持久化，对接前端 RightPanel |
| P2  | 通知系统        | 2+  | 对接前端 TopBar 通知铃铛按钮 |
| P3  | 用户管理 API    | 4+  | 用户信息编辑、头像上传、密码修改 |
| P3  | 邮件发送服务     | 1   | 邮箱验证码实际发送（当前仅开发模式） |

### 13.3 从 v1.0.0 到 v1.2.1 的变更总结

| 项目       | v1.0.0 (初始) | v1.2.1 (当前)     |
| -------- | ----------- | ------------------ |
| API 模块   | 1 (agent)   | 5 (agent + auth + captcha + oauth + sms) |
| 数据模型     | 0           | 3 (User + UserOAuth + LoginRecord) |
| 中间件      | 0           | CORS + 依赖注入体系（get_db/get_store/get_client_ip） |
| 安全       | 无           | RSA( cryptography) + JWT(PyJWT + 自动持久化) + bcrypt + 登录锁定 |
| 存储抽象     | 无           | KeyValueStore（Redis + MemoryStore 自动降级） |
| 外部依赖     | DeepSeek + DashScope | + bcrypt + cryptography + httpx + Pillow + redis(可选) |
| 环境变量     | 8           | 28             |
| API 接口    | 2           | 17             |

---

> 本文档 v1.2.1 基于实际代码实现更新。v1.2.0 设计的全部模块（auth/captcha/oauth/sms）已完成编码并通过功能验证。KeyValueStore 存储抽象层使开发环境无需 Redis 即可运行全部功能。后续版本应优先实现对话历史 CRUD 和模型列表 API。
