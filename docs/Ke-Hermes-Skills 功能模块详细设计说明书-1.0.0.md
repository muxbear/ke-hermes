# Ke-Hermes Skills 功能模块详细设计说明书

**版本**: 1.0.0  
**状态**: 待实现  
**日期**: 2026-05-26

---

## 1. 概述

### 1.1 背景

ke-hermes 是一个基于 DeepAgents (LangGraph) 的通用智能体服务平台。Skills（技能）模块为用户提供可配置的 AI 智能体能力扩展机制——每个 Skill 定义一种特定行为或工具能力（如网络搜索、代码执行、图像生成等），用户可按需启用/禁用，也可创建自定义技能。

### 1.2 现状分析

| 位置 | 现状 |
|------|------|
| `frontend/src/components/SideMenu.vue:32` | 已有 "Skills" 菜单项占位，无路由跳转 |
| `backend/src/agent/graph.py:94` | 注释掉的 `# skills=["/skills/"]` 参数（DeepAgents 文件系统技能） |
| 数据库 / API / 页面 | 均无技能相关代码 |

### 1.3 目标

1. 后端提供完整的 Skills CRUD API + 数据库持久化
2. 前端提供技能管理页面，支持查看/创建/编辑/删除/启停
3. 预置 5 个内置技能作为系统默认能力
4. 为后续与 DeepAgents 技能系统集成预留接口

### 1.4 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI + Pydantic |
| ORM | SQLAlchemy 2.0 async |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 前端框架 | Vue 3 Composition API + TypeScript |
| UI 组件库 | Element Plus 2.x (自动导入) |
| 图标 | lucide-vue-next |
| 状态管理 | Pinia (Composition API 风格) |
| HTTP | Axios (统一拦截器) |

---

## 2. 系统架构

### 2.1 整体分层

```
┌─────────────────────────────────────────────┐
│                   Frontend                  │
│  SkillsView → SkillCard / SkillDialog       │
│  useSkillStore → skillApi → Axios           │
├─────────────────────────────────────────────┤
│           HTTP REST (/api/skills)            │
├─────────────────────────────────────────────┤
│                   Backend                   │
│  skill_api.py (routes) → skill/service.py   │
│  Skill ORM Model (db/models/skill.py)       │
├─────────────────────────────────────────────┤
│         SQLite / PostgreSQL                 │
└─────────────────────────────────────────────┘
```

### 2.2 目录规划

```
backend/src/
├── api/
│   ├── __init__.py          ← 修改: 注册 skill_router
│   └── skill/               ← 新建
│       ├── __init__.py
│       ├── skill_api.py      # API 路由
│       ├── schemas.py        # Pydantic 模型
│       └── service.py       # 业务逻辑 + 种子数据
├── db/models/
│   ├── __init__.py          ← 修改: 导出 Skill
│   └── skill.py             ← 新建: Skill ORM 模型
└── server.py                ← 修改: 种子数据调用

frontend/src/
├── components/
│   └── skill/               ← 新建
│       ├── SkillCard.vue     # 技能卡片组件
│       ├── SkillDialog.vue   # 创建/编辑对话框
│       └── iconMap.ts        # 图标映射
├── views/
│   └── SkillsView.vue       ← 新建: 技能管理页面
├── stores/
│   └── skill.ts             ← 新建: 技能状态管理
├── services/
│   └── skillApi.ts          ← 新建: 技能 API 调用
├── types/
│   └── skill.ts             ← 新建: 类型定义
├── router/
│   └── index.ts             ← 修改: 添加 /skills 路由
└── components/
    └── SideMenu.vue         ← 修改: Skills 菜单联动
```

---

## 3. 数据库设计

### 3.1 Skills 表结构

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `String(36)` | PK, UUID | 主键，自动生成 |
| `name` | `String(64)` | unique, not null | 技能名称 |
| `description` | `String(512)` | default "" | 简短描述 |
| `icon` | `String(64)` | default "Zap" | Lucide 图标名称 |
| `category` | `String(64)` | default "custom" | 分类标识 |
| `prompt` | `Text` | default "" | 技能系统提示词 |
| `enabled` | `Boolean` | default True | 是否启用 |
| `is_builtin` | `Boolean` | default False | 是否内置技能 |
| `user_id` | `String(36)` | nullable | 所有者 (内置=null) |
| `created_at` | `DateTime` | server_default | 创建时间 |
| `updated_at` | `DateTime` | onupdate | 更新时间 |

