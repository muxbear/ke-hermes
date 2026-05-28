# Ke-Hermes Agent 功能模块详细设计说明书 v1.0.0

## Context

前端 "代理" 页面（`/agents`）已实现完整的功能和交互，但后端尚无对应的 Agent 管理 API —— 目前前端使用 `agentApi.ts` 中的 mock 实现（内存数组 + 200ms 模拟延迟）。需要开发真实的后端逻辑和接口来替换 mock，同时保证前端 Vue 组件代码无需改动。

## 1. 数据库设计

### 1.1 新建 `agents` 表

新建文件 `backend/src/db/models/agent.py`：

| 列名 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `id` | String(36) PK | `uuid4()` | 主键 |
| `name` | String(128) | — | 代理名称 |
| `type` | String(16) | `"sub"` | `main` 或 `sub` |
| `status` | String(16) | `"inactive"` | `active` / `inactive` / `error` |
| `description` | Text | `""` | 描述 |
| `parent_id` | String(36) nullable, index | `None` | 父代理 ID（NULL = 主代理） |
| `user_id` | String(36) index | — | 所属用户 ID |
| `tools` | JSON | `[]` | 工具名称列表 |
| `skills` | JSON | `[]` | 技能名称列表 |
| `prompts` | JSON | `[]` | 提示词/Cron Job 列表 |
| `files` | JSON | `[]` | 文件名称列表 |
| `undeletable` | Boolean | `False` | 是否不可删除 |
| `created_at` | DateTime | `func.now()` | 创建时间 |
| `updated_at` | DateTime | `func.now()` onupdate | 更新时间 |

**设计决策：**
- 配置项（tools/skills/prompts/files）使用 JSON 列存储在 agent 行内，避免额外关联表，与现有 `McpTool.tags`/`McpTool.features` 模式一致
- `parent_id` 实现层级关系：NULL=主代理，非NULL=子代理；`subAgents` 由查询动态计算
- `user_id` 实现多用户数据隔离
- `callCount` / `lastActive` 不在 DB 中存储（运行时指标），API 响应中设为占位值 0/null
- 使用 `sqlalchemy.dialects.sqlite.JSON` 兼容双数据库后端
- 无数据库级外键约束（兼容 SQLite）

### 1.2 注册模型

修改 `backend/src/db/models/__init__.py`：添加 `Agent` 导入和 `__all__` 导出。

## 2. 后端接口设计

所有接口前缀 `/api/agents`，需 JWT 认证。

### 2.1 `GET /api/agents` — 获取代理列表

**响应：** `ApiResponse[AgentListResponse]`
```json
{
  "code": 0,
  "data": {
    "agents": [{
      "id": "uuid",
      "name": "主智能体",
      "type": "main",
      "status": "active",
      "description": "...",
      "tools": ["web_search"],
      "skills": ["code_analysis"],
      "prompts": ["每小时检查"],
      "files": ["AGENTS.md"],
      "sub_agents": ["sub-uuid-1"],
      "parent_id": null,
      "last_active": null,
      "call_count": 0,
      "undeletable": true,
      "created_at": "2026-05-28T...",
      "updated_at": "2026-05-28T..."
    }]
  }
}
```

### 2.2 `GET /api/agents/{agent_id}` — 获取单个代理

响应格式同上，返回单个 `AgentInfo`。

### 2.3 `POST /api/agents` — 创建代理

**请求体：**
```json
{
  "name": "新代理",
  "description": "描述（可选）",
  "parent_id": "父代理ID（可选，不传则创建主代理）"
}
```
**响应：** `ApiResponse[AgentInfo]`

**逻辑：**
- 不传 `parent_id`：创建主代理，检查用户是否已有主代理（有则 409）
- 传 `parent_id`：创建子代理，验证父代理存在且属于同一用户（否则 404）
- 初始状态：`status="inactive"`, 空配置列表, `undeletable=false`

### 2.4 `DELETE /api/agents/{agent_id}` — 删除代理

**响应：** `ApiResponse[None]`

**逻辑：**
- 未找到 → 404
- `undeletable=true` → 403
- 主代理：级联删除其所有子代理
- 子代理：仅删除自身

### 2.5 `PATCH /api/agents/{agent_id}/status` — 切换状态

无请求体。状态循环：`active` ↔ `inactive`，`error` → `inactive`。

**响应：** `ApiResponse[AgentInfo]`

