# Ke-Hermes 前端详细设计说明书 — Skills 模块（桌面版）v1.0.1

| 版本    | 日期         | 作者  | 变更说明                           |
| ----- | ---------- | --- | ------------------------------ |
| 1.0.0 | 2026-05-26 | -   | Skills 模块前端详细设计初版，基于后端设计说明书 v1.0.0 |
| 1.0.1 | 2026-05-26 | -   | 对照实际代码实现更新：页面布局重构、SkillDialog 自定义模态框、下拉菜单逻辑、统一下载面板 |

---

## 目录

1. [概述](#1-概述)
2. [页面架构](#2-页面架构)
3. [路由设计](#3-路由设计)
4. [组件设计](#4-组件设计)
5. [状态管理设计](#5-状态管理设计)
6. [类型定义](#6-类型定义)
7. [API 服务层设计](#7-api-服务层设计)
8. [样式设计](#8-样式设计)
9. [交互流程](#9-交互流程)
10. [权限控制（前端侧）](#10-权限控制前端侧)
11. [测试设计](#11-测试设计)
12. [附录](#12-附录)

---

## 1. 概述

### 1.1 文档目的

本文档为 Ke-Hermes Skills 模块的**前端**详细设计说明书，基于《Ke-Hermes Skills 功能模块详细设计说明书-1.0.0》编写。**本文档与实际代码实现保持一致**（v1.0.1），供前端开发人员编码实现、代码审查和后期维护使用。

### 1.2 模块背景

Skills（技能）模块为用户提供可配置的 AI 智能体能力扩展机制。每个 Skill 定义一种特定行为或工具能力（如网络搜索、代码执行、图像生成等），用户可按需启用/禁用，也可创建自定义技能。系统预置 5 个内置技能。

### 1.3 技术选型

| 类别       | 选型                   | 版本     |
| -------- | -------------------- | ------ |
| 框架       | Vue 3                | ^3.5   |
| 类型系统     | TypeScript           | ~5.5   |
| 路由       | Vue Router           | ^4.4   |
| 状态管理     | Pinia                | ^2.2   |
| 构建工具     | Vite                 | ^5.4   |
| UI 组件库   | Element Plus         | ^2.8   |
| HTTP 客户端 | Axios                | ^1.7   |
| CSS 方案   | SCSS + CSS Variables | -      |
| 图标       | lucide-vue-next      | ^0.400 |

### 1.4 相关文档

- [Ke-Hermes Skills 功能模块详细设计说明书-1.0.0](../../../docs/Ke-Hermes-Skills%20功能模块详细设计说明书-1.0.0.md)
- [Ke-Hermes 前端详细设计说明书-1.2.2](./Ke%20Hermes-前端详细设计说明书-1.2.2.md)

---

## 2. 页面架构

### 2.1 整体布局结构

Skills 页面不是独立的全屏页面，而是嵌套在 `MainLayout` 共享布局中。SideMenu 和 TopBar 由 MainLayout 统一管理，所有需认证的二级页面（聊天、Skills）共享。

```
MainLayout (100vh flex row)
├── SideMenu (220px, 共享)
└── right-area (flex:1, column)
    ├── TopBar (52px, 共享 — 搜索/通知/用户菜单)
    └── work-area (flex:1)
        └── <RouterView />
            ├── /       → HomeView → AppShell (ChatMain + RightPanel)
            └── /skills → SkillsView (技能管理页)
```

**SkillsView 使用 `height: 100%`** 自适应 work-area 高度，无独立滚动条。

### 2.2 目录规划

```
frontend/src/
├── types/
│   └── skill.ts                  ← 新建: 技能类型定义
├── services/
│   └── skillApi.ts               ← 新建: 技能 API 调用
├── stores/
│   └── skill.ts                  ← 新建: 技能状态管理
├── components/
│   ├── MainLayout.vue            ← 新建: 共享布局（SideMenu + TopBar + RouterView）
│   └── skill/                    ← 新建
│       ├── SkillCard.vue          # 技能卡片组件
│       ├── SkillDialog.vue        # 创建/编辑对话框（自定义模态框）
│       └── iconMap.ts             # 图标映射
├── views/
│   └── SkillsView.vue            ← 新建: 技能管理页面
├── router/
│   └── index.ts                  ← 修改: 嵌套路由结构
├── components/
│   ├── SideMenu.vue              ← 修改: 动态路由高亮 + 导航
│   └── AppShell.vue              ← 修改: 移除 SideMenu 和 TopBar（上移至 MainLayout）
```

### 2.3 模块分层

```
Views 层        SkillsView.vue
                 └── Components 层   SkillCard.vue / SkillDialog.vue
                      └── Stores 层       useSkillStore
                           ├── Services 层   skillApi
                           └── Types 层      skill.ts
```

### 2.4 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `SkillCard.vue` |
| Store | `useXxxStore` | `useSkillStore` |
| API 函数 | camelCase | `fetchSkills()` |
| Store Actions | camelCase | `addSkill()`, `removeSkill()` |
| 类型接口 | PascalCase | `Skill`, `SkillCreateRequest` |
| 目录 | kebab-case | `components/skill/` |

---

## 3. 路由设计

### 3.1 路由表

Skills 页面嵌套在 `MainLayout` 下，与首页共享布局外壳：

```typescript
// src/router/index.ts
const MainLayout = () => import('@/components/MainLayout.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
      { path: 'skills', name: 'skills', component: () => import('@/views/SkillsView.vue'), meta: { title: 'Skills' } },
    ],
  },
  // 登录/注册使用独立的 AuthLayout，不经过 MainLayout
]
```

| 路径 | 名称 | 组件 | Meta |
|------|------|------|------|
| `/skills` | `skills` | `SkillsView.vue` (懒加载) | 继承父路由 `requiresAuth: true` |

### 3.2 路由守卫

`requiresAuth: true` 在父路由 `path: '/'` 上定义，子路由 `/skills` 自动继承。Vue Router 4 `to.meta` 合并所有匹配路由的 meta，未登录用户访问 `/skills` 重定向至 `/login?redirect=/skills`。

### 3.3 SideMenu 联动

SideMenu 引入 `useRouter` / `useRoute`，菜单项增加 `route` 字段，通过 `isItemActive()` 动态判断高亮，通过 `handleItemClick()` 导航：

```typescript
interface MenuItem {
  icon: Component
  text: string
  route?: string
}

function isItemActive(item: MenuItem): boolean {
  if (item.route) return route.path === item.route
  return false
}

function handleItemClick(item: MenuItem) {
  if (item.route) router.push(item.route)
}
```

"技能"菜单项：`{ icon: Zap, text: '技能', route: '/skills' }`

---

## 4. 组件设计

### 4.1 MainLayout.vue — 共享布局

**功能**: 所有需认证页面的外壳，包含共享的 SideMenu + TopBar + `<RouterView />` 内容区。

```
┌──────────┬──────────────────────────────┐
│ SideMenu │  TopBar (搜索/通知/用户)      │
│  (共享)  ├──────────────────────────────│
│          │  work-area                   │
│          │  ┌────────────────────────┐  │
│          │  │ <RouterView />         │  │
│          │  │  二级页面内容...         │  │
│          │  └────────────────────────┘  │
└──────────┴──────────────────────────────┘
```

**关键 CSS**:
- `.main-layout`: `display: flex; height: 100vh`
- `.right-area`: `flex: 1; display: flex; flex-direction: column; overflow: hidden`
- `.work-area`: `flex: 1; overflow: hidden; min-height: 0`

### 4.2 AppShell.vue — 聊天页面（修改后）

从原三栏布局中移除 SideMenu 和 TopBar（已上移至 MainLayout），仅保留：

```
AppShell (flex row, height: 100%)
├── chat-column (flex:1) → ChatMain
└── RightPanel (280px)
```

### 4.3 SkillsView.vue

#### 4.3.1 组件树

```
SkillsView.vue
├── 页面标题行
│   ├── 标题 "Skills" + 描述
│   └── el-button "创建技能" [type=primary]
├── 状态横幅 (仅接口错误时显示, type=warning, closable)
├── 统计栏 (4 卡片: 总数/已启用/已禁用/不可用)
├── 分类筛选栏 (el-button round, 全部/搜索/代码/创意/分析/工具)
├── 分类概览 (5 卡片, 每分类显示 total/enabled/disabled)
├── 技能列表标题 + 计数
└── 技能卡片网格
    └── SkillCard.vue × N
```

#### 4.3.2 脚本结构

```typescript
const skillStore = useSkillStore()
const activeCategory = ref('')
const dialogVisible = ref(false)
const editingSkill = ref<Skill | null>(null)

// 分类统计
const categoryStatsEntries = computed(() => {
  return Object.entries(skillStore.categoryStats).map(([key, stats]) => ({
    key, label: CATEGORY_LABELS[key] || key, ...stats,
  }))
})

// Actions
async function handleSave(data: SkillCreateRequest) {
  if (editingSkill.value) {
    await skillStore.editSkill(editingSkill.value.id, data)
  } else {
    await skillStore.addSkill(data)
  }
}

async function handleToggle(skill: Skill) {
  await skillStore.toggleSkillEnabled(skill.id, !skill.enabled)
}

async function handleDelete(skill: Skill) {
  await ElMessageBox.confirm(`确定要删除技能"${skill.name}"吗？...`)
  await skillStore.removeSkill(skill.id)
}
```

#### 4.3.3 状态处理

| 状态 | 展示 |
|------|------|
| 加载中 | `v-loading` + `el-skeleton` 卡片占位（6 个骨架卡片） |
| 空数据（全部） | `el-empty description="暂无技能，点击上方按钮创建第一个技能"` + 创建按钮 |
| 空数据（筛选后） | `el-empty description="该分类下暂无技能"` |
| 接口错误 | `el-alert type="warning"` + 重试按钮（可关闭） |
| 正常 | 统计卡片 + 分类概览 + 卡片网格 |

#### 4.3.4 样式要点

```css
.skills-page {
  height: 100%;           /* 自适应 work-area */
  /* 无 overflow-y，滚动由 work-area 管理 */
  padding: 24px 32px;
  gap: 20px;
}
.skills-grid {
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}
.stats-bar { grid-template-columns: repeat(4, 1fr); gap: 16px; }
.category-grid { grid-template-columns: repeat(5, 1fr); gap: 12px; }
```

### 4.4 SkillCard.vue

#### 4.4.1 组件契约

**Props**: `skill: Skill`

**Emits**: `edit(skill)`, `delete(skill)`, `toggle(skill)`

#### 4.4.2 卡片结构

```
┌─────────────────────────────────────────┐
│ [图标圆角框]  技能名称  [内置标签]  [开关] │  ← header
│                                         │
│ 技能描述文字（最多2行）                    │  ← description
│                                         │
│ [分类标签]                   [编辑][删除] │  ← footer
└─────────────────────────────────────────┘
```

#### 4.4.3 视觉规格

| 属性 | 值 |
|------|-----|
| 背景 | `var(--surface-card)` |
| 边框 | `1px solid var(--border-subtle)` |
| 圆角 | `var(--radius-xl)` (12px) |
| hover 边框 | `rgba(59, 130, 246, 0.25)` |
| 内间距 | 20px |
| 图标框 | 36×36px, border-radius 10px, bg `var(--accent-primary-light)` |
| 编辑/删除 | 仅 `!skill.is_builtin` 时显示，lucide Pencil/Trash2 |

### 4.5 SkillDialog.vue

**架构**: 不使用 `el-dialog`，改用 `Teleport` + 自定义模态框（与 `CaptchaModal` 相同模式），完全自主控制暗色主题样式。

#### 4.5.1 组件契约

```typescript
defineProps<{ visible: boolean; skill: Skill | null }>()
defineEmits<{ (e: 'close'): void; (e: 'save', data: SkillCreateRequest): void }>()
```

#### 4.5.2 模态框规格

| 属性 | 值 |
|------|-----|
| 实现方式 | `Teleport to="body"` + 自定义 overlay |
| 固定尺寸 | `width: 680px; height: 660px; max-height: 88vh` |
| 背景 | `var(--color-modal-bg)` (rgba(15,23,46,0.98)) |
| 边框 | `var(--color-border-card)` |
| 遮罩 | `var(--color-overlay)`，点击遮罩关闭 |
| ESC 关闭 | `document.addEventListener('keydown')` 先关闭下拉再关闭对话框 |

#### 4.5.3 Tab 导航

三个 Tab，胶囊式按钮组，**默认激活"从仓库下载"**：

```
[从仓库下载] [本地上传] [手动创建]
```

编辑模式下不显示 Tab 导航，直接显示手动创建表单。

#### 4.5.4 Tab 1: 从仓库下载

**布局结构** — 统一面板 `.download-panel`（flex column）：

```
┌── download-panel ──────────────────────┐
│ [ClawHub ▼] [https://clawhub.ai/] [获取]│ ← dp-top (单行, flex-shrink:0)
│ ─────────────────────────────────────── │ ← dp-divider
│ [🔍 检索技能...]                        │ ← dp-search (flex-shrink:0)
│ ☑ 全选当前页              已选 N/M 个   │ ← dp-select-all (flex-shrink:0)
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│ ☑ web-search      实时搜索...  [搜索]   │
│ ☑ code-interpreter 沙箱执行... [代码]   │ ← dp-skill-list (flex:1, overflow-y:auto)
│ ☐ image-generator  生成图像... [创意]   │     ↑ 唯一滚动区域
│ ...                                    │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│           ‹ 1  2 ›                     │ ← dp-pager (flex-shrink:0)
│ ─────────────────────────────────────── │ ← dp-divider
│              [取消] [拉取到本地 (3)]     │ ← dp-actions (flex-shrink:0)
└────────────────────────────────────────┘
```

**仓库下拉菜单** — 自定义实现，不依赖 `el-select`（避免 portal 白底问题）：

```html
<div ref="repoSelectRef" class="custom-select" :class="{ open: repoDropdownOpen }">
  <button class="select-trigger" @click.stop="repoDropdownOpen = !repoDropdownOpen">
    <span>{{ isCustomRepo ? '自定义地址' : selectedRepo.label }}</span>
    <ChevronDown />
  </button>
  <div v-show="repoDropdownOpen" class="select-dropdown">
    <div v-for="opt in repoOptions" class="select-option" @click.stop="selectRepoOption(opt)">
      <span>{{ opt.label }}</span><span>{{ opt.desc }}</span>
      <Check v-if="selected" />
    </div>
    <div class="select-divider" />
    <div class="select-option" @click.stop="selectCustomRepo()">
      自定义地址 / 手动输入仓库 URL
    </div>
  </div>
</div>
```

**关闭逻辑**: `document.addEventListener('click', handleClickOutside, true)` 在捕获阶段监听，点击 `.custom-select` 外部时关闭下拉。ESC 键先关闭下拉，再关闭对话框。

**预设仓库**: ClawHub（默认）/ Anthropic Skills / LangChain / CrewAI / AutoGen

**分页**: 自定义 `.dp-pager`（不依赖 `el-pagination`），每页 6 条

**技能检索**: 自定义搜索框，按名称/描述/分类实时过滤

**导入**: 全选当前页复选框（支持半选态），已选计数，批量 `emit('save')`

#### 4.5.5 Tab 2: 本地上传

- 自定义 dropzone（不依赖 `el-upload`），拖拽 + 点击上传
- 支持格式：`.json` / `.yaml` / `.yml` / `.md` / `.zip`
- 校验结果面板：文件扩展名 → 字段完整性检查
- 绿色圆点（通过）/ 红色圆点（失败）视觉反馈

#### 4.5.6 Tab 3: 手动创建

- 5 个表单字段：技能名称* / 描述 / 图标名称 / 分类 / 系统提示词
- 自定义 `<input>` 和 `<textarea>`（不依赖 `el-form`），暗色主题样式
- 编辑模式：watch `skill` prop 回填表单 + 标题改为"编辑技能"

#### 4.5.7 样式要点

- **所有 Element Plus 组件已被自定义实现替代**：`el-dialog` → 自定义 modal、`el-select` → 自定义 dropdown、`el-upload` → 自定义 dropzone、`el-pagination` → 自定义 pager
- Checkbox 为纯 CSS 实现（`.check-box.checked` / `.check-box.partial`）
- 滚动条：`::-webkit-scrollbar` width 6px，半透明白色 thumb
- 按钮：`.btn-primary`（蓝色）/ `.btn-ghost`（暗色半透明 + 边框）
- 输入框：`#0f172e` 背景 + `#1f293d` 边框，focus 蓝色边框 + 外发光

### 4.6 iconMap.ts

```typescript
import {
  Globe, Code2, Image, BarChart3, FolderOpen,
  Zap, Search, FileText, Database, Palette, Music, Wrench,
} from 'lucide-vue-next'
import type { Component } from 'vue'

export const SKILL_ICONS: Record<string, Component> = {
  Globe, Code2, Image, BarChart3, FolderOpen, Zap,
  Search, FileText, Database, Palette, Music, Wrench,
}

export function getSkillIcon(iconName: string): Component {
  return SKILL_ICONS[iconName] || Zap
}
```

使用 `BarChart3`（而非 `ChartBar` — 后者在 lucide-vue-next 中不存在）。缺省 fallback 为 `Zap`。

---

## 5. 状态管理设计

### 5.1 useSkillStore

```typescript
// src/stores/skill.ts
export const useSkillStore = defineStore('skill', () => {
  // State
  const skills = ref<Skill[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const builtinSkills = computed(() => skills.value.filter(s => s.is_builtin))
  const customSkills = computed(() => skills.value.filter(s => !s.is_builtin))
  const enabledSkills = computed(() => skills.value.filter(s => s.enabled))
  const disabledSkills = computed(() => skills.value.filter(s => !s.enabled))
  const categoryStats = computed(() => {
    // 返回 Record<category, { total, enabled, disabled }>
    const map: Record<string, { total: number; enabled: number; disabled: number }> = {}
    for (const s of skills.value) {
      if (!map[s.category]) map[s.category] = { total: 0, enabled: 0, disabled: 0 }
      map[s.category].total++
      s.enabled ? map[s.category].enabled++ : map[s.category].disabled++
    }
    return map
  })

  // Actions
  async function fetchSkills(category?: string) {
    loading.value = true; error.value = null
    try { skills.value = await skillApi.fetchSkills(category) }
    catch (err: unknown) {
      if (err instanceof Error && err.message.includes('404'))
        error.value = 'Skills API 尚未部署，后端接口开发中'
      else
        error.value = err instanceof Error ? err.message : '加载技能列表失败'
    }
    finally { loading.value = false }
  }

  async function addSkill(data: SkillCreateRequest): Promise<Skill> { ... }
  async function editSkill(id: string, data: Partial<SkillCreateRequest>): Promise<Skill> { ... }
  async function removeSkill(id: string) { ... }
  async function toggleSkillEnabled(id: string, enabled: boolean) { ... }  // 乐观更新
})
```

### 5.2 Store Actions 对照

| 原设计名 | 实现名 | 说明 |
|---------|--------|------|
| `createSkill` | `addSkill` | 创建后 unshift 到列表头部 |
| `updateSkill` | `editSkill` | 更新后替换列表中对应项 |
| `deleteSkill` | `removeSkill` | 删除后从列表过滤 |
| `toggleSkill` | `toggleSkillEnabled` | 乐观更新 + 失败回滚 |

### 5.3 乐观更新策略

`toggleSkillEnabled` 采用乐观更新：立即修改本地 `skill.enabled`，API 失败时回滚。其余操作采用悲观更新。

### 5.4 分类统计

`categoryStats` computed 在 SkillsView 中映射为 `categoryStatsEntries`，驱动分类概览区域渲染。

---

## 6. 类型定义

```typescript
// src/types/skill.ts

export interface Skill {
  id: string; name: string; description: string
  icon: string; category: string; prompt: string
  enabled: boolean; is_builtin: boolean
  user_id: string | null; created_at: string; updated_at: string
}

export interface SkillCreateRequest {
  name: string
  description?: string
  icon?: string
  category?: string
  prompt?: string
}

export const CATEGORY_LABELS: Record<string, string> = {
  search: '搜索', code: '代码', creative: '创意',
  analysis: '分析', tools: '工具', custom: '自定义',
}

export const CATEGORY_FILTERS = [
  { key: '', label: '全部' },
  { key: 'search', label: '搜索' },
  { key: 'code', label: '代码' },
  { key: 'creative', label: '创意' },
  { key: 'analysis', label: '分析' },
  { key: 'tools', label: '工具' },
]
```

---

## 7. API 服务层设计

### 7.1 skillApi

```typescript
// src/services/skillApi.ts
import instance from './request'

export async function fetchSkills(category?: string): Promise<Skill[]> {
  const res = await instance.get('/skills', category ? { params: { category } } : {})
  return res.data.data as Skill[]
}
export async function createSkill(data: SkillCreateRequest): Promise<Skill> { ... }
export async function fetchSkill(id: string): Promise<Skill> { ... }
export async function updateSkill(id: string, data: Partial<SkillCreateRequest>): Promise<Skill> { ... }
export async function deleteSkill(id: string): Promise<void> { ... }
export async function toggleSkill(id: string, enabled: boolean): Promise<Skill> { ... }
```

### 7.2 接口对照表

| 函数 | HTTP | 路径 |
|------|------|------|
| `fetchSkills(category?)` | GET | `/api/skills?category=` |
| `createSkill(data)` | POST | `/api/skills` |
| `fetchSkill(id)` | GET | `/api/skills/{id}` |
| `updateSkill(id, data)` | PUT | `/api/skills/{id}` |
| `deleteSkill(id)` | DELETE | `/api/skills/{id}` |
| `toggleSkill(id, enabled)` | PATCH | `/api/skills/{id}/toggle` |

### 7.3 错误处理

- 所有接口复用 `request.ts` 的 Axios 实例，自动注入 Token + 401 刷新
- `code !== 0` → `ApiError(code, message)`
- 404 → store 中识别并显示友好提示："Skills API 尚未部署，后端接口开发中"
- 网络异常 → `ElMessage.error`

---

## 8. 样式设计

### 8.1 设计 Token

完全复用 `variables.css` 中已定义的 CSS 变量：

| 用途 | 变量 |
|------|------|
| 页面背景 | `--surface-primary` (#060b1a) |
| 卡片背景 | `--surface-card` |
| 输入框背景 | `--color-bg-input` (#0f172e) |
| 输入框边框 | `--color-border-input` (#1f293d) |
| 主色调 | `--accent-primary` (#3b82f6) |
| 模态框背景 | `--color-modal-bg` |
| 遮罩 | `--color-overlay` |

### 8.2 SkillDialog 暗色主题关键样式

```css
/* overlay */
.skill-overlay { position: fixed; inset: 0; background: var(--color-overlay); }
/* modal shell */
.skill-modal { background: var(--color-modal-bg); border: 1px solid var(--color-border-card); }
/* tabs */
.dialog-tabs { background: var(--color-bg-input); padding: 3px; }
.tab-btn.active { background: var(--accent-primary); color: #fff; }
/* inputs */
.text-input { background: var(--color-bg-input); border: 1px solid var(--color-border-input); }
.text-input:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 2px rgba(59,130,246,0.12); }
/* dropdown */
.select-dropdown { background: #111b35; border: 1px solid var(--color-border-card); box-shadow: 0 8px 30px rgba(0,0,0,0.55); }
/* scrollbar */
.dp-skill-list::-webkit-scrollbar { width: 6px; }
.dp-skill-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); }
```

---

## 9. 交互流程

### 9.1 加载技能列表

```
SkillsView.onMounted() → skillStore.fetchSkills() → GET /api/skills
  → 成功: skills 填充 → 页面渲染
  → 失败: error 设置 → warning 横幅
```

### 9.2 创建技能（仓库下载）

```
选择仓库 [ClawHub ▼] → 点击 [获取] → 模拟 API 拉取技能列表
  → 搜索框检索过滤 → 勾选技能 → 分页浏览
  → [拉取到本地 (N)] → 逐个 emit('save') → store.addSkill() → POST /api/skills
```

### 9.3 创建技能（手动）

```
[手动创建] Tab → 填写表单 → [创建]
  → emit('save', data)
  → store.addSkill(data) → POST /api/skills
  → ElMessage.success → 关闭对话框
```

### 9.4 编辑/切换/删除

与设计初版流程一致，Actions 名称已更新为实际代码命名。

### 9.5 分类筛选

```
点击分类标签 → activeCategory = key → filteredSkills 计算属性过滤 → 网格更新
```

---

## 10. 权限控制（前端侧）

| 操作 | 内置技能 | 自定义技能 |
|------|----------|-----------|
| 查看 | 是 | 是 |
| 编辑按钮 | 隐藏 | 显示 |
| 删除按钮 | 隐藏 | 显示 |
| 切换启用 | 允许 | 允许 |

前端实现：`v-if="!skill.is_builtin"` 控制按钮显隐。后端二次校验 403 响应。

---

## 11. 测试设计

与设计初版（v1.0.0）的测试用例保持一致，Store / API / SkillCard / SkillDialog 的测试覆盖不变。SkillDialog 的测试需注意：不再使用 `el-dialog`，改为自定义 modal + 自定义 dropdown。

---

## 12. 附录

### 12.1 变更文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/types/skill.ts` | **新建** | Skill 类型 + CATEGORY_LABELS + CATEGORY_FILTERS |
| `src/services/skillApi.ts` | **新建** | 6 个 API 函数 |
| `src/stores/skill.ts` | **新建** | Pinia Store（含 categoryStats getter, 404 检测） |
| `src/components/skill/iconMap.ts` | **新建** | 图标映射 (BarChart3) |
| `src/components/skill/SkillCard.vue` | **新建** | 技能卡片 |
| `src/components/skill/SkillDialog.vue` | **新建** | 自定义模态框（3 Tab, 自定义 dropdown/dropzone/pager） |
| `src/views/SkillsView.vue` | **新建** | 技能管理页面（统计栏 + 分类概览 + 网格） |
| `src/components/MainLayout.vue` | **新建** | 共享布局（SideMenu + TopBar + RouterView） |
| `src/router/index.ts` | 修改 | 嵌套路由（MainLayout 为父，home/skills 为子） |
| `src/components/SideMenu.vue` | 修改 | 动态路由高亮 + 导航 |
| `src/components/AppShell.vue` | 修改 | 移除 SideMenu 和 TopBar |

### 12.2 内置技能数据

| 名称 | 图标 | 分类 |
|------|------|------|
| 网络搜索 | Globe | search |
| 代码解释器 | Code2 | code |
| 图像生成 | Image | creative |
| 数据分析 | BarChart3 | analysis |
| 文件管理 | FolderOpen | tools |

### 12.3 v1.0.0 → v1.0.1 主要变更

| 设计项 | v1.0.0 计划 | v1.0.1 实施 |
|--------|------------|------------|
| 页面布局 | SkillsView 独立渲染（无 SideMenu） | MainLayout 共享布局嵌套 |
| AppShell | 包含 SideMenu + TopBar | SideMenu/TopBar 上移至 MainLayout |
| SkillDialog | `el-dialog` + `el-select` + `el-upload` | 自定义 Teleport 模态框，无 Element Plus 弹窗依赖 |
| Tab 顺序 | 手动创建 → 下载 → 上传 | 从仓库下载 → 本地上传 → 手动创建 |
| 仓库选择 | `el-select` + 外部 "自定义" 按钮 | 自定义 dropdown，"自定义地址" 在下拉列表中 |
| 下载面板 | 仓库选择区和结果区分离 | 统一 `.download-panel`，单行顶部栏 |
| 下拉菜单关闭 | `@mousedown.prevent` + `@blur` | `document.addEventListener('click', capture phase)` |
| 分页 | `el-pagination` | 自定义 `.dp-pager` |
| 图标 | `ChartBar` | `BarChart3`（lucide-vue-next 实际导出名） |
| Store Actions | `createSkill` / `updateSkill` / `deleteSkill` / `toggleSkill` | `addSkill` / `editSkill` / `removeSkill` / `toggleSkillEnabled` |
| Store Getters | `builtinSkills` / `customSkills` / `enabledSkills` | 增加 `disabledSkills` / `categoryStats` |
| 错误处理 | 通用 `ElMessage.error` | 404 识别 + 友好提示 |

---

> 本文档仅包含前端内容，与实际代码实现保持一致（v1.0.1）。后端设计参见 [Ke-Hermes Skills 功能模块详细设计说明书-1.0.0](../../../docs/Ke-Hermes-Skills%20功能模块详细设计说明书-1.0.0.md)。