### 3.2 索引策略

- `name` 唯一索引（保证名称唯一性）
- `(user_id, category)` 复合索引（按用户+分类查询）
- `is_builtin` 索引（快速筛选内置技能）

### 3.3 内置种子数据

系统预置 5 个内置技能，首次启动时通过 `seed_builtin_skills()` 自动创建：

| 名称 | 图标 | 分类 | 说明 |
|------|------|------|------|
| 网络搜索 | Globe | search | 实时搜索互联网信息，获取最新数据 |
| 代码解释器 | Code2 | code | 在安全沙箱中执行代码，支持数据分析 |
| 图像生成 | Image | creative | 根据文本描述生成高质量图像 |
| 数据分析 | ChartBar | analysis | 处理结构化数据，生成统计报告和图表 |
| 文件管理 | FolderOpen | tools | 读写多种格式文件，支持批量处理 |

**分类枚举**: `search` / `code` / `creative` / `analysis` / `tools` / `custom`

### 3.4 SQLAlchemy 模型定义

```python
# backend/src/db/models/skill.py

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(512), default="")
    icon: Mapped[str] = mapped_column(String(64), default="Zap")
    category: Mapped[str] = mapped_column(String(64), default="custom")
    prompt: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
```

---

## 4. 后端 API 设计

### 4.1 通用约定

- **Base URL**: `/api`
- **响应格式**: `ApiResponse<T>` 统一包装
  ```json
  { "code": 0, "data": {...}, "message": "ok", "requestId": "...", "timestamp": ... }
  ```
- **认证**: 所有接口需 `Authorization: Bearer <JWT>` 头
- **权限规则**: 内置技能全员可见但不可修改/删除；自定义技能仅所有者可修改/删除
- **错误码**:
  - `404` 技能不存在
  - `403` 无权操作（非所有者操作自定义技能 / 尝试修改内置技能）
  - `400` 参数校验失败

### 4.2 接口列表

#### 4.2.1 获取技能列表

```
GET /api/skills?category=search
```

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "uuid-1",
      "name": "网络搜索",
      "description": "让 AI 智能体能够实时搜索互联网信息",
      "icon": "Globe",
      "category": "search",
      "prompt": "You can search the web to find current information...",
      "enabled": true,
      "is_builtin": true,
      "user_id": null,
      "created_at": "2026-05-26T10:00:00",
      "updated_at": "2026-05-26T10:00:00"
    }
  ]
}
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `category` | string | 否 | 按分类筛选 |

**逻辑**: 返回所有 `is_builtin=true` 的技能 + 当前用户创建的自定义技能

#### 4.2.2 创建技能

```
POST /api/skills
```

**请求体**:
```json
{
  "name": "多语言翻译",
  "description": "支持 50+ 语言的精准翻译",
  "icon": "Languages",
  "category": "custom",
  "prompt": "You are a professional translator..."
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | **是** | - | 技能名称（最长 64 字符） |
| `description` | string | 否 | "" | 描述（最长 512 字符） |
| `icon` | string | 否 | "Zap" | 图标名称 |
| `category` | string | 否 | "custom" | 分类 |
| `prompt` | string | 否 | "" | 提示词 |

**逻辑**: 创建 `is_builtin=false`, `user_id=当前用户` 的技能

#### 4.2.3 获取技能详情

```
GET /api/skills/{skill_id}
```

#### 4.2.4 更新技能

```
PUT /api/skills/{skill_id}
```

**请求体**: 同创建，但所有字段可选（部分更新）

**权限**: 内置技能返回 403；非所有者返回 403

#### 4.2.5 删除技能

```
DELETE /api/skills/{skill_id}
```

**权限**: 内置技能返回 403；非所有者返回 403

#### 4.2.6 切换启用状态

```
PATCH /api/skills/{skill_id}/toggle
```

**请求体**:
```json
{ "enabled": false }
```

### 4.3 依赖注入

所有接口使用以下依赖：

- `get_current_user_id(request)` → `str`: 从 JWT 解析用户 ID
- `get_db()` → `AsyncSession`: 异步数据库会话

### 4.4 路由注册

```python
# backend/src/api/skill/__init__.py
from api.skill.skill_api import router
__all__ = ["router"]