### 2.6 `POST /api/agents/{agent_id}/clone` — 克隆代理

无请求体。深拷贝代理配置，名称为 `"{原名} (副本)"`，状态 `inactive`。

**响应：** `ApiResponse[AgentInfo]`

### 2.7 `POST /api/agents/{agent_id}/config` — 添加配置项

**请求体：**
```json
{
  "type": "tool|skill|prompt|file|subagent",
  "value": "配置名称或子代理ID"
}
```

**逻辑：**
- `type=subagent`：验证目标为 main 类型，创建新子代理
- 其他类型：追加到对应 JSON 数组（去重）
- **响应：** `ApiResponse[AgentInfo]`

### 2.8 `DELETE /api/agents/{agent_id}/config` — 移除配置项

**请求体：** 同添加（`{type, value}`）

**逻辑：**
- `type=subagent`：删除 value 对应的子代理（value 为子代理 ID）
- 其他类型：从对应 JSON 数组中移除
- **响应：** `ApiResponse[AgentInfo]`

## 3. 后端逻辑设计

### 3.1 文件结构（新增 4 个文件）

```
backend/src/
├── db/models/agent.py          # ORM 模型
├── api/agents/
│   ├── __init__.py             # 导出 router
│   ├── schemas.py              # Pydantic 请求/响应模型
│   ├── service.py              # 业务逻辑层
│   └── agents_api.py           # FastAPI 路由定义
```

### 3.2 需修改的现有文件（3 个）

| 文件 | 修改内容 |
|------|----------|
| `backend/src/db/models/__init__.py` | 注册 `Agent` 模型 |
| `backend/src/api/__init__.py` | 引入并挂载 `agents_router` |
| `frontend/src/services/agentApi.ts` | 替换 mock 为真实 HTTP 调用 |

### 3.3 服务层函数签名

```python
# backend/src/api/agents/service.py

async def list_agents(db: AsyncSession, user_id: str) -> AgentListResponse
async def get_agent(db: AsyncSession, agent_id: str, user_id: str) -> AgentInfo
async def create_agent(db: AsyncSession, req: AgentCreateRequest, user_id: str) -> AgentInfo
async def delete_agent(db: AsyncSession, agent_id: str, user_id: str) -> None
async def toggle_agent_status(db: AsyncSession, agent_id: str, user_id: str) -> AgentInfo
async def clone_agent(db: AsyncSession, agent_id: str, user_id: str) -> AgentInfo
async def add_agent_config(db: AsyncSession, agent_id: str, req: AgentConfigRequest, user_id: str) -> AgentInfo
async def remove_agent_config(db: AsyncSession, agent_id: str, req: AgentConfigRequest, user_id: str) -> AgentInfo
```

### 3.4 关键业务逻辑

**获取列表：** 查询用户所有 agent → 每个 agent 动态计算 `sub_agents`（查 `parent_id == agent.id` 的 ID 列表）

**创建代理：** 校验名称唯一性（同用户下）→ 判断 main/sub → main 检查唯一性 → INSERT

**删除代理：** 404/403 守卫 → main 则先级联删子代理 → DELETE

**状态切换：** active→inactive, inactive→active, error→inactive

**克隆：** 深拷贝字段 → 名称去重（"(副本)" / "(副本 N)"）→ status=inactive → INSERT

**配置管理：** 映射 type 到 JSON 列名 → subagent 特殊处理 → Python 侧 JSON 读写（避免数据库级 JSON 函数，兼容 SQLite/PG）

### 3.5 启动种子数据

在 `server.py` 的 lifespan 中：如果用户尚无主代理，创建默认主代理（`name="主智能体"`, `type="main"`, `undeletable=true`），含默认 files/tools/skills。确保前端代理页面登录后非空。

## 4. 前后端联调设计

### 4.1 字段名映射

后端遵循 snake_case 命名，前端 TypeScript 使用 camelCase。在 `agentApi.ts` 中加转换层：

| 后端字段 (JSON) | 前端字段 (TypeScript) |
|-----------------|----------------------|
| `parent_id` | `parentId` |
| `sub_agents` | `subAgents` |
| `last_active` | `lastActive` |
| `call_count` | `callCount` |
| `created_at` | — (前端不使用) |
| `updated_at` | — (前端不使用) |

### 4.2 前端 `agentApi.ts` 改造

