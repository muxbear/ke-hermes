# DeepAgents Memory 使用详解

> 基于 [DeepAgents 官方 Memory 文档](https://docs.langchain.com/oss/python/deepagents/memory) 整理，并结合 ke-hermes 后端现状给出落地路径。  
> 适用版本：`deepagents>=0.6.1`，`langgraph>=1.0`。

---

## 目录

1. [概述：Memory 是什么](#1-概述memory-是什么)
2. [短期记忆 vs 长期记忆](#2-短期记忆-vs-长期记忆)
3. [Memory 工作机制（三步）](#3-memory-工作机制三步)
4. [作用域（Scoped Memory）](#4-作用域scoped-memory)
5. [高级用法](#5-高级用法)
6. [实战案例：个性化客服助手](#6-实战案例个性化客服助手)
7. [ke-hermes 现状分析](#7-ke-hermes-现状分析)
8. [ke-hermes 落地方案与步骤](#8-ke-hermes-落地方案与步骤)
9. [附录：关键 API 速查](#9-附录关键-api-速查)

---

## 1. 概述：Memory 是什么

DeepAgents 将 **Memory（记忆）** 设计为一等公民：智能体通过 **文件系统抽象** 读写记忆——记忆就是虚拟路径下的 Markdown/文本文件（如 `/memories/AGENTS.md`），底层由 **Backend** 决定文件存到哪里、谁能访问。

Memory 让智能体能够：

- **跨对话** 记住用户偏好、业务上下文
- **持续进化** 自己的角色设定与行为风格（Agent-scoped）
- **按需加载** 技能说明（Skills，属于程序性记忆 Procedural Memory）

与 RAG 知识库的区别：

| 维度 | DeepAgents Memory | RAG 知识库 |
|------|-------------------|------------|
| 写入者 | 智能体自身（`edit_file`）或应用代码 | 用户上传文档、索引流程 |
| 粒度 | 结构化 Markdown 文件 | 文档切片 + 向量检索 |
| 典型内容 | 偏好、人设、工作流 | 企业文档、手册、FAQ |
| 隔离 | Store namespace（user/agent/org） | 按 knowledge_base + user 隔离 |

---

## 2. 短期记忆 vs 长期记忆

官方文档明确区分两类记忆：

### 2.1 短期记忆（Short-term Memory）

- **范围**：单次对话会话内
- **机制**：LangGraph **Checkpointer** + `thread_id`
- **内容**：完整对话历史、会话内临时 scratch 文件（`StateBackend`）
- **生命周期**：绑定到 `thread_id`；删除对话可 `checkpointer.adelete_thread(thread_id)`

ke-hermes 中对应：

```python
# backend/src/api/agent/agent_api.py
config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
result = await get_graph().ainvoke(
    {"messages": [HumanMessage(content=req.message)]},
    config=config,
    context=context,
)
```

### 2.2 长期记忆（Long-term Memory）

- **范围**：跨 `thread_id`、跨多次登录会话
- **机制**：LangGraph **Store** + `StoreBackend` + `memory=[...]` 路径
- **内容**：`/memories/*.md` 等持久化文件
- **生命周期**：写入 Store 后，下次任意新对话均可读取

ke-hermes 中 Store 初始化见 `backend/src/agent/graph.py`：

```python
if backend == "sqlite":
    _store = InMemoryStore()          # 开发环境：进程重启即丢失
elif backend == "postgres":
    _store = AsyncPostgresStore(_conn_pool)  # 生产：持久化
```

> **重要**：开发环境使用 SQLite Checkpointer 时，Store 当前为 `InMemoryStore`，长期记忆 **不会落盘**。生产环境应使用 PostgreSQL 后端以获得真正的跨会话持久化。

---

## 3. Memory 工作机制（三步）

官方文档总结为三个步骤：

```
┌─────────────────────────────────────────────────────────────────┐
│  1. 配置 memory= 路径 + Backend 路由                             │
│  2. 启动时/按需 读取 → 注入 system prompt 或运行时 read_file      │
│  3. 对话中 edit_file 更新（可选）→ 写入 Store → 下次对话可见       │
└─────────────────────────────────────────────────────────────────┘
```

### 3.1 指向记忆文件（配置）

创建 Agent 时传入 `memory` 参数，列出要加载的长期记忆虚拟路径：

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-4o",
    memory=[
        "/memories/AGENTS.md",      # 智能体人设与行为准则
        "/memories/preferences.md", # 用户偏好（如 user-scoped）
    ],
    store=store,                   # LangGraph Store 实例
    checkpointer=checkpointer,     # 短期记忆
    backend=...,                   # 见下文 CompositeBackend
)
```

**知识点**：

- 路径必须以 `/memories/` 开头（当使用 `StoreBackend` 路由到该前缀时）
- 可同时挂载多个文件；每个文件对应 Store 中的一个 key
- `skills=["/skills/"]` 是 **程序性记忆**，通常按需读取完整 SKILL.md，而非全部塞进 prompt

### 3.2 智能体读取记忆

两种检索策略（官方 Advanced 表格）：

| 策略 | 说明 | 典型场景 |
|------|------|----------|
| **加载到 prompt（默认）** | 启动时将 `memory=` 列表中的文件内容注入 system prompt | AGENTS.md、合规策略 |
| **按需加载（On demand）** | 仅加载摘要/描述，匹配任务后再 `read_file` | Skills 目录 |

Skills 示例（按需）：

```markdown
---
name: langgraph-docs
description: 获取 LangGraph 官方文档以回答架构问题。
---

# langgraph-docs
...完整指令...
```

Agent 启动时只看到 `description`；用户问到 LangGraph 时才读取完整 SKILL.md，从而 **控制 context 长度**。

### 3.3 智能体更新记忆（可选）

默认情况下，Agent 拥有内置 `edit_file` 工具，可在对话中 **热路径（hot path）** 更新记忆：

```python
# 用户说："请记住我喜欢详细解释"
# Agent 内部等价于：
# edit_file("/memories/preferences.md", ...)
```

更新后的内容通过 `StoreBackend` 持久化到 LangGraph Store，**下一个新 thread_id 的对话** 也能读到。

并非所有记忆都可写：

- 用户偏好、Agent 自学习 → 可读写
- 组织合规策略、开发者预置 Skills → 建议 **只读**（见 [5.4](#54-只读-vs-可写记忆)）

---

## 4. 作用域（Scoped Memory）

Backend 的 **`namespace`** 决定「同一路径下，不同用户/智能体是否共享同一份文件」。

### 4.1 Agent-scoped（智能体级，全员共享）

同一智能体下 **所有用户共享** 一份记忆。智能体通过多轮对话积累「人格、专长、经验教训」。

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

agent = create_deep_agent(
    model="google_genai:gemini-2.5-flash",
    memory=["/memories/AGENTS.md"],
    skills=["/skills/"],
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                namespace=lambda rt: (
                    rt.server_info.assistant_id,  # 仅 assistant_id
                ),
            ),
            "/skills/": StoreBackend(
                namespace=lambda rt: (
                    rt.server_info.assistant_id,
                ),
            ),
        },
    ),
)
```

**适用场景**：

- 平台级「主智能体」统一人设（SOUL.md、IDENTITY.md）
- 智能体在运营中自我优化响应风格
- 多用户共享同一套 Agent 技能库

**安全注意**：任一用户若可写入 Agent-scoped 记忆，可能 **污染** 其他用户读到的内容。共享写入需谨慎，或改为只读 + 后台 consolidation。

### 4.2 User-scoped（用户级，按用户隔离）

每个用户独立一份 `/memories/preferences.md`，用户 A 的偏好不会泄漏给用户 B。

```python
agent = create_deep_agent(
    model="google_genai:gemini-2.5-flash",
    memory=["/memories/preferences.md"],
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                namespace=lambda rt: (rt.server_info.user.identity,),
            ),
        },
    ),
)
```

**完整示例：多种子记忆 + 跨 thread 验证**

```python
from langchain_core.utils.uuid import uuid7
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# 为两位用户预置不同偏好
store.put(
    ("user-alice",),
    "/memories/preferences.md",
    create_file_data("""## Preferences
- 喜欢简洁要点
- 偏好 Python 示例
"""),
)
store.put(
    ("user-bob",),
    "/memories/preferences.md",
    create_file_data("""## Preferences
- 喜欢详细解释
- 偏好 TypeScript 示例
"""),
)

agent = create_deep_agent(
    model="openai:gpt-4o",
    memory=["/memories/preferences.md"],
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={
            "/memories/": StoreBackend(
                rt,
                namespace=lambda rt: (rt.server_info.user.identity,),
            ),
        },
    ),
    store=store,
)

# Alice 的对话
agent.invoke(
    {"messages": [{"role": "user", "content": "如何读取 CSV？"}]},
    config={"configurable": {"thread_id": str(uuid7())}},
    context={"user": {"identity": "user-alice"}},
)

# Bob 另开 thread，读到的是 Bob 的 preferences
agent.invoke(
    {"messages": [{"role": "user", "content": "如何读取 CSV？"}]},
    config={"configurable": {"thread_id": str(uuid7())}},
    context={"user": {"identity": "user-bob"}},
)
```

**ke-hermes 映射**：JWT 中的 `user_id` 传入 `Context.user_id`，`StoreBackend` namespace 使用 `(user_id,)`——见 `agent_builder.py`。

### 4.3 混合作用域（Agent + User）

多智能体部署时，namespace 可同时包含 `assistant_id` 与 `user_id`：

```python
StoreBackend(
    namespace=lambda rt: (
        rt.server_info.assistant_id,
        rt.server_info.user.identity,
    ),
)
```

| namespace 组合 | 隔离效果 |
|----------------|----------|
| `(assistant_id,)` | 每智能体一份，所有用户共享 |
| `(user_id,)` | 每用户一份，所有智能体共享（单 Agent 平台常用） |
| `(assistant_id, user_id)` | 每智能体 × 每用户独立（推荐多 Agent SaaS） |

### 4.4 预置种子记忆（Seed）

应用启动或用户注册时，向 Store 写入初始内容：

```python
from deepagents.backends.utils import create_file_data

store.put(
    ("my-agent",),
    "/memories/AGENTS.md",
    create_file_data("""## Response style
- 回答简洁
- 尽量给出代码示例
"""),
)
```

官方建议：部署到 LangSmith 时使用平台 Store；自托管时使用 `AsyncPostgresStore` 或 `InMemoryStore`（仅开发）。

---

## 5. 高级用法

官方从六个维度描述高级记忆策略：

| 维度 | 问题 | 选项 |
|------|------|------|
| Duration | 持续多久？ | 短期（单会话）/ 长期（跨会话） |
| Information type | 什么类型？ | 情节 Episodic / 程序 Procedural / 语义 Semantic |
| Scope | 谁可见可改？ | User / Agent / Organization |
| Update strategy | 何时写入？ | 对话中（默认）/ 对话间后台 consolidation |
| Retrieval | 如何读取？ | 注入 prompt / 按需（Skills） |
| Permissions | 能否写入？ | 读写（默认）/ 只读 |

### 5.1 情节记忆（Episodic Memory）

记录 **过去发生了什么**（完整对话上下文、解决步骤），区别于语义记忆（事实与偏好写在 MD 文件里）。

DeepAgents **已内置** 情节记忆基础能力：**Checkpointer 将每个 thread 持久化为 checkpoint 链**。

若要 **跨 thread 搜索历史对话**，需封装工具，例如：

```python
from langchain.tools import tool, ToolRuntime
from langgraph_sdk import get_client

client = get_client(url="<DEPLOYMENT_URL>")

@tool
async def search_past_conversations(query: str, runtime: ToolRuntime) -> str:
    """搜索用户历史对话中与 query 相关的上下文。"""
    user_id = runtime.server_info.user.identity
    threads = await client.threads.search(
        metadata={"user_id": user_id},
        limit=5,
    )
    results = []
    for thread in threads:
        history = await client.threads.get_history(thread_id=thread["thread_id"])
        results.append(history)
    return str(results)
```

**按组织搜索**：

```python
threads = await client.threads.search(metadata={"org_id": org_id}, limit=5)
```

**典型场景**：编码助手回顾上周调试同一 Bug 的过程，直接定位根因而非重新排查。

### 5.2 组织级记忆（Organization-level Memory）

组织全员共享、通常 **只读** 的策略与知识：

```python
agent = create_deep_agent(
    memory=[
        "/memories/preferences.md",   # user-scoped，可写
        "/policies/compliance.md",    # org-scoped，只读
    ],
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                namespace=lambda rt: (rt.server_info.user.identity,),
            ),
            "/policies/": StoreBackend(
                namespace=lambda rt: (rt.context.org_id,),
            ),
        },
    ),
)
```

由应用代码写入，而非 Agent：

```python
await client.store.put_item(
    (org_id,),
    "/compliance.md",
    create_file_data("""## 合规要求
- 不得披露内部定价
- 财务建议必须附带免责声明
"""),
)
```

**安全**：组织级共享 writable 记忆易导致 prompt injection 跨用户传播，应对 `/policies/` 配置只读权限。

### 5.3 后台 Consolidation（Sleep-time Compute）

| 方式 | 优点 | 缺点 |
|------|------|------|
| **热路径**（对话中写入） | 立即可用、用户可感知 | 增加延迟；Agent 多任务并行 |
| **后台**（对话间合并） | 无用户侧延迟；可综合多会话提炼 | 下次对话才生效；需第二个 Agent + 调度 |

官方推荐模式：

1. 部署 **consolidation_agent**（独立 Deep Agent）
2. 工具：`search_recent_conversations` 拉取近 N 小时 thread
3. System prompt：合并事实、删除过时信息、保持简洁
4. **Cron** 定时触发（UTC），且 cron 间隔与 lookback 窗口一致

Consolidation Agent 骨架：

```python
from datetime import datetime, timedelta, timezone
from deepagents import create_deep_agent
from langchain.tools import tool, ToolRuntime
from langgraph_sdk import get_client

sdk_client = get_client(url="<DEPLOYMENT_URL>")

@tool
async def search_recent_conversations(query: str, runtime: ToolRuntime) -> str:
    """搜索该用户最近 6 小时内更新的对话。"""
    user_id = runtime.server_info.user.identity
    since = datetime.now(timezone.utc) - timedelta(hours=6)
    threads = await sdk_client.threads.search(
        metadata={"user_id": user_id},
        updated_after=since.isoformat(),
        limit=20,
    )
    conversations = []
    for thread in threads:
        history = await sdk_client.threads.get_history(
            thread_id=thread["thread_id"]
        )
        conversations.append(history["values"]["messages"])
    return str(conversations)

consolidation_agent = create_deep_agent(
    model="openai:gpt-4o",
    system_prompt="""审查近期对话并更新用户 memory 文件。
合并新事实，删除过时信息，保持简洁。""",
    tools=[search_recent_conversations],
)
```

Cron 注册（LangGraph Platform）：

```python
await client.crons.create(
    assistant_id="consolidation_agent",
    schedule="0 */6 * * *",  # 每 6 小时，UTC
    input={"messages": [{"role": "user", "content": "Consolidate recent memories."}]},
)
```

ke-hermes 已有 `cron_jobs` ORM 表，可对接类似调度（见 [8.4](#84-阶段四后台-consolidation可选)）。

### 5.4 只读 vs 可写记忆

| 权限 | 场景 | 实现 |
|------|------|------|
| 读写（默认） | 用户偏好、Agent 自改进 | Agent `edit_file` |
| 只读 | 合规策略、开发者 Skills、组织知识 | 应用代码 `store.put` + permissions 拒绝写 |

**安全建议**（官方）：

- 默认 **user scope**，除非明确需要共享
- 共享策略用只读 + 应用侧写入
- 敏感路径写入前 **Human-in-the-loop**（LangGraph interrupt）

### 5.5 并发写入

多 thread 并行写同一文件可能 **last-write-wins** 冲突。

- User-scoped：通常单用户单活跃会话，冲突少
- Agent/org-scoped：考虑后台 consolidation 串行写入，或 **按主题拆文件**（`topic-a.md`、`topic-b.md`）

实践中 LLM 遇到冲突常会重试，单次丢失写入一般可接受。

### 5.6 多智能体同部署

namespace 务必包含 `assistant_id`，避免不同 Agent 读写同一 Store key：

```python
StoreBackend(
    namespace=lambda rt: (
        rt.server_info.assistant_id,
        rt.server_info.user.identity,
    ),
)
```

可用 LangSmith Tracing 审计每次 `edit_file` 写入内容。

---

## 6. 实战案例：个性化客服助手

### 6.1 业务目标

SaaS 客服智能体需要：

1. **组织级** 只读：`/policies/refund.md` 退款政策（全员一致）
2. **用户级** 可写：`/memories/USER.md` 记住 VIP 等级、语言偏好、历史投诉摘要
3. **Agent 级** 可写：`/memories/AGENTS.md` 总结常见 FAQ 答复模式（运营可审核）
4. **情节记忆**：用户说「上次订单 #12345 的问题解决了吗」时能搜历史 thread

### 6.2 架构示意

```mermaid
flowchart TB
    subgraph HotPath["热路径 - 对话中"]
        User[用户消息] --> Agent[主 Agent]
        Agent --> ReadMem[读取 memory 文件]
        Agent --> EditMem[edit_file 更新 USER.md]
        Agent --> Checkpoint[Checkpointer 短期记忆]
    end

    subgraph Store["LangGraph Store"]
        OrgNS["namespace: org_id"]
        UserNS["namespace: user_id"]
        AgentNS["namespace: assistant_id"]
        OrgNS --> Policy["/policies/refund.md 只读"]
        UserNS --> UserMD["/memories/USER.md 可写"]
        AgentNS --> AgentsMD["/memories/AGENTS.md 可写"]
    end

    subgraph Background["后台 - Cron 每 6h"]
        Cron[Cron] --> ConsAgent[Consolidation Agent]
        ConsAgent --> SearchTool[search_recent_conversations]
        ConsAgent --> UserMD
    end

    ReadMem --> Store
    EditMem --> Store
```

### 6.3 核心代码

```python
from dataclasses import dataclass
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.store.postgres.aio import AsyncPostgresStore

@dataclass
class AppContext:
    org_id: str

def build_support_agent(store, checkpointer, assistant_id: str):
    return create_deep_agent(
        model="openai:gpt-4o",
        memory=[
            "/memories/AGENTS.md",
            "/memories/USER.md",
            "/policies/refund.md",
        ],
        system_prompt="你是客服助手。遵守 /policies/ 下政策；个性化信息写入 /memories/USER.md。",
        backend=lambda rt: CompositeBackend(
            default=StateBackend(rt),
            routes={
                "/memories/AGENTS.md": StoreBackend(
                    rt,
                    namespace=lambda rt: (assistant_id,),
                ),
                "/memories/USER.md": StoreBackend(
                    rt,
                    namespace=lambda rt: (rt.server_info.user.identity,),
                ),
                "/policies/": StoreBackend(
                    rt,
                    namespace=lambda rt: (rt.context.org_id,),
                    # 生产环境在此配置 read-only permissions
                ),
            },
        ),
        store=store,
        checkpointer=checkpointer,
        context_schema=AppContext,
    )

# 启动时种子组织政策
async def seed_org_policy(store, org_id: str):
    await store.aput(
        (org_id,),
        "/policies/refund.md",
        create_file_data("""## 退款政策
- 7 天内未使用可全额退款
- 超过 7 天按剩余天数比例退款
"""),
    )
```

### 6.4 验证流程

1. **Thread-1（用户 Alice）**：「我是 VIP，请用中文简短回答，记住这一点。」  
   → Agent 更新 `/memories/USER.md`

2. **Thread-2（Alice 新会话）**：「查询退款流程」  
   → 读取 USER.md（中文、简短）+ `/policies/refund.md`（组织政策）

3. **Thread-3（用户 Bob）**：「查询退款流程」  
   → 仅读 Bob 的 USER.md（空或默认）+ 同一 refund 政策

4. **6 小时后 Cron**：Consolidation Agent 合并 Alice 多轮对话中的产品反馈到 USER.md

---

## 7. ke-hermes 现状分析

### 7.1 已实现能力

| 能力 | 位置 | 说明 |
|------|------|------|
| 长期记忆路径配置 | `agent/builders/agent_builder.py` → `with_memory()` | 从 DB `agent.files` 生成 `/memories/{filename}` |
| User-scoped Store | `with_backend()` | `/memories/` → `StoreBackend(namespace=user_id)` |
| Store 注入 | `graph.py` + `create_deep_agent(..., store=store)` | PG 持久化 / SQLite 开发用 InMemoryStore |
| 短期记忆 | `agent_api.py` | `thread_id` + checkpointer |
| 用户上下文 | `Context(user_id=...)` | JWT 注入 |
| Agent 配置文件 DB | `agent_files` 表 + Agents API | 管理 AGENTS.md、MEMORY.md 等 **元数据** |
| Skills 文件系统 | `FilesystemBackend` + 沙盒同步中间件 | 程序性记忆（按需） |

当前 `AgentBuilder` 核心片段：

```python
# backend/src/agent/builders/agent_builder.py
self._backend = CompositeBackend(
    default=self._sandbox_backend,
    routes={
        "/memories/": StoreBackend(
            namespace=lambda ctx: (
                cast(Any, ctx).runtime.context.user_id,
            ),
        ),
        "/skills/": FilesystemBackend(
            root_dir=self._skills_root, virtual_mode=True
        ),
    },
)

# memory 路径
if self._agent_info.files:
    self._memory = [f"/memories/{f}" for f in self._agent_info.files]
else:
    self._memory = ["/memories/AGENT.md"]
```

### 7.2 差距与风险

| 编号 | 问题 | 影响 |
|------|------|------|
| G1 | SQLite 开发模式下 Store=`InMemoryStore` | 重启后长期记忆丢失，与「跨会话记忆」预期不符 |
| G2 | `agent_files` 内容 **未同步** 到 LangGraph Store | 管理后台改的 AGENTS.md 不会进入 Agent runtime |
| G3 | 默认文件名不一致：DB 用 `AGENTS.md`，fallback 用 `AGENT.md` | 空 files 时可能读不到预期文件 |
| G4 | namespace 仅 `(user_id,)`，无 `assistant_id` | 未来多主 Agent 时会互相覆盖 |
| G5 | 无组织级 `/policies/` 只读路由 | 无法满足企业合规场景 |
| G6 | 无 `search_past_conversations` 情节记忆工具 | 无法跨 thread 引用历史 |
| G7 | 无 Consolidation Agent / Cron 执行链 | 无法做 sleep-time 记忆合并 |
| G8 | Agent-scoped 与 User-scoped 文件未分离 | AGENTS.md（全局人设）与 USER.md（个人偏好）混在同一 user namespace |

---

## 8. ke-hermes 落地方案与步骤

### 8.1 目标架构

```mermaid
flowchart LR
    subgraph Admin["Agents 管理 API"]
        SaveFile[save_agent_file]
        Sync[memory_sync_service]
        SaveFile --> Sync
    end

    subgraph Runtime["Agent Runtime"]
        Builder[AgentBuilder]
        Graph[graph.py Store]
        Chat[agent_api.py]
    end

    subgraph Namespaces["Store Namespaces"]
        N1["agent_id → AGENTS.md SOUL.md 等"]
        N2["user_id → USER.md MEMORY.md"]
        N3["org_id → policies 只读"]
    end

    Sync --> Graph
    Builder --> Graph
    Chat --> Builder
    Graph --> N1
    Graph --> N2
    Graph --> N3
```

**文件作用域规划**（建议）：

| 文件 | 作用域 | 读写 | 说明 |
|------|--------|------|------|
| `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `TOOLS.md` | `(agent_id,)` | Agent 可读；写可选/需审核 | 平台人设 |
| `USER.md`, `MEMORY.md` | `(user_id,)` 或 `(agent_id, user_id)` | 用户可写 | 个人偏好与摘要 |
| `HEARTBEAT.md` | `(agent_id,)` | 系统 Cron 写 | 定时任务状态 |
| `/policies/*.md` | `(org_id,)` | 只读 | 合规（二期） |

### 8.2 阶段一：Store 持久化与文件名统一（P0）

**步骤：**

1. **生产环境** 设置 `CHECKPOINT_BACKEND=postgres`，确保 `AsyncPostgresStore` 生效。

   ```env
   CHECKPOINT_BACKEND=postgres
   CHECKPOINT_DB_URL=postgresql://user:pass@127.0.0.1:5432/ke_hermes
   ```

2. **统一默认记忆文件名**：将 `agent_builder.py` 中 fallback 从 `AGENT.md` 改为 `AGENTS.md`，与 `DEFAULT_AGENT_FILES` 一致。

3. **开发环境可选增强**：SQLite 模式下为 Store 使用独立 SQLite 文件（若 LangGraph 版本支持 `AsyncSqliteStore`），或文档明确「开发模式长期记忆不持久」。

**验收**：重启服务后，PostgreSQL `store` 表中可见 `/memories/` 键；同一 `user_id` 跨两个 `thread_id` 能读到 Agent 上次写入的内容。

### 8.3 阶段二：DB ↔ Store 同步（P0）

**新增模块**（建议路径）：`backend/src/agent/memory/memory_sync.py`

```python
"""将 agent_files 表内容同步到 LangGraph Store。"""

from deepagents.backends.utils import create_file_data

# Agent-scoped 文件：全员共享的人设
AGENT_SCOPED_FILES = frozenset({
    "AGENTS.md", "SOUL.md", "IDENTITY.md", "TOOLS.md", "HEARTBEAT.md",
})
# User-scoped 文件：按用户隔离
USER_SCOPED_FILES = frozenset({"USER.md", "MEMORY.md"})


async def sync_agent_file_to_store(
    store,
    *,
    agent_id: str,
    user_id: str | None,
    filename: str,
    content: str,
) -> None:
    """根据文件名规则写入对应 namespace。"""
    path = f"/memories/{filename}"
    if filename in AGENT_SCOPED_FILES:
        namespace = (agent_id,)
    elif filename in USER_SCOPED_FILES:
        if not user_id:
            return  # 用户级文件需指定 user
        namespace = (agent_id, user_id)
    else:
        namespace = (agent_id, user_id) if user_id else (agent_id,)

    await store.aput(namespace, path, create_file_data(content))
```

**集成点：**

1. `save_agent_file()` 成功后调用 `sync_agent_file_to_store`
2. `init_graph()` 完成后增加 **bootstrap**：遍历主 Agent 的 `agent_files`，将 Agent-scoped 文件写入 Store
3. 用户首次对话前，可选 lazy 初始化空 `USER.md` / `MEMORY.md`

**调整 `AgentBuilder.with_backend()`**：

```python
routes={
    "/memories/": StoreBackend(
        namespace=lambda ctx: _memory_namespace(ctx, agent_id=self._agent_id),
    ),
    ...
}

def _memory_namespace(ctx, agent_id: str) -> tuple[str, ...]:
    user_id = ctx.runtime.context.user_id
    # 简化版：统一 (agent_id, user_id)；读取时 Store 按完整 path 区分文件
    return (agent_id, user_id)
```

更精细方案：为 Agent-scoped 与 User-scoped 配置 **不同路由前缀**（`/memories/agent/` vs `/memories/user/`），避免 namespace 逻辑复杂化。

**验收**：在 Agents 管理页编辑 `AGENTS.md` 保存后，新开会话 Agent 行为立即反映变更（无需重启 graph）。

### 8.4 阶段三：情节记忆工具（P1）

**步骤：**

1. 在 `agent_api.py` 创建 conversation 时，向 checkpointer/thread metadata 写入 `user_id`（若 LangGraph 支持 configurable metadata）。

2. 新增工具 `search_past_conversations`（`backend/src/agent/tools/conversation_search.py`）：

   ```python
   @tool
   async def search_past_conversations(
       query: str,
       runtime: ToolRuntime,
   ) -> str:
       """搜索当前用户的历史对话摘要。"""
       user_id = runtime.context.user_id  # ke-hermes Context 适配
       # 方案 A：查 conversations 表 + checkpointer.get_state
       # 方案 B：接入 langgraph_sdk（若部署 LangGraph Platform）
       ...
   ```

3. 将工具注册到主 Agent 工具列表（DB `agent_tools` 或代码注册）。

**验收**：用户在新会话问「我们上次讨论的方案是什么」，Agent 能调用工具检索并回答。

### 8.5 阶段四：后台 Consolidation（可选，P2）

ke-hermes 已有 `cron_jobs` 表，可：

1. 新增 `consolidation_agent` 图（或在 `target_type=agent` 的 Cron 触发主 Agent 专用 prompt）
2. 实现 `search_recent_conversations`（查 `conversations.updated_at` + checkpointer history）
3. 调度器：APScheduler / Celery / 独立 worker 读取 `cron_jobs` 表执行

**注意**：Cron 表达式 UTC；lookback 窗口与调度间隔对齐（官方建议）。

### 8.6 阶段五：组织策略与只读权限（P2）

1. `Context` 扩展 `org_id`（从 User 表或 JWT claims）
2. `CompositeBackend` 增加 `/policies/` → `StoreBackend(namespace=(org_id,))`
3. 管理 API 写入 policies；配置 StoreBackend 只读（待 deepagents 版本 permissions API 稳定后接入）

### 8.7 推荐实施顺序

| 优先级 | 任务 | 预估工作量 |
|--------|------|------------|
| P0 | PostgreSQL Store + 文件名统一 | 0.5 天 |
| P0 | agent_files → Store 同步 + bootstrap | 1–2 天 |
| P0 | namespace 引入 `agent_id` | 0.5 天 |
| P1 | search_past_conversations 工具 | 1 天 |
| P2 | Consolidation Agent + Cron 执行 | 2–3 天 |
| P2 | org policies 只读 | 1 天 |

### 8.8 配置清单

```env
# 长期记忆持久化（生产必开）
CHECKPOINT_BACKEND=postgres
CHECKPOINT_DB_URL=postgresql://...

# 可选：独立 Store（当前实现与 checkpoint 共用 PG 连接池）
STORE_BACKEND=postgres
STORE_DB_URL=postgresql://...

# 工作区（Skills 文件系统）
WORKSPACE=/path/to/backend/workspace
```

### 8.9 测试建议

```python
# tests/integration_tests/test_agent_memory.py 示意

async def test_memory_persists_across_threads(store, agent, user_id):
    ctx = Context(server_info="test", user_id=user_id)
    tid1 = str(uuid7())
    await agent.ainvoke(
        {"messages": [HumanMessage("请记住：我喜欢 Python")]},
        config={"configurable": {"thread_id": tid1}},
        context=ctx,
    )
    tid2 = str(uuid7())
    result = await agent.ainvoke(
        {"messages": [HumanMessage("我偏好什么语言？")]},
        config={"configurable": {"thread_id": tid2}},
        context=ctx,
    )
    assert "Python" in result["messages"][-1].content
```

---

## 9. 附录：关键 API 速查

### 9.1 create_deep_agent 记忆相关参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `memory` | `list[str]` | 启动加载的长期记忆虚拟路径 |
| `skills` | `list[str]` | 程序性记忆目录（通常按需加载） |
| `store` | LangGraph Store | 长期记忆存储后端 |
| `checkpointer` | Checkpointer | 短期/session 记忆 |
| `backend` | Backend / Callable | 文件路由与 namespace |
| `context_schema` | dataclass | 运行时上下文（user_id、org_id 等） |

### 9.2 Backend 组件

| 类 | 用途 |
|----|------|
| `StateBackend` | 会话内临时文件（不跨 thread 持久） |
| `StoreBackend` | 长期记忆；`namespace` 控制隔离 |
| `CompositeBackend` | 按路径前缀路由到不同 Backend |
| `FilesystemBackend` | 本地磁盘（ke-hermes Skills） |

### 9.3 Store 写入

```python
from deepagents.backends.utils import create_file_data

# 同步
store.put((namespace_tuple), "/memories/FILE.md", create_file_data("content"))

# 异步（AsyncPostgresStore）
await store.aput((namespace_tuple), "/memories/FILE.md", create_file_data("content"))
```

### 9.4 ke-hermes 相关源文件索引

| 文件 | 职责 |
|------|------|
| `src/agent/graph.py` | Store / Checkpointer 初始化 |
| `src/agent/builders/agent_builder.py` | memory 路径、CompositeBackend |
| `src/agent/context/context.py` | user_id 上下文 |
| `src/api/agent/agent_api.py` | 对话 API、thread_id |
| `src/api/agents/service.py` | Agent 文件 CRUD、DEFAULT_AGENT_FILES |
| `src/db/models/agent_file.py` | 记忆文件 DB 模型 |
| `docs/Ke-Hermes-数据库详细设计说明书.md` | Store 表结构说明 |

---

## 参考链接

- [DeepAgents Memory 官方文档](https://docs.langchain.com/oss/python/deepagents/memory)
- [DeepAgents Context Engineering（短期记忆）](https://docs.langchain.com/oss/python/deepagents/context-engineering)
- [LangGraph Store 文档](https://langchain-ai.github.io/langgraph/concepts/persistence/#store)
- [ke-hermes Agent 模块设计](./Ke-Hermes-Agent-功能模块详细设计说明书-1.0.0.md)
- [ke-hermes 数据库设计 - Store 章节](./Ke-Hermes-数据库详细设计说明书.md)
