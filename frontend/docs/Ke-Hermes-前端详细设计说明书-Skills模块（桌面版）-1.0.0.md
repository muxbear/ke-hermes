# Ke-Hermes 前端详细设计说明书 — Skills 模块（桌面版）v1.0.0

| 版本    | 日期         | 作者  | 变更说明                           |
| ----- | ---------- | --- | ------------------------------ |
| 1.0.0 | 2026-05-26 | -   | Skills 模块前端详细设计初版，基于后端设计说明书 v1.0.0 |

---

## 目录

1. [概述](#1-概述)
2. [项目架构](#2-项目架构)
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

本文档为 Ke-Hermes Skills 模块的**前端**详细设计说明书，基于《Ke-Hermes Skills 功能模块详细设计说明书-1.0.0》（下文简称"后端设计说明书"）编写。文档定义了 Skills 模块前端的技术架构、组件结构、数据流、接口契约和实现规范，供前端开发人员编码实现。

**本文档仅包含前端内容**。后端 API 设计、数据库设计、服务层设计等参见后端设计说明书。

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

## 2. 项目架构

### 2.1 目录规划

Skills 模块涉及以下前端文件的变更：

```
frontend/src/
├── types/
│   └── skill.ts                  ← 新建: 技能类型定义
├── services/
│   └── skillApi.ts               ← 新建: 技能 API 调用
├── stores/
│   └── skill.ts                  ← 新建: 技能状态管理
├── components/
│   └── skill/                    ← 新建
│       ├── SkillCard.vue          # 技能卡片组件
│       ├── SkillDialog.vue        # 创建/编辑对话框
│       └── iconMap.ts             # 图标映射
├── views/
│   └── SkillsView.vue            ← 新建: 技能管理页面
├── router/
│   └── index.ts                  ← 修改: 添加 /skills 路由
└── components/
    └── SideMenu.vue              ← 修改: Skills 菜单联动
```

### 2.2 模块分层

```
Views 层        SkillsView.vue
                 └── Components 层   SkillCard.vue / SkillDialog.vue
                      └── Stores 层       useSkillStore
                           ├── Services 层   skillApi
                           └── Types 层      skill.ts
```

依赖方向：上层依赖下层，下层不感知上层。

### 2.3 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `SkillCard.vue` |
| Store | `useXxxStore` | `useSkillStore` |
| API 函数 | camelCase | `fetchSkills()` |
| 类型接口 | PascalCase | `Skill`, `SkillCreateRequest` |
| 目录 | kebab-case | `components/skill/` |

---

## 3. 路由设计

### 3.1 路由表

在现有路由表中新增 Skills 页面路由：

```typescript
// src/router/index.ts — 新增路由
{
  path: '/skills',
  name: 'skills',
  component: () => import('@/views/SkillsView.vue'),
  meta: { requiresAuth: true, title: 'Skills' },
}
```

| 路径 | 名称 | 组件 | Meta |
|------|------|------|------|
| `/skills` | `skills` | `SkillsView.vue` (懒加载) | requiresAuth: true |

### 3.2 路由守卫

Skills 页面使用 `requiresAuth: true`，由现有全局前置守卫统一处理：未登录用户访问 `/skills` 将被重定向至 `/login?redirect=/skills`。

### 3.3 SideMenu 联动修改

`SideMenu.vue` 中"技能"菜单项需要支持路由导航和高亮：

**修改点 1：引入路由**

```typescript
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
```

**修改点 2：菜单项增加 route 字段**

```typescript
// 代理分组中"技能"项增加 route
{ icon: Zap, text: '技能', route: '/skills' }
// 聊天分组中"对话"项增加 route
{ icon: MessageSquare, text: '对话', route: '/' }
```

**修改点 3：模板增加导航与高亮逻辑**

```html
<div
  v-for="item in group.items"
  :key="item.text"
  class="menu-item"
  :class="{ active: item.route && route.path === item.route }"
  @click="item.route && router.push(item.route)"
>
  <component :is="item.icon" :size="16" />
  <span class="menu-text">{{ item.text }}</span>
</div>
```

menuGroups 中的 `active` 硬编码字段可移除（由 `route.path === item.route` 动态计算）。

---

## 4. 组件设计

### 4.1 组件树

```
SkillsView.vue
├── 页面标题行
│   ├── 标题 "Skills" + 描述文字
│   └── el-button "创建技能" [type=primary]
├── 分类标签栏 (按钮组)
├── 技能卡片网格
│   └── SkillCard.vue × N
│       ├── 图标圆角框 (lucide 动态组件)
│       ├── 技能名称 + "内置" 标签 (el-tag)
│       ├── el-switch (启用/禁用)
│       ├── 描述文字
│       └── 分类标签 + 编辑/删除按钮
├── SkillDialog.vue (条件渲染)
│   └── el-dialog + el-form
└── 删除确认 (el-message-box)
```

### 4.2 SkillsView.vue

#### 4.2.1 页面布局

```
┌──────────┬──────────────────────────────────────────────┐
│ SideMenu │  Skills                [+ 创建技能]           │
│ (复用)   │  管理和配置 AI 智能体的技能与工具能力          │
│          ├──────────────────────────────────────────────┤
│          │ [全部] [搜索] [代码] [创意] [分析] [工具]     │
│          ├──────────────┬──────────────┬─────────────────┤
│          │ Skill Card 1 │ Skill Card 2 │ Skill Card 3    │
│          ├──────────────┼──────────────┼─────────────────┤
│          │ Skill Card 4 │ Skill Card 5 │ Skill Card 6    │
│          │              │              │                 │
│          └──────────────┴──────────────┴─────────────────┘
└──────────┴──────────────────────────────────────────────┘
```

SkillsView 作为 HomeView 的平级页面，直接由 `<RouterView />` 渲染，**不嵌套在 AppShell 的三栏布局中**。页面左侧复用 `SideMenu.vue`（由 App.vue 或父级布局统一渲染），页面主内容区独立布局。

#### 4.2.2 脚本结构

```typescript
// src/views/SkillsView.vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from 'lucide-vue-next'
import { useSkillStore } from '@/stores/skill'
import type { Skill, SkillCreateRequest } from '@/types/skill'
import SkillCard from '@/components/skill/SkillCard.vue'
import SkillDialog from '@/components/skill/SkillDialog.vue'

const skillStore = useSkillStore()

// ---- 分类筛选 ----
const categories = [
  { key: '', label: '全部' },
  { key: 'search', label: '搜索' },
  { key: 'code', label: '代码' },
  { key: 'creative', label: '创意' },
  { key: 'analysis', label: '分析' },
  { key: 'tools', label: '工具' },
]
const activeCategory = ref('')

const filteredSkills = computed(() => {
  if (!activeCategory.value) return skillStore.skills
  return skillStore.skills.filter(s => s.category === activeCategory.value)
})

// ---- 对话框 ----
const dialogVisible = ref(false)
const editingSkill = ref<Skill | null>(null)

function openCreateDialog() {
  editingSkill.value = null
  dialogVisible.value = true
}

function openEditDialog(skill: Skill) {
  editingSkill.value = skill
  dialogVisible.value = true
}

// ---- 操作 ----
async function handleSave(data: SkillCreateRequest) {
  try {
    if (editingSkill.value) {
      await skillStore.updateSkill(editingSkill.value.id, data)
      ElMessage.success('技能已更新')
    } else {
      await skillStore.createSkill(data)
      ElMessage.success('技能创建成功')
    }
    dialogVisible.value = false
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

async function handleToggle(skill: Skill) {
  try {
    await skillStore.toggleSkill(skill.id, !skill.enabled)
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

async function handleDelete(skill: Skill) {
  try {
    await ElMessageBox.confirm(
      `确定要删除技能"${skill.name}"吗？此操作不可撤销。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await skillStore.deleteSkill(skill.id)
    ElMessage.success('技能已删除')
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  skillStore.fetchSkills()
})
</script>
```

#### 4.2.3 状态处理

| 状态 | 展示 |
|------|------|
| 加载中 | `v-loading` 指令 + `el-skeleton` 卡片占位（6 个骨架卡片） |
| 空数据（全部） | `el-empty description="暂无技能，点击上方按钮创建第一个技能"` |
| 空数据（筛选后） | `el-empty description="该分类下暂无技能"` |
| 接口错误 | `el-alert type="error"` 显示错误信息 + 重试按钮 |
| 正常 | 分类标签 + 卡片网格 |

#### 4.2.4 分类标签栏

使用 `el-button-group` 或平铺 `el-button`，当前选中项为 `type="primary"`，其余为 `type="default"`（或 `plain`）。

分类列表对应关系：

| 标签文字 | category 值 | 对应内置技能 |
|---------|------------|------------|
| 全部 | `""` | - |
| 搜索 | `"search"` | 网络搜索 |
| 代码 | `"code"` | 代码解释器 |
| 创意 | `"creative"` | 图像生成 |
| 分析 | `"analysis"` | 数据分析 |
| 工具 | `"tools"` | 文件管理 |

未选中的分类即使没有技能也正常展示（为空时由 el-empty 兜底）。

### 4.3 SkillCard.vue

#### 4.3.1 组件契约

**Props**:

```typescript
defineProps<{
  skill: Skill
}>()
```

**Emits**:

```typescript
defineEmits<{
  (e: 'edit', skill: Skill): void
  (e: 'delete', skill: Skill): void
  (e: 'toggle', skill: Skill): void
}>()
```

#### 4.3.2 卡片结构

```
┌─────────────────────────────────────┐
│ [图标圆角框]  技能名称  [内置]   [开关] │  ← header (flex, justify-between)
│                                     │
│ 技能描述文字...                       │  ← description
│                                     │
│ [分类标签]                   [编辑][删除]│  ← footer (flex, justify-between)
└─────────────────────────────────────┘
```

#### 4.3.3 视觉规格

| 属性 | 值 |
|------|-----|
| 背景 | `var(--surface-card)` |
| 边框 | `1px solid var(--border-subtle)` |
| 圆角 | `var(--radius-xl)` (12px) |
| 内间距 | 20px |
| 卡片内垂直间距 | 14px |
| 宽度 | 由 CSS Grid 列宽决定 |

#### 4.3.4 各区域规格

**图标圆角框**:
- 尺寸: 36×36px
- 圆角: 10px
- 背景: `var(--accent-primary-light)` (`rgba(59, 130, 246, 0.15)`)
- 图标: 从 `iconMap.ts` 获取对应 lucide 组件，18×18px
- 图标颜色: `var(--accent-primary)`

**技能名称**:
- 字号: `var(--font-size-md)` (14px)
- 字重: `var(--font-weight-semibold)` (600)

**内置标签**: 仅 `skill.is_builtin === true` 时显示，使用 `el-tag size="small" type="info"`

**开关**: `el-switch`，绑定 `skill.enabled`，内置技能也允许切换

**描述文字**:
- 字号: `var(--font-size-sm)` (12px)
- 颜色: `var(--foreground-secondary)`
- 最多显示 2 行（`display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;`）
- 无描述时显示 "暂无描述"（foreground-muted 色）

**分类标签**: `el-tag size="small"`，显示 `skill.category`，自定义技能显示为 "custom"，内置技能显示对应分类中文名

**编辑/删除按钮**: 仅 `skill.is_builtin === false` 时显示。使用 `el-button text`，编辑图标 `Pencil`(lucide)，删除图标 `Trash2`(lucide)

### 4.4 SkillDialog.vue

#### 4.4.1 组件契约

**Props**:

```typescript
defineProps<{
  visible: boolean
  skill: Skill | null  // null = 创建模式, Skill = 编辑模式
}>()
```

**Emits**:

```typescript
defineEmits<{
  (e: 'close'): void
  (e: 'save', data: SkillCreateRequest): void
}>()
```

#### 4.4.2 对话框规格

| 属性 | 值 |
|------|-----|
| 组件 | `el-dialog` |
| 标题 | 创建模式: "创建技能"，编辑模式: "编辑技能" |
| 宽度 | 520px |
| 关闭方式 | 右上角 X、点击遮罩、ESC 键 |
| 确认按钮文字 | 创建模式: "创建"，编辑模式: "保存" |
| 确认按钮加载态 | 提交时 `loading` 状态（由父组件控制） |

#### 4.4.3 表单字段

| 字段 | 组件 | 验证规则 | 默认值 |
|------|------|---------|--------|
| 名称 | `el-input` | 必填，最长 64 字符 | - |
| 描述 | `el-input type="textarea"` (3行) | 最长 512 字符 | - |
| 图标 | `el-input` | - | `"Zap"` |
| 分类 | `el-input` | - | `"custom"` |
| 提示词 | `el-input type="textarea"` (6行) | - | - |

编辑模式下，使用 `watch` 监听 `skill` prop 变化进行表单回填：

```typescript
import { ref, watch } from 'vue'
import type { Skill, SkillCreateRequest } from '@/types/skill'