# backend/src/api/__init__.py (追加)
from api.skill import router as skill_router
router.include_router(skill_router)
```

### 4.5 种子数据调用

在 `server.py` 的 lifespan 中 `init_db()` 之后调用：

```python
from api.skill.service import seed_builtin_skills
async for db in get_db():
    await seed_builtin_skills(db)
    break
```

---

## 5. 前端设计

### 5.1 页面路由

| 路径 | 名称 | 组件 | 权限 |
|------|------|------|------|
| `/skills` | `skills` | `SkillsView.vue` | `requiresAuth` |

### 5.2 页面布局

```
┌──────────┬──────────────────────────────────────────────┐
│ SideMenu │  Skills                [+ 创建技能]           │
│ (复用)   │  管理和配置 AI 智能体的技能与工具能力          │
│          ├──────────────────────────────────────────────┤
│ 聊天     │ [全部] [搜索] [代码] [创意] [分析] [工具]     │
│  对话    ├──────────────┬──────────────┬─────────────────┤
│          │ Skill Card 1 │ Skill Card 2 │ Skill Card 3    │
│ 代理     ├──────────────┼──────────────┼─────────────────┤
│  代理列表 │ Skill Card 4 │ Skill Card 5 │ Skill Card 6    │
│ ▶Skills  │              │              │                 │
│          └──────────────┴──────────────┴─────────────────┘
└──────────┴──────────────────────────────────────────────┘
```

- 左侧复用现有 `SideMenu.vue` 组件
- 主内容区包含：页面标题、分类筛选、技能卡片网格
- 右侧历史面板不显示（Skills 页面属于独立管理页，非聊天场景）

### 5.3 组件树

```
SkillsView.vue
├── SideMenu.vue                          (复用)
├── 页面标题行
│   ├── 标题 "Skills" + 描述文字
│   └── el-button "创建技能" [type=primary]
├── 分类标签栏 (el-tabs / 按钮组)
├── 技能卡片网格
│   └── SkillCard.vue × N
│       ├── 图标 (动态 lucide 组件)
│       ├── 技能名称 + "内置" 标签
│       ├── el-switch (启用/禁用)
│       ├── 描述文字
│       └── 分类标签 + 编辑/删除按钮
├── SkillDialog.vue (条件渲染)
│   └── el-dialog + el-form
└── 删除确认 (el-message-box)
```

### 5.4 SkillCard.vue 设计

**Props**:
```typescript
defineProps<{ skill: Skill }>()
```

**Emits**:
```typescript
defineEmits<{
  (e: 'edit', skill: Skill): void
  (e: 'delete', skill: Skill): void
  (e: 'toggle', skill: Skill): void
}>()
```

**视觉规格**:

| 属性 | 值 |
|------|-----|
| 背景 | `var(--surface-card)` (深色半透明) |
| 边框 | `1px solid var(--border-subtle)` |
| 圆角 | `var(--radius-xl)` (12px) |
| 内间距 | 20px |
| 卡片内垂直间距 | 14px |

**卡片结构**:
```
┌─────────────────────────────────────┐
│ [图标圆角框]  技能名称  [内置]   [开关] │  ← header
│                                     │
│ 技能描述文字...                       │  ← description
│                                     │
│ [分类标签]                   [编辑][删除]│  ← footer
└─────────────────────────────────────┘
```

- **图标圆角框**: 36×36, `border-radius: 10px`, 背景 `var(--accent-primary-light)`, 居中渲染 lucide 图标 (18×18)
- **内置标签**: 小号 `el-tag`, type="info", 仅 `is_builtin=true` 时显示
- **开关**: `el-switch`, 控制启用/禁用状态
- **编辑/删除**: `el-button text`, 仅自定义技能显示

### 5.5 SkillDialog.vue 设计

**Props**:
```typescript
defineProps<{
  visible: boolean
  skill: Skill | null  // null=创建模式, Skill=编辑模式
}>()
```

**Emits**:
```typescript
defineEmits<{
  (e: 'close'): void
  (e: 'save', data: SkillCreateRequest): void
}>()
```

**表单字段**:

| 字段 | 组件 | 验证 |
|------|------|------|
| 名称 | `el-input` | 必填，最长 64 字符 |
| 描述 | `el-input type=textarea` (3行) | 最长 512 字符 |
| 图标 | `el-input` | 默认 "Zap" |
| 分类 | `el-input` | 默认 "custom" |
| 提示词 | `el-input type=textarea` (6行) | - |

### 5.6 图标映射 (iconMap.ts)

```typescript
import {
  Globe, Code2, Image, ChartBar, FolderOpen,
  Zap, Search, FileText, Database, Palette, Music, Wrench
} from 'lucide-vue-next'
import type { Component } from 'vue'