文件：`frontend/src/services/agentApi.ts`

- 删除所有 mock 数据和 `delay()` 函数
- 导入项目现有的 axios 实例（`@/services/request`）
- 每个函数改为真实 HTTP 调用，内部做 snake_case ↔ camelCase 转换
- 函数签名不变，Vue 组件和 Store 代码零改动

示例转换函数：
```typescript
function toAgent(raw: Record<string, any>): Agent {
  return {
    ...raw,
    parentId: raw.parent_id ?? undefined,
    subAgents: raw.sub_agents ?? [],
    lastActive: raw.last_active ?? undefined,
    callCount: raw.call_count ?? 0,
  }
}
```

### 4.3 API 契约对照

| 前端调用 | HTTP 方法 | 后端路径 | 请求体 |
|----------|-----------|----------|--------|
| `fetchAgents()` | GET | `/api/agents` | — |
| `createAgent(data)` | POST | `/api/agents` | `{name, description?}` |
| `deleteAgent(id)` | DELETE | `/api/agents/{id}` | — |
| `toggleAgentStatus(id)` | PATCH | `/api/agents/{id}/status` | — |
| `cloneAgent(id)` | POST | `/api/agents/{id}/clone` | — |
| `addConfig(id, type, value)` | POST | `/api/agents/{id}/config` | `{type, value}` |
| `removeConfig(id, type, value)` | DELETE | `/api/agents/{id}/config` | `{type, value}` |

## 5. 测试设计

### 5.1 单元测试 (`tests/unit_tests/test_agent_service.py`)

使用内存 SQLite 测试服务层所有函数，覆盖：

- 创建主代理（含重复创建 → 409）
- 创建子代理（含不存在的父代理 → 404）
- 列表查询含正确 sub_agents 计算
- 删除代理（含 undeletable → 403，主代理级联删除）
- 状态切换三种状态循环
- 克隆含名称去重
- 配置添加/移除（含 subagent 类型、去重）
- 名称唯一性校验

### 5.2 集成测试 (`tests/tests/integration_tests/test_agents_api.py`)

使用现有 `client` fixture 测试完整 HTTP 链路：

- 未认证请求 → 401
- 完整 CRUD 生命周期（创建→列表→查看→状态切换→克隆→配置管理→删除）
- 边界条件（不存在的 ID → 404，无效请求体 → 422）

## 6. 实现顺序

| 阶段 | 文件 | 内容 |
|------|------|------|
| **Phase 1** | `db/models/agent.py` | ORM 模型 |
| | `db/models/__init__.py` | 注册模型 |
| | `api/agents/schemas.py` | Pydantic schemas |
| **Phase 2** | `api/agents/service.py` | 完整业务逻辑 |
| | `api/agents/__init__.py` | 导出 router |
| | `api/agents/agents_api.py` | 路由定义 |
| | `api/__init__.py` | 挂载 router |
| **Phase 3** | `server.py` | 启动种子数据 |
| | `frontend/src/services/agentApi.ts` | 替换 mock 为真实调用 |
| **Phase 4** | `tests/unit_tests/test_agent_service.py` | 单元测试 |
| | `tests/integration_tests/test_agents_api.py` | 集成测试 |

## 7. 与现有 DeepAgents 运行时的关系

- **DB `agents` 表**：存储代理的**声明式元数据**（配置、状态、层级关系）
- **`agent/graph.py` 运行时**：DeepAgents/LangGraph 执行引擎（当前硬编码 main-agent + research-agent）
- **当前阶段**：两者独立运作。DB 管理前端可见的代理配置；运行时继续使用硬编码图
- **未来迭代**：运行时可从 DB 动态读取配置，按需构建 subagent 图（如 toggle 激活/停用子代理）

## 8. 验证方案

1. 启动后端：`cd backend && uv run python run.py`，确认 `/docs` Swagger 中出现 `/api/agents` 路由组
2. 启动前端：`cd frontend && npm run dev`，登录后进入 `/agents` 页面，确认能加载和操作代理
3. 运行测试：`cd backend && uv run pytest tests/unit_tests/test_agent_service.py tests/integration_tests/test_agents_api.py -v`
4. 手动验证关键场景：
   - 创建子代理 → 左侧树中出现新节点
   - 切换状态 → 状态标签变化
   - 添加/删除配置 → 详情面板标签变化
   - 关系图谱 → 正确展示主-子关系连线
