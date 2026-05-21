# Ke-Hermes 数据库详细设计说明书

**版本**: 1.0.0
**日期**: 2026-05-21
**状态**: 已发布

---

## 目录

1. [概述](#1-概述)
2. [存储架构](#2-存储架构)
3. [关系型数据库设计](#3-关系型数据库设计)
   - [3.1 数据库引擎](#31-数据库引擎)
   - [3.2 用户表 users](#32-用户表-users)
   - [3.3 OAuth 关联表 user_oauths](#33-oauth-关联表-user_oauths)
   - [3.4 登录记录表 login_records](#34-登录记录表-login_records)
   - [3.5 LangGraph 检查点表](#35-langgraph-检查点表)
       - [3.5.1 概述](#351-概述)
       - [3.5.2 检查点表 checkpoints](#352-检查点表-checkpoints)
       - [3.5.3 通道写入表 writes](#353-通道写入表-writes)
       - [3.5.4 数据流](#354-数据流)
   - [3.6 ER 图](#36-er-图)
4. [键值存储设计](#4-键值存储设计)
   - [4.1 架构概述](#41-架构概述)
   - [4.2 键空间设计](#42-键空间设计)
   - [4.3 数据生命周期](#43-数据生命周期)
5. [安全模型](#5-安全模型)
   - [5.1 密码安全](#51-密码安全)
   - [5.2 身份认证与令牌](#52-身份认证与令牌)
   - [5.3 登录风控](#53-登录风控)
6. [数据流与 API 映射](#6-数据流与-api-映射)
   - [6.1 认证相关](#61-认证相关)
   - [6.2 OAuth 第三方登录](#62-oauth-第三方登录)
   - [6.3 智能体对话](#63-智能体对话)
7. [配置与部署](#7-配置与部署)
   - [7.1 环境变量](#71-环境变量)
   - [7.2 初始化流程](#72-初始化流程)

---

## 1. 概述

Ke-Hermes 是一个通用智能体服务平台，采用前后端分离架构。后端基于 **Python FastAPI**，使用 **SQLAlchemy 2.0 异步 ORM** 管理持久化数据，辅以 **Redis/内存键值存储** 管理临时状态。

### 设计原则

| 原则 | 说明 |
|------|------|
| **持久化与临时分离** | 用户、OAuth 绑定等长期数据使用 SQLite 持久存储；验证码、限流计数器等短期数据使用 Key-Value 存储（Redis / 内存回退） |
| **UUID 主键** | 所有业务表主键使用 UUID v4 字符串（36 字符），避免自增 ID 的序列暴露和分布式扩展问题 |
| **异步优先** | 数据库引擎、会话、ORM 操作全程异步（`aiosqlite` + `sqlalchemy[asyncio]`） |
| **密码零明文** | 密码经 RSA 加密传输，服务端 bcrypt 哈希后存储，永不以明文形式落盘 |
| **无外键约束** | SQLite 默认不强制外键，通过应用层逻辑保证引用完整性 |

---

## 2. 存储架构

```
┌─────────────────────────────────────────────────────────┐
│                    Ke-Hermes 后端                        │
├─────────────────────────────────────────────────────────┤
│  FastAPI 应用层                                          │
│  ├── api/auth/     认证服务                              │
│  ├── api/oauth/    OAuth 服务                            │
│  ├── api/agent/    智能体对话服务                         │
│  ├── api/sms/      短信服务                              │
│  └── api/captcha/  验证码服务                            │
├─────────────────────────────────────────────────────────┤
│  数据访问层                                              │
│  ┌─────────────────────────┬──────────────────────────┐ │
│  │ SQLAlchemy ORM (异步)    │ KeyValueStore (抽象接口)  │ │
│  │ ─────────────────────── │ ──────────────────────── │ │
│  │ • User                  │ • get/set/delete/exists  │ │
│  │ • UserOAuth             │ • incr (原子递增)         │ │
│  │ • LoginRecord           │ • ttl (过期时间)          │ │
│  └───────────┬─────────────┴────────────┬─────────────┘ │
│              │                          │               │
├──────────────┼──────────────────────────┼───────────────┤
│  存储层       │                          │               │
│  ┌───────────▼──────────┐  ┌────────────▼─────────────┐ │
│  │ SQLite (aiosqlite)   │  │ Redis (主) / Memory (回退) │ │
│  │ ──────────────────── │  │ ───────────────────────── │ │
│  │ ke-hermes.db         │  │ • 验证码 session           │ │
│  │ • users              │  │ • SMS/邮件 验证码          │ │
│  │ • user_oauths        │  │ • 登录失败计数器           │ │
│  │ • login_records      │  │ • OAuth state token       │ │
│  │                       │  │ • 每日短信限额             │ │
│  ├───────────────────────┤  └──────────────────────────┘ │
│  │ langgraph_checkpoints │                               │
│  │ .sqlite (独立 DB)      │                               │
│  │ • Agent 对话检查点     │                               │
│  └───────────────────────┘                               │
└─────────────────────────────────────────────────────────┘
```

**双存储设计原因**：

| 数据类型 | 存储 | 原因 |
|----------|------|------|
| 用户信息、OAuth 绑定、登录日志 | SQLite | 需持久化、支持复杂查询、关联查询 |
| 验证码、限流计数、OAuth state | Redis/Memory | 短期有效、自动过期、高频读写 |
| Agent 对话检查点 | SQLite（独立文件） | LangGraph 框架管理，与业务库隔离 |

---

## 3. 关系型数据库设计

### 3.1 数据库引擎

```python
# 来源: backend/src/db/engine.py

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

async_engine = create_async_engine(
    "sqlite+aiosqlite:///./db/ke-hermes.db",
    echo=False
)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)
```

| 属性 | 值 |
|------|-----|
| 数据库类型 | SQLite 3 |
| 异步驱动 | aiosqlite |
| 数据库文件 | `./db/ke-hermes.db` |
| 连接字符串 | 通过 `DATABASE_URL` 环境变量配置 |
| ORM 基类 | `sqlalchemy.orm.DeclarativeBase` |
| 表创建方式 | `Base.metadata.create_all`（启动时自动建表） |
| Session 工厂 | `async_sessionmaker(expire_on_commit=False)` |

**会话管理**（依赖注入模式）：

```python
# 来源: backend/src/db/engine.py
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

每个 HTTP 请求通过 FastAPI `Depends(get_db)` 获取独立会话，请求成功自动提交，异常自动回滚。

### 3.2 用户表 users

**表名**: `users`
**模型文件**: `backend/src/db/models/user.py`

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | String(36) | PRIMARY KEY | `uuid4()` | 用户唯一标识 |
| `username` | String(64) | UNIQUE, NULLABLE | — | 用户名（账号密码登录用） |
| `nickname` | String(64) | — | `""` | 用户昵称/显示名 |
| `password_hash` | String(128) | NULLABLE | — | bcrypt 密码哈希 |
| `phone` | String(20) | UNIQUE, NULLABLE | — | 手机号 |
| `email` | String(128) | UNIQUE, NULLABLE | — | 邮箱地址 |
| `avatar` | String(256) | — | `""` | 头像 URL |
| `workspace_id` | String(36) | — | `"default"` | 工作空间 ID（预留多租户） |
| `is_active` | Boolean | — | `True` | 账号启用状态 |
| `created_at` | DateTime | — | `func.now()` | 创建时间 |
| `updated_at` | DateTime | ON UPDATE | `func.now()` | 最后更新时间 |

**建表 DDL**（由 SQLAlchemy 生成）：

```sql
CREATE TABLE users (
    id           VARCHAR(36)  PRIMARY KEY,
    username     VARCHAR(64)  UNIQUE,
    nickname     VARCHAR(64)  DEFAULT '',
    password_hash VARCHAR(128),
    phone        VARCHAR(20)  UNIQUE,
    email        VARCHAR(128) UNIQUE,
    avatar       VARCHAR(256) DEFAULT '',
    workspace_id VARCHAR(36)  DEFAULT 'default',
    is_active    BOOLEAN      DEFAULT TRUE,
    created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     DEFAULT CURRENT_TIMESTAMP
);
```

**设计要点**：

1. **多登录方式共存**: `username`、`phone`、`email` 均为可空且唯一，支持账号密码、手机号、邮箱三种方式登录，同一字段 `account` 可匹配任一标识。
2. **密码哈希可空**: OAuth 第三方登录创建的用户无密码，`password_hash` 为 NULL，后续可绑定密码。
3. **UUID 主键**: 避免自增 ID 在分布式场景的冲突问题，同时防止用户数泄露。
4. **workspace_id**: 预留多租户/多工作空间扩展能力，当前固定为 `"default"`。

**用户创建场景**：

| 场景 | 必填字段 | 说明 |
|------|----------|------|
| 手机号注册 | `phone`, `nickname`, `password_hash` | 需验证短信验证码 |
| 邮箱注册 | `email`, `nickname`, `password_hash` | 需验证邮箱验证码 |
| 手机号快捷登录 | `phone` | 无密码，首次登录自动创建 |
| OAuth 第三方登录 | `nickname`, `avatar`, `email` | 无密码，通过 `user_oauths` 关联 |

### 3.3 OAuth 关联表 user_oauths

**表名**: `user_oauths`
**模型文件**: `backend/src/db/models/user_oauth.py`

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | String(36) | PRIMARY KEY | `uuid4()` | 记录唯一标识 |
| `user_id` | String(36) | FOREIGN KEY → users.id, NOT NULL | — | 关联用户 |
| `provider` | String(20) | NOT NULL | — | OAuth 提供商 |
| `open_id` | String(128) | NOT NULL | — | 第三方平台的用户标识 |
| `created_at` | DateTime | — | `func.now()` | 绑定时间 |

**建表 DDL**：

```sql
CREATE TABLE user_oauths (
    id         VARCHAR(36)  PRIMARY KEY,
    user_id    VARCHAR(36)  NOT NULL REFERENCES users(id),
    provider   VARCHAR(20)  NOT NULL,
    open_id    VARCHAR(128) NOT NULL,
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_oauth_provider_openid UNIQUE (provider, open_id)
);
```

**支持的 OAuth 提供商**：

| provider | 说明 | 配置项 |
|----------|------|--------|
| `github` | GitHub OAuth App | `OAUTH_GITHUB_CLIENT_ID` / `OAUTH_GITHUB_CLIENT_SECRET` |
| `google` | Google OAuth 2.0 | `OAUTH_GOOGLE_CLIENT_ID` / `OAUTH_GOOGLE_CLIENT_SECRET` |
| `wechat` | 微信开放平台 | `OAUTH_WECHAT_CLIENT_ID` / `OAUTH_WECHAT_CLIENT_SECRET` |

**唯一约束** (`provider`, `open_id`) 确保同一第三方账号只能绑定一个 Ke-Hermes 用户。

**绑定流程**：
1. 根据 `provider + open_id` 查询 `user_oauths` 表
2. 若存在记录 → 直接登录对应用户
3. 若不存在 → 创建新 `User` + 插入 `UserOAuth` 记录

### 3.4 登录记录表 login_records

**表名**: `login_records`
**模型文件**: `backend/src/db/models/login_record.py`

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | String(36) | PRIMARY KEY | `uuid4()` | 记录唯一标识 |
| `account` | String(128) | NOT NULL, INDEX | — | 登录账号（用户名/手机/邮箱） |
| `success` | Boolean | NOT NULL | — | 是否登录成功 |
| `ip` | String(45) | NULLABLE | — | 客户端 IP（支持 IPv6） |
| `created_at` | DateTime | — | `func.now()` | 记录时间 |

**建表 DDL**：

```sql
CREATE TABLE login_records (
    id         VARCHAR(36)  PRIMARY KEY,
    account    VARCHAR(128) NOT NULL,
    success    BOOLEAN      NOT NULL,
    ip         VARCHAR(45),
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_login_records_account ON login_records (account);
```

**设计要点**：

- **审计日志**: 记录所有登录尝试（成功/失败），用于事后安全审计
- **IP 追踪**: `ip` 字段支持 IPv6（最长 45 字符），通过 `X-Forwarded-For` 头获取真实 IP
- **按账号索引**: `account` 字段建索引，支持按账号查询登录历史

### 3.5 LangGraph 检查点表

LangGraph 框架使用独立的 SQLite 数据库存储 Agent 对话检查点（短期记忆），由 `langgraph-checkpoint-sqlite` 库的 `AsyncSqliteSaver` 自动管理表结构。该数据库包含 2 张表：`checkpoints`（检查点快照）和 `writes`（通道写入记录）。

#### 3.5.1 概述

| 属性 | 值 |
|------|-----|
| 数据库文件 | `./db/langgraph_checkpoints.db` |
| 配置项 | `CHECKPOINT_DB_PATH` 环境变量（默认 `./db/langgraph_checkpoints.db`） |
| Python 类 | `AsyncSqliteSaver` (from `langgraph.checkpoint.sqlite.aio`) |
| 驱动 | aiosqlite |
| 初始化 | `backend/src/agent/graph.py` → `init_graph()`，由 FastAPI lifespan 调用 |
| 序列化格式 | msgpack（`type` 字段标识） |

**与业务库隔离的原因**：
- LangGraph 的表结构和迁移周期独立于业务
- 避免与业务表的命名冲突
- 便于单独备份/清理对话历史而不影响用户数据

#### 3.5.2 检查点表 checkpoints

**表名**: `checkpoints`
**管理方**: `langgraph-checkpoint-sqlite` 库

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `thread_id` | TEXT | NOT NULL, PK | — | 对话线程唯一标识（对应 API 中的 `thread_id`） |
| `checkpoint_ns` | TEXT | NOT NULL, PK | `''` | 检查点命名空间（当前均为空字符串，预留多租户/子图隔离） |
| `checkpoint_id` | TEXT | NOT NULL, PK | — | 检查点唯一标识（UUID7，按时间有序） |
| `parent_checkpoint_id` | TEXT | NULLABLE | — | 父检查点 ID，形成对话历史链表；首个检查点为 NULL |
| `type` | TEXT | NULLABLE | — | 序列化格式标识（当前为 `msgpack`） |
| `checkpoint` | BLOB | — | — | 检查点状态快照（msgpack 序列化的 Agent 状态） |
| `metadata` | BLOB | — | — | 检查点元数据（msgpack 序列化，含 source、step、writes 等信息） |

**建表 DDL**（由 `langgraph-checkpoint-sqlite` 自动创建）：

```sql
CREATE TABLE checkpoints (
    thread_id         TEXT NOT NULL,
    checkpoint_ns     TEXT NOT NULL DEFAULT '',
    checkpoint_id     TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type              TEXT,
    checkpoint        BLOB,
    metadata          BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
```

**设计要点**：

1. **复合主键** (`thread_id`, `checkpoint_ns`, `checkpoint_id`): 支持多线程、多命名空间的检查点隔离存储。
2. **UUID7 排序**: `checkpoint_id` 使用 UUID7（时间戳前缀），天然按时间排序，便于 LangGraph 按序回溯对话历史。
3. **链表式历史链**: 通过 `parent_checkpoint_id` 串联同一线程的检查点，形成对话演化链条。首个检查点的 `parent_checkpoint_id` 为 NULL。
4. **BLOB 序列化**: `checkpoint` 和 `metadata` 以 msgpack 二进制格式存储，紧凑高效。`checkpoint` 字段包含 Agent 完整状态（消息历史、中间变量等）；`metadata` 包含来源（source）、步骤（step）、写入（writes）等元信息。

#### 3.5.3 通道写入表 writes

**表名**: `writes`
**管理方**: `langgraph-checkpoint-sqlite` 库

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `thread_id` | TEXT | NOT NULL, PK | — | 对话线程唯一标识 |
| `checkpoint_ns` | TEXT | NOT NULL, PK | `''` | 检查点命名空间 |
| `checkpoint_id` | TEXT | NOT NULL, PK | — | 关联的检查点 ID |
| `task_id` | TEXT | NOT NULL, PK | — | 引发此写入的任务/节点 ID |
| `idx` | INTEGER | NOT NULL, PK | — | 同一 task 内的写入序号（从 0 递增） |
| `channel` | TEXT | NOT NULL | — | 通道名称，标识写入目标 |
| `type` | TEXT | NULLABLE | — | 序列化格式（msgpack）或 NULL（表示空写入） |
| `value` | BLOB | — | — | 写入的通道数据（msgpack 序列化或 NULL） |

**建表 DDL**（由 `langgraph-checkpoint-sqlite` 自动创建）：

```sql
CREATE TABLE writes (
    thread_id       TEXT NOT NULL,
    checkpoint_ns   TEXT NOT NULL DEFAULT '',
    checkpoint_id   TEXT NOT NULL,
    task_id         TEXT NOT NULL,
    idx             INTEGER NOT NULL,
    channel         TEXT NOT NULL,
    type            TEXT,
    value           BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

**设计要点**：

1. **复合主键** (`thread_id`, `checkpoint_ns`, `checkpoint_id`, `task_id`, `idx`): 精确标识每个检查点中每个任务的每次通道写入。
2. **写入序号**: `idx` 自 0 递增，记录单个 task 内多次写入的先后顺序。
3. **通道类型**: `channel` 标识数据写入的目标通道，常见值：

   | channel | 说明 |
   |---------|------|
   | `messages` | 对话消息通道，存储 HumanMessage / AIMessage 等 |
   | `branch:to:model` | 发送给 LLM 模型节点的分支触发 |
   | `branch:to:PatchToolCallsMiddleware.before_agent` | DeepAgents 工具调用修复中间件触发 |
   | `branch:to:TodoListMiddleware.after_model` | DeepAgents 任务列表管理中间件触发 |
   | `__no_writes__` | 空通道（无实际写入，仅标记检查点创建） |

4. **与 checkpoints 的关系**: 每个检查点（`checkpoint_id`）可包含多个 task 写入记录，`writes` 表是 `checkpoints` 表的明细/子表，通过 (`thread_id`, `checkpoint_ns`, `checkpoint_id`) 关联。

#### 3.5.4 数据流

**Agent 对话的检查点写入流程**：

```
用户请求
  │
  ▼
POST /api/chat 或 /api/chat/stream
  │ thread_id = 前端提供或自动生成 UUID7
  ▼
graph.ainvoke / graph.astream_events
  │ {"messages": [HumanMessage], "configurable": {"thread_id": thread_id}}
  ▼
LangGraph Runtime
  │ 1. 执行 Agent 图节点（model → tools → model 循环）
  │ 2. 每步执行后自动写入 checkpoints 和 writes
  ▼
AsyncSqliteSaver
  │ INSERT INTO checkpoints ...  (保存状态快照)
  │ INSERT INTO writes ...       (保存通道写入)
  ▼
langgraph_checkpoints.db
```

**上下文恢复流程**：

```
用户请求（携带已有 thread_id）
  │
  ▼
graph.ainvoke(config={"configurable": {"thread_id": thread_id}})
  │
  ▼
AsyncSqliteSaver
  │ SELECT ... FROM checkpoints WHERE thread_id = ?
  │ ORDER BY checkpoint_id DESC LIMIT 1
  │ → 获取最新检查点
  │ → 反序列化 checkpoint BLOB
  │ → 恢复消息历史和 Agent 状态
  ▼
Agent 在已有上下文基础上继续对话
```

**API 映射**：

| API | 方法 | 说明 |
|-----|------|------|
| `/api/chat` | POST | 非流式对话，返回完整响应 + `thread_id` |
| `/api/chat/stream` | POST | SSE 流式对话，逐 Token 返回，结束时返回 `thread_id` |

- 前端首次对话不传 `thread_id`，后端自动生成 UUID7
- 前端保存返回的 `thread_id`，后续对话携带同一 ID 以维持上下文

### 3.6 ER 图

```
┌─────────────────────────────┐
│          users              │
├─────────────────────────────┤
│ PK │ id          VARCHAR(36)│
│ UK │ username    VARCHAR(64)│
│ UK │ phone       VARCHAR(20)│
│ UK │ email       VARCHAR(128)│
│    │ nickname    VARCHAR(64)│
│    │ password_hash VARCHAR(128)│
│    │ avatar      VARCHAR(256)│
│    │ workspace_id VARCHAR(36)│
│    │ is_active   BOOLEAN     │
│    │ created_at  DATETIME    │
│    │ updated_at  DATETIME    │
└────────────┬────────────────┘
             │ 1
             │
             │ N
┌────────────▼────────────────┐
│       user_oauths           │
├─────────────────────────────┤
│ PK │ id          VARCHAR(36)│
│ FK │ user_id     VARCHAR(36)│──→ users.id
│    │ provider    VARCHAR(20)│
│    │ open_id     VARCHAR(128)│
│    │ created_at  DATETIME    │
│ UK │ (provider, open_id)    │
└─────────────────────────────┘

┌─────────────────────────────┐
│      login_records          │
├─────────────────────────────┤
│ PK │ id          VARCHAR(36)│
│ IX │ account     VARCHAR(128)│
│    │ success     BOOLEAN     │
│    │ ip          VARCHAR(45) │
│    │ created_at  DATETIME    │
└─────────────────────────────┘
（独立审计表，不与 users 关联）
```

**关系说明**：
- `users` : `user_oauths` = **1 : N**（一个用户可绑定多个第三方平台）
- `login_records` 是**独立审计日志**，不设外键关联 `users`，便于保留已删除用户的登录记录

---

## 4. 键值存储设计

### 4.1 架构概述

键值存储用于管理临时状态数据，通过抽象接口 `KeyValueStore` 提供统一 API：

```python
# 来源: backend/src/core/store.py

class KeyValueStore(ABC):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int = 300) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def exists(self, key: str) -> bool: ...
    async def incr(self, key: str) -> int: ...    # 原子递增
    async def ttl(self, key: str) -> int: ...     # 剩余过期时间
```

**双实现策略**：

| 实现 | 类名 | 适用场景 |
|------|------|----------|
| Redis | `RedisStore` | 生产环境，Redis 可用时自动启用 |
| Memory | `MemoryStore` | 开发环境或 Redis 不可用时的回退方案 |

选择逻辑在 `create_store()` 中：尝试连接 Redis 并 `ping()`，成功则使用 `RedisStore`，失败则降级为 `MemoryStore`。

`MemoryStore` 使用 `threading.Lock` 保证线程安全，支持惰性 TTL 驱逐。

### 4.2 键空间设计

#### 登录风控

| Key 模式 | 类型 | TTL | 说明 |
|----------|------|-----|------|
| `login:fail:{account}` | String | 锁定时间 | 格式 `"{failCount}:{lockedUntil}"`，如 `"3:0"` 表示失败 3 次未锁定 |

**登录锁定时长**: `LOGIN_LOCK_MINUTES`（默认 30 分钟）
**最大失败次数**: `LOGIN_MAX_FAILS`（默认 5 次）

#### 短信验证码

| Key 模式 | 类型 | TTL | 说明 |
|----------|------|-----|------|
| `sms:{phone}` | String | 300s (5 分钟) | 6 位数字验证码 |
| `sms:daily:{phone}:{date}` | String | 86400s (24 小时) | 当日发送次数计数器 |

**每日限制**: `SMS_DAILY_LIMIT`（默认 5 条/天）

#### 邮箱验证码

| Key 模式 | 类型 | TTL | 说明 |
|----------|------|-----|------|
| `email:{email}` | String | 300s (5 分钟) | 邮箱验证码 |

#### 验证码 (Captcha)

| Key 模式 | 类型 | TTL | 说明 |
|----------|------|-----|------|
| `captcha:slide:{session_id}` | String | `CAPTCHA_EXPIRE` (默认 300s) | 滑块拼图正确位置 `"{gapX}:{y}"` |
| `captcha:image:{key}` | String | `CAPTCHA_EXPIRE` (默认 300s) | 图形验证码答案（小写） |
| `captcha:ticket:{ticket}` | String | `CAPTCHA_EXPIRE` (默认 300s) | 验证通过凭证 randstr |

#### OAuth 状态

| Key 模式 | 类型 | TTL | 说明 |
|----------|------|-----|------|
| `oauth:state:{state}` | String | 600s (10 分钟) | OAuth 流程中的 state 参数，存 provider 名称 |

### 4.3 数据生命周期

```
验证码发送 → [300s TTL] → 自动过期
滑块验证  → [300s TTL] → 验证通过立即删除 / 过期自动清理
OAuth 流程 → [600s TTL] → 回调后删除 / 过期自动清理
登录失败计数 → [锁定时间 TTL] → 成功后删除 / 过期自动清理
每日短信计数 → [86400s TTL] → 次日自动重置
```

所有临时数据具有明确的 TTL，无数据泄漏风险。`MemoryStore` 回退模式下，进程重启所有临时数据丢失，但不影响核心业务（用户需重新获取验证码）。

---

## 5. 安全模型

### 5.1 密码安全

```
┌──────────┐    RSA 公钥加密     ┌──────────┐    bcrypt 哈希    ┌──────────────┐
│  前端     │ ─────────────────→ │  后端     │ ───────────────→ │ users 表      │
│  明文密码  │                    │  解密     │                  │ password_hash │
└──────────┘                    └──────────┘                  └──────────────┘
```

**传输层**:
- 前端使用 RSA 公钥（`/api/auth/public-key` 获取）加密密码后再发送
- RSA 密钥长度: 2048 位（`RSA_KEY_SIZE` 配置）
- 填充方式: PKCS1v15
- 每次服务重启生成新密钥对（内存中，不持久化）

**存储层**:
- 使用 **bcrypt** 哈希（自动加盐）
- `hash_password()`: `bcrypt.hashpw(password.encode(), bcrypt.gensalt())`
- `verify_password()`: `bcrypt.checkpw(plain.encode(), hashed.encode())`

**密码字段可空**: OAuth 用户无本地密码，`password_hash` 为 NULL。

### 5.2 身份认证与令牌

**JWT 配置**:

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 算法 | HS256 | 对称加密 |
| Access Token 有效期 | 7200s (2 小时) | `JWT_ACCESS_EXPIRE` |
| Refresh Token 有效期 | 604800s (7 天) | `JWT_REFRESH_EXPIRE` |
| Secret 来源 | `.jwt_secret` 文件或 `JWT_SECRET_KEY` 环境变量 | 无配置时自动生成并持久化 |

**Token Payload**:

```json
// Access Token
{ "sub": "<user_id>", "type": "access", "iat": 1234567890, "exp": 1234575090 }

// Refresh Token
{ "sub": "<user_id>", "type": "refresh", "iat": 1234567890, "exp": 1235172690 }
```

**Secret 持久化**: 若未配置 `JWT_SECRET_KEY`，系统自动生成 32 字节随机密钥写入 `.jwt_secret` 文件，确保重启后已签发 Token 仍然有效。

### 5.3 登录风控

```
失败计数流程:
 ┌──────────┐    失败     ┌──────────────────┐
 │ 登录尝试  │ ──────────→ │ incr login:fail:  │
 └──────────┘             │ {account}         │
      │                   └────────┬─────────┘
      │ 成功                       │ count >= LOGIN_MAX_FAILS (5)?
      ▼                            ▼
 ┌──────────────┐          ┌──────────────────┐
 │ 清除失败计数  │          │ 锁定账户          │
 │ delete key   │          │ lockedUntil =     │
 └──────────────┘          │ now + 30 min      │
                           └──────────────────┘

锁定期间:
 ┌──────────┐    已锁定    ┌──────────────────┐
 │ 登录尝试  │ ──────────→ │ HTTP 403         │
 └──────────┘             │ "Try again in N   │
                          │  minutes"         │
                          └──────────────────┘
```

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `LOGIN_MAX_FAILS` | 5 | 最大失败次数 |
| `LOGIN_LOCK_MINUTES` | 30 | 锁定时长（分钟） |

---

## 6. 数据流与 API 映射

### 6.1 认证相关

| API | 方法 | 涉及存储 | 操作 |
|-----|------|----------|------|
| `/api/auth/public-key` | GET | 内存 (RSA key) | 获取 RSA 公钥 |
| `/api/auth/login/account` | POST | KV + users + login_records | 账号密码登录，失败计数+审计日志 |
| `/api/auth/login/phone` | POST | KV + users | 手机验证码登录，首次自动注册 |
| `/api/auth/register/phone` | POST | KV + users | 手机号注册 |
| `/api/auth/register/email` | POST | KV + users | 邮箱注册 |
| `/api/auth/refresh` | POST | users | 刷新 Token |
| `/api/auth/logout` | POST | — | 无状态登出（前端清除 Token） |
| `/api/auth/fail-count` | GET | KV | 查询登录失败次数 |

### 6.2 OAuth 第三方登录

```
1. GET /api/oauth/auth-url?provider=github
   └→ KV: set oauth:state:{uuid} = "github" (TTL 600s)
   └→ 返回授权 URL

2. 用户在第三方完成授权，浏览器重定向到 /oauth/callback?code=xxx&state=xxx

3. POST /api/oauth/callback { provider, code, state }
   └→ KV: get oauth:state:{state} → 验证 state
   └→ 第三方 API: code → access_token → userinfo
   └→ DB: SELECT user_oauths WHERE provider=X AND open_id=Y
   └→ 新用户: INSERT users + INSERT user_oauths
   └→ 返回 JWT Token Pair
```

### 6.3 智能体对话

| API | 方法 | 涉及存储 | 说明 |
|-----|------|----------|------|
| `/api/chat` | POST | langgraph_checkpoints.db | 非流式对话，通过 `thread_id` 关联上下文 |
| `/api/chat/stream` | POST | langgraph_checkpoints.db | SSE 流式对话，逐 Token 返回 |

**检查点存储**:

- 每次对话自动保存检查点到 `langgraph_checkpoints.db`
- 通过 `thread_id` 恢复历史对话上下文
- `thread_id` 由前端管理（首次对话自动生成 UUID7，后续请求携带同一 ID）

---

## 7. 配置与部署

### 7.1 环境变量

```bash
# ---- 数据库 ----
DATABASE_URL=sqlite+aiosqlite:///./db/ke-hermes.db   # 业务数据库
CHECKPOINT_DB_PATH=./db/langgraph_checkpoints.db   # Agent 检查点数据库

# ---- JWT ----
JWT_SECRET_KEY=                    # 留空自动生成并持久化到 .jwt_secret
JWT_ACCESS_EXPIRE=7200            # Access Token 有效期 (秒)
JWT_REFRESH_EXPIRE=604800         # Refresh Token 有效期 (秒)

# ---- 密码加密 ----
RSA_KEY_SIZE=2048                 # RSA 密钥长度

# ---- 登录风控 ----
LOGIN_MAX_FAILS=5                 # 最大失败次数
LOGIN_LOCK_MINUTES=30            # 锁定时长 (分钟)

# ---- 短信 ----
SMS_PROVIDER=                     # 短信服务商 (留空为开发模式)
SMS_ACCESS_KEY=                   # 短信服务 AccessKey
SMS_SECRET_KEY=                   # 短信服务 SecretKey
SMS_SIGN_NAME=                    # 短信签名
SMS_TEMPLATE_CODE=                # 短信模板代码
SMS_DAILY_LIMIT=5                 # 每日短信上限

# ---- 验证码 ----
CAPTCHA_EXPIRE=300               # 验证码有效期 (秒)
SLIDE_THRESHOLD=5                # 滑块验证容差 (像素)

# ---- Redis ----
REDIS_URL=redis://127.0.0.1:6379/0  # Redis 地址 (不可用时自动回退 MemoryStore)

# ---- OAuth ----
OAUTH_GITHUB_CLIENT_ID=
OAUTH_GITHUB_CLIENT_SECRET=
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
OAUTH_WECHAT_CLIENT_ID=
OAUTH_WECHAT_CLIENT_SECRET=
```

### 7.2 初始化流程

```python
# 来源: backend/src/server.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()        # 1. 创建业务表 (users, user_oauths, login_records)
    await init_graph()      # 2. 初始化 Agent (创建 AsyncSqliteSaver + LLM)
    store = await create_store()  # 3. 初始化 KV 存储 (Redis 或 Memory)
    set_store(store)
    init_jwt()             # 4. 初始化 JWT Secret
    yield                  # 5. 应用就绪
```

**数据库初始化** (`init_db`):

```python
# 来源: backend/src/db/engine.py
async def init_db():
    from db.base import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

所有模型继承 `Base` 的表自动创建，**无独立的迁移脚本**。首次启动或模型字段变更后，SQLAlchemy 自动同步表结构（`create_all` 不会修改已有表）。

---

## 附录 A: 文件索引

| 文件 | 职责 |
|------|------|
| `backend/src/db/base.py` | ORM 基类 `Base` (DeclarativeBase) |
| `backend/src/db/engine.py` | 异步引擎、会话工厂、`init_db`、`get_db` |
| `backend/src/db/models/user.py` | `User` 模型 |
| `backend/src/db/models/user_oauth.py` | `UserOAuth` 模型 |
| `backend/src/db/models/login_record.py` | `LoginRecord` 模型 |
| `backend/src/db/models/__init__.py` | 模型导出汇总 |
| `backend/src/core/store.py` | `KeyValueStore` 抽象接口 + Redis/Memory 实现 |
| `backend/src/core/security.py` | RSA 加密、bcrypt 哈希、JWT 签发/验证 |
| `backend/src/core/response.py` | 统一 API 响应格式 `ApiResponse` |
| `backend/src/api/deps.py` | FastAPI 依赖注入 (`get_db`, `get_store`, `get_client_ip`) |
| `backend/src/api/auth/service.py` | 认证业务逻辑 |
| `backend/src/api/auth/schemas.py` | 认证请求/响应 Pydantic 模型 |
| `backend/src/api/auth/auth_api.py` | 认证 API 路由 |
| `backend/src/api/oauth/service.py` | OAuth 业务逻辑 |
| `backend/src/api/sms/service.py` | 短信验证码业务逻辑 |
| `backend/src/api/captcha/service.py` | 验证码生成/验证逻辑 |
| `backend/src/agent/graph.py` | Agent 图定义 + LangGraph checkpointer 初始化 |
| `backend/src/agent/config/config.py` | 全局配置（环境变量 → Pydantic Settings） |
| `backend/src/server.py` | FastAPI 应用入口 + 生命周期管理 |

## 附录 B: 术语对照

| 术语 | 英文 | 说明 |
|------|------|------|
| 检查点 | Checkpoint | LangGraph 中保存对话状态快照的机制 |
| 短期记忆 | Short-term Memory | Agent 在多轮对话中保持上下文的存储 |
| 键值存储 | KV Store / Key-Value Store | Redis 或 MemoryStore，用于临时状态 |
| 工作空间 | Workspace | 多租户隔离单元，当前预留字段 |