export const SKILL_ICONS: Record<string, Component> = {
  Globe, Code2, Image, ChartBar, FolderOpen, Zap,
  Search, FileText, Database, Palette, Music, Wrench,
}

export function getSkillIcon(iconName: string): Component {
  return SKILL_ICONS[iconName] || Zap
}
```

### 5.7 SkillsView.vue 状态处理

| 状态 | 展示 |
|------|------|
| 加载中 | `v-loading` 指令 + `el-skeleton` 卡片占位 |
| 空数据 | `el-empty description="暂无技能"` |
| 接口错误 | `el-alert type="error"` 显示错误信息 |
| 正常 | 分类标签 + 卡片网格 |

### 5.8 SideMenu.vue 修改

```typescript
// 新增导入
import { useRouter, useRoute } from 'vue-router'
const router = useRouter()
const route = useRoute()

// 菜单数据结构变更：添加 route 字段
const menuGroups = [
  {
    label: '聊天',
    items: [
      { icon: MessageSquare, text: '对话', route: '/' },
    ],
  },
  {
    label: '代理',
    items: [
      { icon: Bot, text: '代理列表', route: null },
      { icon: Zap, text: 'Skills', route: '/skills' },
    ],
  },
  // ...
]
```

```html
<!-- 模板：动态 active + 点击导航 -->
<div
  v-for="item in group.items"
  :key="item.text"
  class="menu-item"
  :class="{ active: item.route && route.path === item.route }"
  @click="item.route && router.push(item.route)"
>
```

### 5.9 样式策略

- 复用现有 `variables.css` 中的设计 Token
- 组件使用 `<style scoped>` + CSS 变量
- 网格使用 CSS Grid：

```css
.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
```

---

## 6. 数据流设计

### 6.1 技能列表加载

```
SkillsView.onMounted()
  → useSkillStore.loadSkills()
    → skillApi.fetchSkills()
      → GET /api/skills
        → skill_service.list_skills(db, user_id)
          → SELECT * FROM skills WHERE is_builtin OR user_id = ?
    ← ApiResponse<Skill[]>
  ← skills 更新 (ref)
← 模板响应式渲染
```

### 6.2 创建技能

```
SkillDialog.save()
  → SkillsView.handleCreate(data)
    → useSkillStore.addSkill(data)
      → skillApi.createSkill(data)
        → POST /api/skills
          → skill_service.create_skill(db, user_id, req)
            → INSERT INTO skills (name, ..., user_id) VALUES (...)
    ← ApiResponse<Skill>
  ← 关闭对话框, 刷新列表
```

### 6.3 切换启用/禁用

```
SkillCard.toggle()
  → SkillsView.handleToggle(skill)
    → useSkillStore.toggleSkill(id, enabled)
      → skillApi.toggleSkill(id, enabled)
        → PATCH /api/skills/{id}/toggle
    ← 乐观更新本地状态
```

### 6.4 删除技能

```
SkillCard.delete()
  → SkillsView.handleDelete(skill)
    → el-message-box.confirm("确认删除?")
      → useSkillStore.removeSkill(id)
        → skillApi.deleteSkill(id)
          → DELETE /api/skills/{id}
    ← 从列表中移除