const props = defineProps<{ visible: boolean; skill: Skill | null }>()
const emit = defineEmits<{ close: void; save: [data: SkillCreateRequest] }>()

const form = ref<SkillCreateRequest>({
  name: '',
  description: '',
  icon: 'Zap',
  category: 'custom',
  prompt: '',
})

watch(() => props.skill, (s) => {
  if (s) {
    form.value = {
      name: s.name,
      description: s.description,
      icon: s.icon,
      category: s.category,
      prompt: s.prompt,
    }
  } else {
    form.value = { name: '', description: '', icon: 'Zap', category: 'custom', prompt: '' }
  }
})

const isEditing = computed(() => !!props.skill)

function handleConfirm() {
  // el-form 校验通过后 emit
  emit('save', { ...form.value })
}
```

表单校验规则：

```typescript
const rules = {
  name: [
    { required: true, message: '请输入技能名称', trigger: 'blur' },
    { max: 64, message: '名称最长 64 个字符', trigger: 'blur' },
  ],
  description: [
    { max: 512, message: '描述最长 512 个字符', trigger: 'blur' },
  ],
}
```

### 4.5 iconMap.ts — 图标映射

```typescript
// src/components/skill/iconMap.ts
import {
  Globe, Code2, Image, ChartBar, FolderOpen,
  Zap, Search, FileText, Database, Palette, Music, Wrench,
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

使用方式：

```vue
<script setup lang="ts">
import { getSkillIcon } from '@/components/skill/iconMap'

const props = defineProps<{ skill: Skill }>()
const iconComponent = computed(() => getSkillIcon(props.skill.icon))
</script>

<template>
  <component :is="iconComponent" :size="18" />
</template>
```

`Zap` 作为 fallback 图标，当 `skill.icon` 不在 `SKILL_ICONS` 中时使用。

---

## 5. 状态管理设计

### 5.1 useSkillStore

```typescript
// src/stores/skill.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Skill, SkillCreateRequest } from '@/types/skill'
import * as skillApi from '@/services/skillApi'

export const useSkillStore = defineStore('skill', () => {
  // ---- State ----
  const skills = ref<Skill[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ---- Getters ----
  const builtinSkills = computed(() => skills.value.filter(s => s.is_builtin))
  const customSkills = computed(() => skills.value.filter(s => !s.is_builtin))
  const enabledSkills = computed(() => skills.value.filter(s => s.enabled))

  // ---- Actions ----
  async function fetchSkills(category?: string) {
    loading.value = true
    error.value = null
    try {
      skills.value = await skillApi.fetchSkills(category)
    } catch (err: any) {
      error.value = err.message || '加载技能列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createSkill(data: SkillCreateRequest) {
    const newSkill = await skillApi.createSkill(data)
    skills.value.unshift(newSkill)
    return newSkill
  }

  async function updateSkill(id: string, data: Partial<SkillCreateRequest>) {
    const updated = await skillApi.updateSkill(id, data)
    const idx = skills.value.findIndex(s => s.id === id)
    if (idx !== -1) skills.value[idx] = updated
    return updated
  }

  async function deleteSkill(id: string) {
    await skillApi.deleteSkill(id)
    skills.value = skills.value.filter(s => s.id !== id)
  }

  async function toggleSkill(id: string, enabled: boolean) {
    // 乐观更新
    const skill = skills.value.find(s => s.id === id)
    if (skill) skill.enabled = enabled
    try {
      await skillApi.toggleSkill(id, enabled)
    } catch {
      // 回滚
      if (skill) skill.enabled = !enabled
      throw new Error('切换失败')
    }
  }

  return {
    skills, loading, error,
    builtinSkills, customSkills, enabledSkills,
    fetchSkills, createSkill, updateSkill, deleteSkill, toggleSkill,
  }
})
```

### 5.2 状态流转

```
初始: skills=[], loading=false, error=null
  ↓ fetchSkills()
加载中: loading=true
  ↓ 成功
正常: skills=[...], loading=false, error=null
  ↓ 失败
错误: error="错误信息", loading=false
  ↓ 重试 → fetchSkills()
正常
```

### 5.3 乐观更新策略

`toggleSkill` 采用乐观更新：先更新本地状态，API 失败时回滚。创建/编辑/删除操作采用悲观更新：API 返回成功后更新本地状态。

---

## 6. 类型定义

```typescript
// src/types/skill.ts

/** 技能实体 */
export interface Skill {
  id: string
  name: string
  description: string
  icon: string
  category: string
  prompt: string
  enabled: boolean
  is_builtin: boolean
  user_id: string | null
  created_at: string
  updated_at: string
}

/** 创建/更新技能请求 */
export interface SkillCreateRequest {
  name: string
  description?: string
  icon?: string
  category?: string
  prompt?: string
}

/** 分类枚举 */
export type SkillCategory = 'search' | 'code' | 'creative' | 'analysis' | 'tools' | 'custom'

/** 分类中文映射 */
export const CATEGORY_LABELS: Record<string, string> = {
  search: '搜索',
  code: '代码',
  creative: '创意',
  analysis: '分析',
  tools: '工具',
  custom: '自定义',
}
```

类型文件遵循现有的 `src/types/` 目录规范，与 `api.ts`、`auth.ts`、`captcha.ts` 并列。

---

## 7. API 服务层设计

### 7.1 skillApi

```typescript
// src/services/skillApi.ts
import instance from './request'
import type { Skill, SkillCreateRequest } from '@/types/skill'

/** 获取技能列表 */
export async function fetchSkills(category?: string): Promise<Skill[]> {
  const params = category ? { category } : {}
  const res = await instance.get('/skills', { params })
  return res.data.data as Skill[]
}

/** 创建技能 */
export async function createSkill(data: SkillCreateRequest): Promise<Skill> {
  const res = await instance.post('/skills', data)
  return res.data.data as Skill
}

/** 获取技能详情 */
export async function fetchSkill(id: string): Promise<Skill> {
  const res = await instance.get(`/skills/${id}`)
  return res.data.data as Skill
}

/** 更新技能 */
export async function updateSkill(id: string, data: Partial<SkillCreateRequest>): Promise<Skill> {
  const res = await instance.put(`/skills/${id}`, data)
  return res.data.data as Skill
}

/** 删除技能 */
export async function deleteSkill(id: string): Promise<void> {
  await instance.delete(`/skills/${id}`)
}

/** 切换启用状态 */
export async function toggleSkill(id: string, enabled: boolean): Promise<Skill> {
  const res = await instance.patch(`/skills/${id}/toggle`, { enabled })
  return res.data.data as Skill
}
```

### 7.2 接口对照表

| 前端函数 | HTTP 方法 | 路径 | 说明 |
|---------|----------|------|------|
| `fetchSkills(category?)` | GET | `/api/skills?category=` | 获取技能列表 |
| `createSkill(data)` | POST | `/api/skills` | 创建技能 |
| `fetchSkill(id)` | GET | `/api/skills/{id}` | 获取技能详情 |
| `updateSkill(id, data)` | PUT | `/api/skills/{id}` | 更新技能 |
| `deleteSkill(id)` | DELETE | `/api/skills/{id}` | 删除技能 |
| `toggleSkill(id, enabled)` | PATCH | `/api/skills/{id}/toggle` | 切换启用状态 |

### 7.3 错误处理

所有接口错误由 `request.ts` 响应拦截器统一处理：

- `code !== 0` → 抛出 `ApiError(code, message)`
- `401` → 自动刷新 Token 或跳转登录
- `403` → 组件层捕获后展示 "无权操作" 错误提示
- `404` → 组件层捕获后展示 "技能不存在" 错误提示
- 网络异常 → 由调用方 catch 后展示 `ElMessage.error`

---

## 8. 样式设计

### 8.1 设计 Token

Skills 页面复用 `variables.css` 中已定义的 CSS 变量，不新增全局 Token。

### 8.2 页面布局样式

```scss
// SkillsView.vue <style scoped lang="scss">
.skills-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 32px;
  height: 100vh;
  overflow-y: auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  &__info {
    h1 {
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-bold);
      color: var(--foreground-primary);
      margin: 0;
    }
    p {
      font-size: var(--font-size-sm);
      color: var(--foreground-secondary);
      margin: 4px 0 0;
    }
  }
}

.category-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}
```

### 8.3 SkillCard 样式

```scss
// SkillCard.vue <style scoped lang="scss">
.skill-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: border-color var(--transition-fast);

  &:hover {
    border-color: rgba(59, 130, 246, 0.25);
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-box {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--accent-primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--accent-primary);
}

.skill-name {
  flex: 1;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.card-description {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 18px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-actions {
  display: flex;
  gap: 4px;
}
```

### 8.4 SkillDialog 样式

使用 `el-dialog` + `el-form` 默认样式，`el-input` / `el-textarea` 全局暗色主题样式已由 `variables.css` 覆盖。

---

## 9. 交互流程

### 9.1 加载技能列表

```
SkillsView.onMounted()
  → useSkillStore.fetchSkills()
    → skillApi.fetchSkills()
      → GET /api/skills
    ← Skill[]
  → skills 更新 (ref)
→ 模板响应式渲染
```

### 9.2 创建技能

```
用户点击 [创建技能]
  → SkillDialog 打开 (visible=true, skill=null)
  → 填写表单 → 点击 [创建]
  → 前端 el-form 校验
  → emit('save', data)
  → SkillsView.handleSave(data)
    → useSkillStore.createSkill(data)
      → skillApi.createSkill(data)
        → POST /api/skills
      ← Skill
    → skills.unshift(newSkill)
  → ElMessage.success("技能创建成功")
  → 关闭对话框
```

### 9.3 编辑技能

```
用户点击卡片 [编辑] 按钮
  → SkillDialog 打开 (visible=true, skill=当前技能)
  → 表单回填当前技能数据
  → 修改 → 点击 [保存]
  → emit('save', data)
  → SkillsView.handleSave(data)
    → useSkillStore.updateSkill(id, data)
      → skillApi.updateSkill(id, data)
        → PUT /api/skills/{id}
      ← Skill (更新后)
    → skills[idx] = updated
  → ElMessage.success("技能已更新")
  → 关闭对话框
```

### 9.4 切换启用/禁用

```
用户点击卡片 [开关]
  → SkillCard emit('toggle', skill)
  → SkillsView.handleToggle(skill)
    → useSkillStore.toggleSkill(id, enabled)
      → 乐观更新: skill.enabled = enabled (UI 立即响应)
      → skillApi.toggleSkill(id, enabled)
        → PATCH /api/skills/{id}/toggle
      ← 成功: 保持
      → 失败: 回滚 skill.enabled, ElMessage.error
```

### 9.5 删除技能

```
用户点击卡片 [删除] 按钮
  → SkillsView.handleDelete(skill)
  → ElMessageBox.confirm("确定要删除技能"{name}"吗？")
  → 用户确认
    → useSkillStore.deleteSkill(id)
      → skillApi.deleteSkill(id)
        → DELETE /api/skills/{id}
    → skills 中移除该 skill
  → ElMessage.success("技能已删除")
```

### 9.6 分类筛选

```
用户点击分类标签
  → activeCategory = categoryKey
  → filteredSkills 计算属性自动过滤
  → 卡片网格响应式更新
```

---

## 10. 权限控制（前端侧）

### 10.1 权限规则

| 操作 | 内置技能 | 他人的自定义技能 | 自己的自定义技能 |
|------|----------|------------------|------------------|
| 查看 | 是 | 是 | 是 |
| 创建 | - | - | 是 |
| 编辑按钮 | 隐藏 | 隐藏 | 显示 |
| 删除按钮 | 隐藏 | 隐藏 | 显示 |
| 切换启用 | 允许 | 允许 | 允许 |

### 10.2 前端实现

权限控制在前端通过 `skill.is_builtin` 字段实现：

```vue
<!-- SkillCard.vue — 仅自定义技能显示编辑/删除 -->
<div v-if="!skill.is_builtin" class="card-actions">
  <el-button text @click.stop="emit('edit', skill)">
    <Pencil :size="14" />
  </el-button>
  <el-button text @click.stop="emit('delete', skill)">
    <Trash2 :size="14" />
  </el-button>
</div>
```

后端会二次校验权限（403 响应），前端拦截并展示错误提示。当前版本不区分"他人"还是"自己"的技能（`user_id` 比对），因为后端 `/api/skills` 接口已过滤：仅返回内置技能 + 当前用户自定义技能，不会返回他人的自定义技能。

### 10.3 403 错误处理

```typescript
// 在 handleSave / handleToggle 的 catch 中
if (err.code === 403) {
  ElMessage.error('无权操作此技能')
}
```

---

## 11. 测试设计

### 11.1 测试策略

| 测试类型 | 工具 | 覆盖范围 |
|---------|------|---------|
| Store 单元测试 | Vitest | `useSkillStore` 全部 Actions |
| API Mock 测试 | Vitest + vi.fn() | `skillApi` 各接口 |
| 组件测试 | Vitest + @vue/test-utils + jsdom | SkillCard、SkillDialog |

### 11.2 skillStore 测试

```
• fetchSkills 成功后 skills 填充数据
• fetchSkills 失败后 error 设置错误信息
• createSkill 成功后技能插入 skills 数组头部
• updateSkill 成功后对应技能数据更新
• deleteSkill 成功后对应技能从 skills 移除
• toggleSkill 乐观更新 + API 失败后回滚
• builtinSkills getter 正确过滤
• customSkills getter 正确过滤
```

### 11.3 skillApi 测试

```
• fetchSkills 无参数时不传 category
• fetchSkills 有参数时正确携带 category query
• createSkill 发送 POST 请求
• updateSkill 使用 PUT 方法
• deleteSkill 使用 DELETE 方法
• toggleSkill 使用 PATCH 方法携带 { enabled }
```

### 11.4 SkillCard 组件测试

```
• 渲染技能名称、描述、图标
• is_builtin=true 时显示"内置"标签
• is_builtin=true 时隐藏编辑/删除按钮
• is_builtin=false 时显示编辑/删除按钮
• 点击编辑按钮 emit('edit', skill)
• 点击删除按钮 emit('delete', skill)
• 切换开关 emit('toggle', skill)
• 无描述时显示"暂无描述"
```

### 11.5 SkillDialog 组件测试

```
• 创建模式：标题为"创建技能"，表单为空
• 编辑模式：标题为"编辑技能"，表单回填
• 点击确认触发 el-form 校验
• 校验通过后 emit('save', formData)
• 点击取消/关闭 emit('close')
```

---

## 12. 附录

### 12.1 变更文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/types/skill.ts` | **新建** | Skill 类型定义 + 分类常量 |
| `src/services/skillApi.ts` | **新建** | 技能 API 调用 (6 个接口) |
| `src/stores/skill.ts` | **新建** | 技能 Pinia Store |
| `src/components/skill/iconMap.ts` | **新建** | 图标映射 |
| `src/components/skill/SkillCard.vue` | **新建** | 技能卡片组件 |
| `src/components/skill/SkillDialog.vue` | **新建** | 创建/编辑对话框 |
| `src/views/SkillsView.vue` | **新建** | 技能管理页面 |
| `src/router/index.ts` | 修改 | 添加 `/skills` 路由 |
| `src/components/SideMenu.vue` | 修改 | Skills 菜单联动（路由导航 + 高亮） |

### 12.2 内置技能数据（前端展示参考）

技能数据由后端种子数据初始化，前端通过 API 获取。以下为 5 个内置技能的预期展示数据：

| 名称 | 图标 | 分类 | 描述 |
|------|------|------|------|
| 网络搜索 | Globe | search | 实时搜索互联网信息，获取最新数据 |
| 代码解释器 | Code2 | code | 在安全沙箱中执行代码，支持数据分析 |
| 图像生成 | Image | creative | 根据文本描述生成高质量图像 |
| 数据分析 | ChartBar | analysis | 处理结构化数据，生成统计报告和图表 |
| 文件管理 | FolderOpen | tools | 读写多种格式文件，支持批量处理 |

### 12.3 图标预设列表

`iconMap.ts` 中已注册的 Lucide 图标：

`Globe`, `Code2`, `Image`, `ChartBar`, `FolderOpen`, `Zap`, `Search`, `FileText`, `Database`, `Palette`, `Music`, `Wrench`

用户可在创建自定义技能时输入 `icon` 字段指定图标名称（对应 Lucide 图标组件名），未匹配的图标名 fallback 到 `Zap`。

### 12.4 响应式布局

- ≥1024px: 左侧 SideMenu (220px) + 右侧技能管理区
- 768–1023px: SideMenu 可折叠为 56px，技能内容区自适应
- <768px: SideMenu 完全隐藏，技能内容区 100% 宽度

响应式断点沿用 `mixins.scss` 中已有的 `$breakpoint-lg` (1024px) 和 `$breakpoint-md` (768px)。

### 12.5 npm 脚本

开发过程中使用的命令：

```bash
npm run dev          # 启动开发服务器，访问 /skills 页面
npm run test         # 运行全部测试
npm run test:watch   # 开发模式测试
npm run type-check   # TypeScript 类型检查
npm run lint         # ESLint 代码检查
```

---

> 本文档仅包含前端内容，后端设计参见 [Ke-Hermes Skills 功能模块详细设计说明书-1.0.0](../../../docs/Ke-Hermes-Skills%20功能模块详细设计说明书-1.0.0.md)。实现过程中如需偏离本文档设计，需在 PR 中说明理由并同步更新此文档。