```

---

## 7. 权限模型

| 操作 | 内置技能 | 他人的自定义技能 | 自己的自定义技能 |
|------|----------|------------------|------------------|
| 查看 | ✓ | ✓ | ✓ |
| 创建 | - | - | ✓ |
| 编辑 | ✗ (403) | ✗ (403) | ✓ |
| 删除 | ✗ (403) | ✗ (403) | ✓ |
| 切换启用 | ✓ | ✗ (403) | ✓ |

---

## 8. 交互流程

### 8.1 创建技能流程

```
1. 用户点击 [创建技能] → SkillDialog 打开 (visible=true, skill=null)
2. 填写表单 → 点击 [创建]
3. 前端校验 → API 调用 → 成功
4. ElMessage.success("技能创建成功") → 关闭对话框 → 列表刷新
5. 失败: ElMessage.error(错误信息) → 对话框保持打开
```

### 8.2 编辑技能流程

```
1. 用户点击卡片 [编辑] → SkillDialog 打开 (visible=true, skill=当前技能)
2. 表单回填 → 修改 → 点击 [保存]
3. API 调用 → 成功 → ElMessage → 列表刷新
```

### 8.3 删除技能流程

```
1. 用户点击卡片 [删除]
2. el-message-box 确认弹窗
3. 确认 → API 调用 → 成功 → 卡片移除
```

---

## 9. 后续规划 (v1.1+)

### 9.1 DeepAgents 集成

当前 `agent/graph.py` 中 `skills=["/skills/"]` 参数被注释，后续可将数据库中的已启用技能导出到文件系统目录，或直接通过 DeepAgents 配置注入，使技能提示词在对话中生效。

### 9.2 技能市场

后续可支持技能分享/导入/导出功能，形成技能市场生态。

### 9.3 技能参数化

支持为技能定义输入参数 schema，让用户在使用技能时提供自定义参数。

---

## 10. 附录

### A. Pencil 设计稿

设计稿文件: `D:/work/PencilProjects/ke-hermes/ke-hermes-skills.pen`

包含两个主节点：
- **Skills Page** (MGoLB): 完整页面设计（侧边栏 + 标题 + 分类标签 + 3×2 卡片网格）
- **Skill Card Component** (g3UG12): 可复用的技能卡片组件

### B. 变更文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/src/db/models/skill.py` | **新建** | Skill ORM 模型 |
| `backend/src/db/models/__init__.py` | 修改 | 导出 Skill |
| `backend/src/api/skill/__init__.py` | **新建** | 模块导出 |
| `backend/src/api/skill/schemas.py` | **新建** | Pydantic 模型 |
| `backend/src/api/skill/service.py` | **新建** | 业务逻辑 + 种子数据 |
| `backend/src/api/skill/skill_api.py` | **新建** | API 路由 |
| `backend/src/api/__init__.py` | 修改 | 注册路由 |
| `backend/src/server.py` | 修改 | 种子数据调用 |
| `frontend/src/types/skill.ts` | **新建** | 类型定义 |
| `frontend/src/services/skillApi.ts` | **新建** | API 服务 |
| `frontend/src/stores/skill.ts` | **新建** | Pinia Store |
| `frontend/src/components/skill/iconMap.ts` | **新建** | 图标映射 |
| `frontend/src/components/skill/SkillCard.vue` | **新建** | 技能卡片 |
| `frontend/src/components/skill/SkillDialog.vue` | **新建** | 编辑对话框 |
| `frontend/src/views/SkillsView.vue` | **新建** | 技能管理页面 |
| `frontend/src/router/index.ts` | 修改 | 添加路由 |
| `frontend/src/components/SideMenu.vue` | 修改 | Skills 菜单联动 |

### C. 参考文件

- 后端 API 模式参考: `backend/src/api/conversation/conversation_api.py`
- 后端 Service 模式参考: `backend/src/api/auth/service.py`
- 前端 Store 模式参考: `frontend/src/stores/ui.ts`
- 前端 API 模式参考: `frontend/src/services/conversationApi.ts`
- 前端全局样式: `frontend/src/assets/styles/variables.css`
