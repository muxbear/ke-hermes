# Ke-Hermes 详细设计说明书 — v1.4.0

| 版本    | 日期         | 作者  | 变更说明                                         |
| ----- | ---------- | --- | -------------------------------------------- |
| 1.0.0 | 2026-05-18 | -   | 登录模块详细设计初版，基于需求说明书 v1.1.0                      |
| 1.1.0 | 2026-05-18 | -   | 完成前端重构实施：JS→TS 迁移、登录模块全部组件、暗色主题、测试套件、Element Plus 集成 |
| 1.2.0 | 2026-05-18 | -   | 新增聊天模块详细设计：基于 requirements.md 进行全面需求分析，补充 AppShell 三栏布局、消息流、SSE 流式对话、Markdown 渲染、chatStore/uiStore 状态管理的完整设计方案 |
| 1.2.1 | 2026-05-19 | -   | 文档对照实际代码更新：测试目录迁移至 tests/、路由改为 AuthLayout 嵌套结构、普通对话 API 已实现、ChatHeader 模型选择器已实现、auth store 持久化增强、captcha store 新增 smsErrorCount、useAuth 密码加密降级策略 |
| 1.2.2 | 2026-05-22 | -   | 文档对照实际代码更新：chatStore 增加 threadId 状态管理、sendStreamRequest/sendChatRequest 支持 thread_id 参数、SSE 解析增加 onThreadId 回调、clearMessages 重置 threadId、ChatMessage 增加 thread_id 流转 |
| 1.3.0 | 2026-05-26 | -   | 文档对照实际代码更新：新增 MainLayout 根布局组件重构路由结构；新增 MCP 广场模块（列表/详情/安装/卸载）；新增 Skills 技能管理模块（CRUD/仓库导入/本地上传）；新增 conversationApi 服务对接后端对话历史 API；RightPanel 接入真实对话历史数据；SideMenu 增加可折叠菜单分组 + 路由导航；uiStore 重构 HistoryItem/activeThreadId；chatStore 增加 loadConversation |
| 1.4.0 | 2026-05-28 | -   | 新增代理管理模块（Part D）：智能体列表树、多标签配置面板（文件/工具/技能/Cron Jobs）、Vue Flow 主子智能体关系图（拖动/缩放/锁定/最大化）、dagre 自动布局、自定义节点边组件、Agent Store/API/Types 完整设计；TopBar 新增面包屑导航；术语统一（主智能体/子智能体/Cron Jobs）；新增 vue-flow/dagre/vueuse-motion 依赖 |


---

## 目录

**Part A — 基础架构与登录模块**
1. [概述](#1-概述)
2. [项目架构](#2-项目架构)
3. [路由设计](#3-路由设计)
4. [组件设计（登录模块）](#4-组件设计登录模块)
5. [状态管理设计（全局）](#5-状态管理设计全局)
6. [类型定义](#6-类型定义)
7. [API 服务层设计](#7-api-服务层设计)
8. [样式系统设计](#8-样式系统设计)
9. [安全设计](#9-安全设计)
10. [测试设计](#10-测试设计)
11. [国际化设计](#11-国际化设计)
12. [实施记录](#12-实施记录)

**Part B — 聊天模块**
13. [聊天模块概述](#13-聊天模块概述)
14. [聊天页面布局](#14-聊天页面布局)
15. [聊天核心组件设计](#15-聊天核心组件设计)
16. [流式对话（SSE）设计](#16-流式对话sse设计)
17. [聊天状态管理](#17-聊天状态管理)
18. [聊天 API 接口对接](#18-聊天-api-接口对接)
19. [需求对照与合规](#19-需求对照与合规)

**Part C — MCP 广场与技能模块（v1.3.0 新增）**
20. [MCP 广场模块](#20-mcp-广场模块)
21. [Skills 技能管理模块](#21-skills-技能管理模块)

**Part D — 代理管理模块（v1.4.0 新增）**
22. [代理管理模块概述](#22-代理管理模块概述)
23. [代理页面布局](#23-代理页面布局)
24. [代理核心组件设计](#24-代理核心组件设计)
25. [代理关系图设计](#25-代理关系图设计)
26. [代理状态管理](#26-代理状态管理)
27. [代理 API 服务层](#27-代理-api-服务层)
28. [代理类型定义](#28-代理类型定义)

---

## 1. 概述

### 1.1 文档目的

本文档为 Ke-Hermes 前端（桌面版）的详细设计说明书 v1.4.0，基于实际代码库编写。文档覆盖四大核心模块：
- **Part A — 基础架构与登录模块**：TypeScript 技术栈、暗色主题、国际化、测试套件
- **Part B — 聊天模块**：AppShell 三栏布局、SSE 流式对话（含 thread_id 上下文管理）、Markdown 渲染、状态管理、对话历史对接
- **Part C — MCP 广场与技能模块**：MCP 工具广场（浏览/详情/安装/卸载）、Skills 技能管理（CRUD/仓库导入/本地上传/手动创建）
- **Part D — 代理管理模块（v1.4.0 新增）**：智能体列表树、多标签配置面板（文件/工具/技能/Cron Jobs）、Vue Flow 主子智能体关系图（拖动/缩放/锁定/最大化）、dagre 自动布局

文档供前端开发人员编码实现、代码审查和后期维护使用。

### 1.2 技术选型

| 类别       | 选型                     | 版本     |
| -------- | ---------------------- | ------ |
| 框架       | Vue 3                  | ^3.5   |
| 类型系统     | TypeScript             | ~5.5   |
| 路由       | Vue Router             | ^4.4   |
| 状态管理     | Pinia                  | ^2.2   |
| 构建工具     | Vite                   | ^5.4   |
| 测试框架     | Vitest                 | ^2.1   |
| 单元测试工具   | @vue/test-utils        | ^2.4   |
| 组件测试环境   | jsdom                  | ^24.0  |
| UI 组件库   | Element Plus           | ^2.8   |
| HTTP 客户端 | Axios                  | ^1.7   |
| CSS 方案   | SCSS + CSS Variables   | -      |
| 加密       | JSEncrypt              | ^3.3   |
| 国际化      | vue-i18n               | ^9.14  |
| 图标       | lucide-vue-next        | ^0.400 |
| Markdown | marked                 | ^18.0  |
| 组件自动导入  | unplugin-vue-components | ^0.27  |
| 代码格式化   | Prettier               | ^3.3   |
| SCSS     | sass                   | ^1.80  |
| 图引擎      | @vue-flow/core         | ^1.48  | (v1.4.0)|
| 图背景      | @vue-flow/background   | ^1.3   | (v1.4.0)|
| 图控件      | @vue-flow/controls     | ^1.1   | (v1.4.0)|
| 图小地图     | @vue-flow/minimap      | ^1.5   | (v1.4.0)|
| 图布局      | dagre                  | ^0.8   | (v1.4.0)|
| 动画引擎     | @vueuse/motion         | ^2.2   | (v1.4.0)|

### 1.3 适用模块

- **Part A**：PC Web 端登录/注册页面、OAuth 回调处理、路由守卫、Token 刷新、权限校验
- **Part B**：智能体对话界面（三栏布局）、流式 SSE 对话、Markdown 渲染、对话历史管理
- **Part C**：MCP 工具广场、Skills 技能管理（仓库导入/本身上传/手动创建）
- **Part D**：智能体列表管理、配置面板（文件/工具/技能/Cron Jobs）、主子智能体关系图、智能体 CRUD

### 1.4 相关文档

- [Ke-Hermes 需求说明书-登录模块（桌面版）-1.1.0](./Ke%20Hermes%20需求说明书-登录模块（桌面版）-1.1.0.md)
- [ke-hermes 前端需求文档（聊天模块）](./requirements.md)

---

## 2. 项目架构

### 2.1 目录结构（v1.3.0）

```
frontend/
├── index.html                         # 入口 HTML → /src/main.ts
├── package.json
├── tsconfig.json                      # 项目引用根
├── tsconfig.app.json                  # 应用 TS 配置（exclude tests/）
├── tsconfig.node.json                 # 构建工具 TS 配置
├── tsconfig.vitest.json               # 测试 TS 配置（include tests/）
├── vite.config.ts
├── vitest.config.ts                   # 测试配置
├── env.d.ts
├── .env / .env.development / .env.production
├── .prettierrc.json
│
├── public/
│
├── tests/                             # 测试目录
│   ├── setup.ts                       # localStorage/sessionStorage mock
│   ├── stores/
│   │   ├── auth.test.ts               # 7 用例
│   │   └── captcha.test.ts            # 5 用例
│   ├── composables/
│   │   ├── useCountdown.test.ts        # 5 用例
│   │   └── usePasswordEncrypt.test.ts  # 2 用例
│   └── router/
│       └── guards.test.ts             # 4 用例
│
└── src/
    ├── main.ts                        # createApp + pinia + router + i18n + ElementPlus
    ├── App.vue                        # 仅 <RouterView />
    │
    ├── router/
    │   └── index.ts                   # 路由表（MainLayout + AuthLayout 嵌套路由） + 前置守卫
    │
    ├── stores/
    │   ├── auth.ts                    # Token/用户/登录状态
    │   ├── captcha.ts                 # 验证码/倒计时状态
    │   ├── chat.ts                    # 聊天消息 + SSE 流式 + loadConversation
    │   ├── ui.ts                      # UI 状态（侧栏/面板/模型）+ 对话历史（后端对接）
    │   ├── agent.ts                   # 智能体状态（v1.4.0 新增）
    │   ├── mcp.ts                     # MCP 工具状态（v1.3.0 新增）
    │   └── skill.ts                   # Skills 技能状态（v1.3.0 新增）
    │
    ├── types/
    │   ├── api.ts                     # ApiResponse<T>, SendSmsRequest
    │   ├── auth.ts                    # AuthTokens, UserInfo, Request/Response
    │   ├── captcha.ts                 # SlidePuzzleData, SlideVerifyRequest
    │   ├── components.ts              # FeatureItem, OAuthProvider, CaptchaResult
    │   ├── agent.ts                   # Agent, ConfigType, STATUS_LABELS, CONFIG_TYPE_MAP（v1.4.0 新增）
    │   ├── mcp.ts                     # McpTool, McpConfigField, InstallMcpRequest（v1.3.0 新增）
    │   ├── skill.ts                   # Skill, SkillCreateRequest, CATEGORY_LABELS（v1.3.0 新增）
    │   └── router.d.ts                # RouteMeta 扩展
    │
    ├── services/
    │   ├── request.ts                 # Axios 实例 + 拦截器 + SSE + sendChatRequest
    │   ├── authApi.ts                 # 认证接口（8 个）
    │   ├── captchaApi.ts              # 验证码 + 短信接口（5 个）
    │   ├── oauthApi.ts                # OAuth 接口（2 个）
    │   ├── agentApi.ts                # 智能体 Mock API（8 个）（v1.4.0 新增）
    │   ├── conversationApi.ts         # 对话历史 CRUD（4 个）（v1.3.0 新增）
    │   ├── mcpApi.ts                  # MCP 接口（4 个）（v1.3.0 新增）
    │   └── skillApi.ts                # Skills 接口（6 个）（v1.3.0 新增）
    │
    ├── composables/
    │   ├── useAuth.ts                 # 登录逻辑封装 + 重定向 + 密码加密降级
    │   ├── usePasswordEncrypt.ts      # RSA 加密（含公钥缓存）
    │   ├── useCountdown.ts            # 倒计时
    │   ├── useCaptcha.ts              # 验证码流程
    │   ├── useAgreement.ts            # 协议勾选
    │   └── useAgentGraph.ts           # 智能体关系图数据 + dagre 布局（v1.4.0 新增）
    │
    ├── components/
    │   ├── MainLayout.vue             # 认证页面根布局（SideMenu + TopBar + RouterView）（v1.3.0 新增）
    │   ├── AppShell.vue               # 聊天三栏布局容器（ChatMain + RightPanel）
    │   ├── ChatMain.vue               # 中间聊天主区域
    │   ├── ChatHeader.vue             # 聊天头部（含模型下拉选择器）
    │   ├── MessageList.vue            # 消息列表（自动滚动）
    │   ├── MessageItem.vue            # 单条消息（Markdown 渲染）
    │   ├── InputBar.vue               # 消息输入栏（含 + 弹出菜单）
    │   ├── SideMenu.vue               # 可折叠左侧导航菜单（路由导航 + 可折叠分组）
    │   ├── TopBar.vue                 # 顶部搜索 + 通知 + 用户菜单
    │   ├── RightPanel.vue             # 可折叠右侧历史面板（后端对话数据对接）
    │   ├── auth/
    │   │   ├── AuthLayout.vue         # 认证页根布局（左品牌 + 右 RouterView）
    │   │   ├── BrandPanel.vue         # 左侧品牌面板
    │   │   ├── FeatureGrid.vue        # 2×4 特性网格
    │   │   ├── LoginCard.vue          # 520px 毛玻璃卡片
    │   │   ├── LoginTabs.vue          # 登录方式切换标签
    │   │   ├── AccountLoginForm.vue    # 账号密码登录表单
    │   │   ├── PhoneLoginForm.vue      # 手机验证码登录表单
    │   │   ├── AgreementCheckbox.vue   # 协议勾选区
    │   │   ├── OAuthPanel.vue         # 第三方登录图标面板
    │   │   ├── RegisterLink.vue        # 注册入口链接
    │   │   ├── RegisterForm.vue        # 手机号注册表单
    │   │   └── EmailRegisterForm.vue   # 邮箱注册表单
    │   ├── common/
    │   │   ├── PasswordInput.vue       # 密码显隐输入框
    │   │   ├── CountdownButton.vue     # 倒计时发送按钮
    │   │   └── FormError.vue          # 表单错误提示
    │   ├── captcha/
    │   │   ├── CaptchaModal.vue        # 验证码弹窗 (Teleport)
    │   │   ├── SlidePuzzle.vue         # 滑动拼图验证码
    │   │   └── ImageCaptcha.vue        # 图形验证码降级方案
    │   ├── mcp/
    │   │   └── McpCard.vue            # MCP 工具卡片（v1.3.0 新增）
    │   ├── agent/
    │   │   ├── AgentListItem.vue      # 智能体列表树节点（v1.4.0 新增）
    │   │   ├── AgentDetail.vue        # 智能体详情 + 标签配置面板（v1.4.0 新增）
    │   │   ├── AgentGraph.vue         # 主子智能体关系图组件（v1.4.0 新增）
    │   │   ├── AgentNode.vue          # 自定义 Vue Flow 节点（v1.4.0 新增）
    │   │   ├── AgentEdge.vue          # 自定义 Vue Flow 边（v1.4.0 新增）
    │   │   └── AddConfigDialog.vue    # 添加配置弹窗（v1.4.0 新增）
    │   └── skill/
    │       ├── SkillCard.vue           # Skills 技能卡片（v1.3.0 新增）
    │       ├── SkillDialog.vue         # Skills 创建/编辑弹窗（3 标签页）（v1.3.0 新增）
    │       └── iconMap.ts             # Skills 图标映射（v1.3.0 新增）
    │
    ├── views/
    │   ├── HomeView.vue               # 受保护首页（包裹 AppShell）
    │   ├── LoginView.vue              # 登录页
    │   ├── RegisterView.vue           # 注册页
    │   ├── EmailRegisterView.vue      # 邮箱注册页
    │   ├── OAuthCallbackView.vue      # OAuth 回调处理页
    │   ├── SkillsView.vue             # Skills 管理页面（v1.3.0 新增）
    │   ├── McpSquareView.vue          # MCP 广场页面（v1.3.0 新增）
    │   ├── McpDetailView.vue          # MCP 工具详情页面（v1.3.0 新增）
    │   └── AgentsView.vue             # 智能体管理页面（v1.4.0 新增）
    │
    ├── assets/
    │   └── styles/
    │       ├── variables.css          # 暗色主题 Token + Legacy 兼容映射
    │       ├── fonts.css              # Inter + Noto Sans SC 字体
    │       ├── mixins.scss            # 响应式/grid-card/input-focus mixins
    │       └── main.css               # 全局重置
    │
    └── locales/
        ├── index.ts                   # vue-i18n Composition API 模式
        └── zh-CN.ts                   # 简体中文语言包
```

### 2.2 模块分层

```
Views (HomeView, LoginView, SkillsView, McpSquareView, ...)
  └── Components (MainLayout, AppShell, SkillCard, McpCard, ...)
       └── Composables (useAuth, useCaptcha, useCountdown, ...)
            ├── Stores (auth, captcha, chat, ui, mcp, skill)
            └── Services (request, authApi, captchaApi, oauthApi, conversationApi, mcpApi, skillApi)
                 └── Types (auth, api, captcha, components, mcp, skill)
```

### 2.3 v1.2.2 → v1.3.0 实施偏差

| 设计项 | v1.2.2 计划 | v1.3.0 实施 | 原因 |
|--------|------------|------------|------|
| 对话历史 | RightPanel 硬编码 5 条预设 | 对接后端 Conversation API，动态加载 | 后端对话历史 CRUD 已实现 |
| 路由结构 | HomeView 直接包裹 AppShell | 新增 MainLayout 作为认证页面根布局，HomeView/SkillsView/McpSquareView 为嵌套子路由 | 支持多页面导航 |
| 侧栏导航 | 静态菜单无路由 | SideMenu 使用 vue-router 导航，菜单可折叠分组，支持路由高亮 | 支持 MCP 广场和 Skills 页面入口 |
| MCP 广场 | 无 | 完整实现：列表（搜索/分类/排序）+ 详情（概述/配置/使用说明/评价）+ 安装/卸载 | 需求"前端增加了 MCP 广场功能" |
| Skills 管理 | 无 | 完整实现：列表（分类筛选/统计）+ CRUD + 仓库导入 + 本地上传 + 手动创建 | 需求"前端添加技能功能模块" |
| Token 存储 | request.ts 读写 localStorage + sessionStorage | 统一使用 sessionStorage | 简化策略，标签页级别隔离 |

---

## 3. 路由设计

### 3.1 路由表（v1.3.0 重构）

| 路径               | 名称              | 组件 (懒加载)                       | Meta                         |
| ----------------- | --------------- | ------------------------------ | ---------------------------- |
| `/`               | home            | MainLayout → `@/views/HomeView.vue` (child) | requiresAuth: true           |
| `/skills`         | skills          | MainLayout → `@/views/SkillsView.vue` (child) | requiresAuth: true, title: 'Skills' |
| `/agents`         | agents          | MainLayout → `@/views/AgentsView.vue` (child) | requiresAuth: true, title: '代理' | (v1.4.0)|
| `/mcp`            | mcp-square      | MainLayout → `@/views/McpSquareView.vue` (child) | requiresAuth: true, title: 'MCP 广场' |
| `/mcp/:id`        | mcp-detail      | MainLayout → `@/views/McpDetailView.vue` (child) | requiresAuth: true, title: 'MCP 详情' |
| `/login`          | login           | AuthLayout → `@/views/LoginView.vue` (child) | guest: true, title: '登录'     |
| `/register`       | register        | AuthLayout → `@/views/RegisterView.vue` (child) | guest: true, title: '注册'     |
| `/register/email` | register-email  | AuthLayout → `@/views/EmailRegisterView.vue` (child) | guest: true, title: '邮箱注册' |
| `/oauth/callback` | oauth-callback  | `@/views/OAuthCallbackView.vue` | guest: true, title: '第三方登录' |
| `/:pathMatch(.*)*`| not-found       | — (redirect → /)               | —                            |

**v1.3.0 路由重构要点：**

- **MainLayout** 作为所有需认证页面的父布局组件（`/`，`/skills`，`/mcp`，`/mcp/:id`），内部包含 SideMenu + TopBar + `<RouterView />`
- **AuthLayout** 仅包裹认证页面（`/login`，`/register`，`/register/email`）
- 路由守卫逻辑不变：`requiresAuth` → 未登录跳转 `/login`；`guest` → 已登录跳转 `/`

### 3.2 路由守卫逻辑

```
beforeEach:
  requiresAuth && !isAuthenticated → /login?redirect=原路径
  guest && isAuthenticated → /
  其他 → 放行
```

### 3.3 MainLayout 组件（v1.3.0 新增）

```vue
<template>
  <div class="main-layout">
    <SideMenu />
    <div class="right-area">
      <TopBar />
      <div class="work-area">
        <RouterView />
      </div>
    </div>
  </div>
</template>
```

- 左侧：可折叠 SideMenu（导航菜单）
- 右侧：TopBar（搜索/通知/用户）+ RouterView（工作区）
- 取代 v1.2.2 中 HomeView 直接包裹 AppShell 的结构
- 原有 AppShell 三栏布局保留在 HomeView 内部，仅用于聊天页面

---

## 4. 组件设计（登录模块）

（与 v1.2.2 保持一致，无变更。）

### 4.1 组件树

```
AuthLayout.vue
├── BrandPanel.vue
│   ├── Logo (Inline SVG, 96×96, 蓝紫渐变)
│   ├── "Ke-Hermes" (36px/700)
│   ├── "自我进化，越用越强" (20px)
│   ├── FeatureGrid.vue (2×4 网格, 8 特性)
│   └── "2026 Ke-Hermes 版权所有" (12px)
└── <RouterView />
    └── LoginView.vue
        └── LoginCard.vue (max-width 520px, glass-card)
            ├── LoginTabs.vue (账号登录 / 手机登录)
            ├── AccountLoginForm.vue / PhoneLoginForm.vue
            ├── AgreementCheckbox.vue
            ├── el-button (登录按钮, 52px, 蓝色渐变)
            ├── OAuthPanel.vue (5 个 52×52 圆形图标)
            └── RegisterLink.vue (→ /register)
```

---

## 5. 状态管理设计（全局）

### 5.1 authStore (src/stores/auth.ts)

| State | 类型 | 说明 |
|-------|------|------|
| tokens | `AuthTokens \| null` | JWT Token 对 |
| user | `UserInfo \| null` | 当前用户信息 |
| loginLoading | `boolean` | 登录请求进行中 |
| loginError | `string \| null` | 最近登录错误消息 |
| agreedProtocolVersion | `string \| null` | 已同意的协议版本 |

| Action | 说明 |
|--------|------|
| loginWithPassword | 调用 authApi.accountLogin → setTokens + setUser |
| loginWithPhone | 调用 authApi.phoneLogin → setTokens + setUser |
| logout | 调用 authApi.logout → clearTokens |
| refreshAccessToken | 去重锁机制，防止并发刷新 |
| setTokens(t, rememberMe?) | rememberMe=true → localStorage，反之 sessionStorage |
| clearTokens | 清空 tokens + user |

### 5.2 captchaStore (src/stores/captcha.ts)

| State | 类型 | 说明 |
|-------|------|------|
| modalVisible | `boolean` | 验证码弹窗可见性 |
| captchaType | `'slide' \| 'image'` | 验证码类型 |
| pendingAction | `PendingAction \| null` | 验证通过后的待处理操作 |
| smsCountdown | `number` | 短信重发倒计时 |
| smsErrorCount | `number` | 短信发送失败次数 |
| dailySmsCount | `number` | 当日已发送短信次数 |

### 5.3 MCP Store (src/stores/mcp.ts)（v1.3.0 新增）

| State | 类型 | 说明 |
|-------|------|------|
| tools | `McpTool[]` | MCP 工具列表 |
| currentTool | `McpTool \| null` | 当前查看的工具详情 |
| loading | `boolean` | 列表加载中 |
| detailLoading | `boolean` | 详情加载中 |
| error | `string \| null` | 错误消息 |

| Getter | 说明 |
|--------|------|
| installedTools | 已安装的工具列表 |
| officialTools | 官方工具列表 |

| Action | 说明 |
|--------|------|
| fetchTools(params?) | 获取工具列表（支持 category/search/sort） |
| fetchToolById(id) | 获取工具详情 |
| installTool(id) | 安装工具（调用 API + 更新本地状态） |
| uninstallTool(id) | 卸载工具（调用 API + 更新本地状态） |

### 5.4 Skill Store (src/stores/skill.ts)（v1.3.0 新增）

| State | 类型 | 说明 |
|-------|------|------|
| skills | `Skill[]` | 技能列表 |
| loading | `boolean` | 加载中 |
| error | `string \| null` | 错误消息 |

| Getter | 说明 |
|--------|------|
| builtinSkills | 内置技能（is_builtin=true） |
| customSkills | 自定义技能（is_builtin=false） |
| enabledSkills | 已启用的技能 |
| disabledSkills | 已禁用的技能 |
| categoryStats | 分类统计: `{ [category]: { total, enabled, disabled } }` |

| Action | 说明 |
|--------|------|
| fetchSkills(category?) | 获取技能列表 |
| addSkill(data) | 创建技能 |
| editSkill(id, data) | 更新技能 |
| removeSkill(id) | 删除技能 |
| toggleSkillEnabled(id, enabled) | 切换启用/禁用（乐观更新 + 失败回滚） |

### 5.5 chatStore & uiStore

详见 [Part B — 聊天状态管理](#17-聊天状态管理)。

---

## 6. 类型定义

### 文件清单（v1.3.0 扩展）

| 文件 | 导出类型 |
|------|---------|
| `types/api.ts` | `ApiResponse<T>`, `SendSmsRequest` |
| `types/auth.ts` | `AuthTokens`, `UserInfo`, `AccountLoginRequest`, `PhoneLoginRequest`, `RegisterRequest`, `EmailRegisterRequest`, `AuthResponse`, `LoginFailInfo` |
| `types/captcha.ts` | `SlidePuzzleData`, `SlideVerifyRequest`, `SlideVerifyResponse`, `ImageCaptchaData` |
| `types/components.ts` | `LoginTabItem`, `FeatureItem`, `OAuthProvider`, `CaptchaResult`, `PendingAction` |
| `types/mcp.ts` | `McpTool`, `McpConfigField`, `InstallMcpRequest`, `MCP_CATEGORY_LABELS`, `MCP_CATEGORY_FILTERS` |
| `types/skill.ts` | `Skill`, `SkillCreateRequest`, `CATEGORY_LABELS`, `CATEGORY_FILTERS` |
| `types/router.d.ts` | 扩展 `RouteMeta: { title?, requiresAuth?, guest? }` |

---

## 7. API 服务层设计

### 7.1 request.ts — Axios 实例（v1.3.0 更新）

**Token 存储策略（v1.3.0 变更）：** 统一使用 `sessionStorage` 存储 Token（key: `auth_tokens`），不再区分 localStorage/sessionStorage。

```
请求拦截器: 从 sessionStorage 读取 accessToken → 注入 Authorization header
响应拦截器:
  code≠0 → ApiError
  401 → 从 sessionStorage 读取 refreshToken → POST /auth/refresh (去重锁)
    成功 → 更新 sessionStorage → 重试原请求
    失败 → 清除 sessionStorage → window.location.href='/login'
```

**SSE 流式请求:** `sendStreamRequest()` 函数使用 fetch + ReadableStream 解析 SSE。请求头通过 `chatAuthHeaders()` 注入 JWT Token。

### 7.2 API 模块（v1.3.0 扩展）

| 模块 | 接口方法 |
|------|---------|
| authApi | accountLogin, phoneLogin, register, emailRegister, logout, refreshToken, getFailCount, getPublicKey |
| captchaApi | getSlidePuzzle, verifySlide, sendSms, getImageCaptcha, verifyImageCaptcha |
| oauthApi | getAuthUrl, handleCallback |
| conversationApi | fetchConversations, fetchConversationMessages, renameConversation, deleteConversation |
| mcpApi | fetchMcpTools, fetchMcpToolById, installMcpTool, uninstallMcpTool |
| skillApi | fetchSkills, createSkill, fetchSkill, updateSkill, deleteSkill, toggleSkill |

---

## 8. 样式系统设计

（与 v1.2.2 保持一致，无变更。）

---

## 9. 安全设计

### 9.1 密码加密

```
fetchPublicKey() → authApi.getPublicKey() → JSEncrypt.setPublicKey()
encrypt(password) → JSEncrypt.encrypt() → 提交加密后的密文
```

降级策略：若获取公钥失败，自动降级为明文传输密码（开发阶段兼容方案）。

### 9.2 Token 管理（v1.3.0 简化）

| 场景 | 存储 | 有效期 |
|------|------|--------|
| 所有登录 | sessionStorage | 标签页生命周期 |

### 9.3 请求安全

- Authorization Bearer 头注入（含 SSE 流式请求）
- 401 → 自动刷新 Token（去重锁）
- 密码不进 URL，POST Body 传输

---

## 10. 测试设计

### 10.1 测试配置

```typescript
// vitest.config.ts
environment: 'jsdom'
globals: true
include: ['tests/**/*.{test,spec}.{ts,tsx}']
server: { deps: { inline: ['element-plus'] } }
```

### 10.2 测试结果 (24 tests, 6 files)

| 文件 | 数量 | 覆盖内容 |
|------|------|---------|
| `stores/auth.test.ts` | 7 | 登录成功/失败, Token 持久化, 登出, 并发刷新去重锁, 刷新失败处理 |
| `stores/captcha.test.ts` | 5 | modal 显隐, pendingAction, canSendSms, 倒计时, reset |
| `composables/useCountdown.test.ts` | 5 | 初始值, 每秒递减, isActive, stop, 不超 0 |
| `composables/usePasswordEncrypt.test.ts` | 2 | 公钥获取缓存, 加密输出非空 |
| `router/guards.test.ts` | 4 | 未登录→/login, 已登录→/login 被拦截, 未登录可访问 guest 路由, query 参数保留 |

### 10.3 执行命令

```bash
npm run test           # 运行全部测试
npm run test:watch     # watch 模式
npm run test:coverage  # 覆盖率报告
```

---

## 11. 国际化设计

（与 v1.2.2 保持一致，无变更。）

---

## 12. 实施记录

### 12.1 v1.3.0 文件变更统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 新增文件 | 15 | MainLayout, McpCard, SkillCard, SkillDialog, iconMap, conversationApi, mcpApi, skillApi, mcp store, skill store, mcp types, skill types, SkillsView, McpSquareView, McpDetailView |
| 重构文件 | 6 | router/index.ts, stores/ui.ts, stores/chat.ts, services/request.ts, SideMenu.vue, RightPanel.vue |

### 12.2 npm 脚本

| 命令 | 用途 |
|------|------|
| `npm run dev` | 启动 Vite 开发服务器 |
| `npm run build` | 并行类型检查 + 生产构建 |
| `npm run type-check` | 仅类型检查 |
| `npm run test` | 运行测试 |
| `npm run lint` | ESLint 检查 |
| `npm run format` | Prettier 格式化 |

---

## 13. 聊天模块概述

### 13.1 需求来源

聊天模块设计基于 `requirements.md`，定义了 5 项功能需求：F1 对话界面、F2 普通对话、F3 流式对话、F4 状态管理、F5 界面样式。

### 13.2 v1.3.0 对话历史对接

v1.3.0 将 RightPanel 从硬编码历史数据升级为对接后端 Conversation API：

- 组件挂载时调用 `uiStore.fetchHistories()` → `conversationApi.fetchConversations()` 从后端获取真实对话列表
- 点击历史项 → `chatStore.loadConversation(threadId)` → `conversationApi.fetchConversationMessages(threadId)` 加载消息
- 删除历史 → `uiStore.deleteHistory(threadId)` → `conversationApi.deleteConversation(threadId)` 调用后端删除
- 新对话完成后自动刷新历史列表（`sendMessage` 的 `onDone` 回调中调用 `uiStore.fetchHistories()`）

### 13.3 技术要点

| 项目 | 技术 | 说明 |
|------|------|------|
| 布局 | Flexbox 三栏 | SideMenu(左) + MainColumn(中) + RightPanel(右) |
| 页面框架 | MainLayout | SideMenu + TopBar + RouterView，支持多页面导航 |
| 流式通信 | fetch + ReadableStream | 手动解析 SSE `data: { "token": "..." }\n\n` 格式 |
| Markdown | marked 库 | 智能体回复渲染为富文本 |
| 自动滚动 | watch + nextTick + scrollTop | 监听 messages.length 和 lastContent 变化 |

---

## 14. 聊天页面布局

### 14.1 页面层级（v1.3.0）

```
MainLayout.vue (flex row, 100vh)
├── SideMenu (220px / 56px 折叠)
└── right-area (flex:1, flex column)
    ├── TopBar (52px)
    └── work-area (flex:1)
        └── <RouterView />
            └── HomeView.vue
                └── AppShell.vue (flex row)
                    ├── ChatMain (flex:1)
                    │   ├── ChatHeader (48px)
                    │   ├── MessageList (flex:1)
                    │   └── InputBar
                    └── RightPanel (280px / 40px 折叠)
```

**v1.3.0 变更：** MainLayout 作为外层框架提供 SideMenu + TopBar，AppShell 仅在 HomeView 内使用，负责聊天区域的三栏布局（ChatMain + RightPanel）。

---

## 15. 聊天核心组件设计

### 15.1 MainLayout（v1.3.0 新增）

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/MainLayout.vue` |
| 功能 | 认证页面根布局，包含 SideMenu + TopBar + RouterView |
| 样式 | `display: flex; height: 100vh;` |

### 15.2 AppShell

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/AppShell.vue` |
| 功能 | 聊天页三栏布局（ChatMain + RightPanel） |
| 状态依赖 | uiStore（sidebar/panel 折叠态） |

### 15.3 SideMenu（v1.3.0 重构）

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/SideMenu.vue` |
| 功能 | 可折叠左侧导航菜单，支持菜单分组折叠/展开、路由导航、路由高亮 |

**菜单分组（v1.3.0）：**

| 分组 | 项目 |
|------|------|
| 聊天 | 对话 (→ /) |
| 控制 | 概览, 实例, 会话, 使用情况, 定时任务 |
| 代理 | 代理 (→ /agents), 技能 Hub (→ /skills), 节点 |
| 设置 | 配置, 文档 |
| 后台 | 后台 |

- 分组可点击折叠/展开（ChevronDown 旋转动画）
- 菜单项通过 `isItemActive()` 匹配 `route.path` 高亮
- 点击菜单项调用 `router.push(item.route)` 导航

### 15.4 RightPanel（v1.3.0 重构）

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/RightPanel.vue` |
| 功能 | 可折叠右侧历史对话面板，对接后端 Conversation API |
| 数据来源 | `uiStore.histories`（通过 `fetchHistories()` 从后端获取） |
| 点击历史 | `chatStore.loadConversation(threadId)` → 加载消息并渲染 |
| 删除历史 | `uiStore.deleteHistory(threadId)` → 后端删除 + 本地更新 |

### 15.5 TopBar（v1.4.0 更新）

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/TopBar.vue` |
| 功能 | 顶部栏：面包屑导航 + 搜索框 + 通知 + 用户菜单 |

**v1.4.0 变更：**
- 搜索框从左侧移至右侧（靠右对齐）
- 左侧新增面包屑：根据 `useRoute()` 显示当前激活菜单的全路径（如 `聊天 > 对话`、`代理 > 代理`），路由映射在 `breadcrumb` computed 中
- 面包屑样式：分组名灰色 + ChevronRight 分隔符 + 当前项高亮

**路由到面包屑映射：**

| 路由 | 面包屑 |
|------|--------|
| `/` | 聊天 > 对话 |
| `/agents` | 代理 > 代理 |
| `/skills` | 代理 > 技能 Hub |
| `/mcp` | MCP > MCP 广场 |

### 15.6 MessageList / MessageItem / InputBar / ChatHeader

（与 v1.2.2 保持一致。）

---

## 16. 流式对话（SSE）设计

### 16.1 数据流（v1.3.0 更新）

```
用户输入 → InputBar.handleSend()
         → chatStore.sendMessage(text)
           ├─ 追加 user 消息到 messages[]
           ├─ 创建空 assistant 消息（streaming=true）
           ├─ 调用 sendStreamRequest(text, { threadId, onToken, onThreadId, onDone, onError })
           │   ├─ fetch POST /api/chat/stream
           │   ├─ ReadableStream 解析 SSE
           │   ├─ onToken(token) → assistantMsg.content += token
           │   ├─ onThreadId(id) → chatStore.threadId = id
           │   └─ onDone() → streaming=false, loading=false
           │       └─ uiStore.activeThreadId = threadId
           │       └─ uiStore.fetchHistories()  ← v1.3.0 新增：自动刷新历史列表
           └─ onError() → 追加错误文本
```

### 16.2 SSE 解析实现

```typescript
function parseSseDataLine(line, onToken, onThreadId?): void {
  if (!line.startsWith('data: ')) return
  const json = JSON.parse(line.slice(6))
  if (json.token) onToken(json.token)
  if (json.thread_id && onThreadId) onThreadId(json.thread_id)
}
```

---

## 17. 聊天状态管理

### 17.1 chatStore（v1.3.0 更新）

| State | 类型 | 说明 |
|-------|------|------|
| `messages` | `Ref<ChatMessage[]>` | 所有消息 |
| `loading` | `Ref<boolean>` | 等待流式回复中 |
| `threadId` | `Ref<string \| null>` | 当前对话线程 ID |

| Action | 说明 |
|--------|------|
| `sendMessage(text)` | 发送消息 → SSE 流式接收 → onDone 中自动刷新历史列表 |
| `clearMessages()` | 清空消息 + 重置 loading + 重置 threadId |
| `loadConversation(tid)` | **v1.3.0 新增**：从后端加载指定对话的消息并渲染 |

```typescript
async function loadConversation(tid: string) {
  threadId.value = tid
  loading.value = true
  const detail = await fetchConversationMessages(tid)
  messages.value = detail.messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .map((m, idx) => ({ id: idx + 1, role: m.role, content: m.content, streaming: false }))
  nextId = messages.value.length + 1
  loading.value = false
}
```

### 17.2 uiStore（v1.3.0 重构）

| State | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `sidebarCollapsed` | `boolean` | `false` | 左侧菜单折叠态 |
| `rightPanelCollapsed` | `boolean` | `false` | 右侧面板折叠态 |
| `plusMenuOpen` | `boolean` | `false` | 附件弹出菜单 |
| `searchQuery` | `string` | `''` | 搜索框输入 |
| `selectedModel` | `string` | `'DeepSeek V4'` | 当前选中模型 |
| `histories` | `HistoryItem[]` | `[]` | 对话历史列表（从后端获取） |
| `activeThreadId` | `string \| null` | `null` | 当前活跃对话线程 ID |

| Action | 说明 |
|--------|------|
| `fetchHistories()` | **v1.3.0 新增**：从后端获取对话列表 |
| `deleteHistory(thread_id)` | **v1.3.0 更新**：调用后端 API 删除 + 本地移除 |
| `newConversation()` | 重置 activeThreadId + 关闭菜单 |
| `toggleSidebar()` / `toggleRightPanel()` | 翻转折叠态 |

**v1.3.0 核心变更：**
- `HistoryItem` 接口从 `{id: number, title: string}` → `{thread_id: string, title: string}`
- `activeHistoryId: number` → `activeThreadId: string | null`
- `histories` 从硬编码预设 → `fetchHistories()` 从后端动态加载
- `deleteHistory` 从本地过滤 → 调用 `conversationApi.deleteConversation(thread_id)`

---

## 18. 聊天 API 接口对接

### 18.1 后端接口清单

| 接口 | 方法 | 请求体 | 响应体 | 用途 |
|------|------|--------|--------|------|
| `/api/chat` | POST | `{"message","thread_id?"}` | `{"response","thread_id"}` | 普通对话 |
| `/api/chat/stream` | POST | `{"message","thread_id?"}` | SSE 流 | 流式对话 |
| `/api/conversations` | GET | — | `[{thread_id, title, updated_at}]` | 对话列表 |
| `/api/conversations/{id}` | GET | — | `{thread_id, title, messages}` | 对话消息 |
| `/api/conversations/{id}` | PATCH | `{title}` | `{thread_id, title}` | 重命名 |
| `/api/conversations/{id}` | DELETE | — | — | 删除对话 |

### 18.2 conversationApi 服务（v1.3.0 新增）

```typescript
export async function fetchConversations(): Promise<ConversationItem[]>
export async function fetchConversationMessages(thread_id: string): Promise<ConversationDetail>
export async function renameConversation(thread_id: string, title: string): Promise<{thread_id, title}>
export async function deleteConversation(threadId: string): Promise<void>
```

---

## 19. 需求对照与合规

### 19.1 requirements.md 逐条对照

| 需求编号 | 需求描述 | 实现状态 | 实现文件 |
|---------|---------|---------|---------|
| F1 对话界面 | 上方消息列表 + 下方输入区，左右对齐，自动滚动 | 完全实现 + 超越 | AppShell, MessageList, MessageItem, InputBar |
| F2 普通对话 | POST /api/chat，完整回复 | 已实现 | request.ts sendChatRequest() |
| F3 流式对话 | POST /api/chat/stream，SSE 逐 token 推送 | 完全实现 | request.ts sendStreamRequest, chatStore.sendMessage |
| F4 状态管理 | Pinia chatStore | 完全实现 + 超越 | chatStore + uiStore + mcpStore + skillStore |
| F5 界面样式 | 暗色主题 | 已升级 | v1.1.0 暗色主题 + Legacy 兼容层 |

### 19.2 待实现项

| 项目 | 优先级 | 说明 |
|------|--------|------|
| 搜索功能 | P3 | TopBar 搜索框无实际搜索逻辑 |
| 通知功能 | P3 | TopBar 铃铛按钮无交互 |
| 用户菜单完善 | P3 | 可补充个人设置等入口 |
| 注册表单提交 | P2 | RegisterForm 和 EmailRegisterForm 的 submit 为 TODO 占位 |
| MCP 创建功能 | P3 | "创建 MCP"按钮 TODO 占位 |

---

## 20. MCP 广场模块

### 20.1 概述

MCP 广场模块允许用户浏览、搜索、查看详情、安装和卸载 MCP（Model Context Protocol）工具，扩展 AI 智能体的能力。

### 20.2 页面结构

```
McpSquareView.vue
├── 页面标题 + "创建 MCP" 按钮（TODO）
├── 搜索栏（关键字搜索）
├── 统计卡片（总数 / 已安装 / 本周热门 / 最近更新）
├── 分类筛选按钮（全部/代码执行/搜索/数据分析/文件管理/通知/数据库/开发工具）
├── 排序下拉（最多安装 / 最高评分 / 最近更新）
└── 工具卡片网格
    └── McpCard.vue（每个工具一张卡片）
```

### 20.3 McpCard 组件

| 属性 | 说明 |
|------|------|
| Props | `tool: McpTool` |
| Emits | `click(tool)`, `install(tool)` |

卡片展示内容：图标 + 名称 + 官方标识 + 作者 + 描述 + 标签 + 安装数 + 评分 + 安装/已安装按钮

### 20.4 McpDetailView 详情页

| 标签页 | 内容 |
|--------|------|
| 概述 | 简介 + 核心功能列表 + 信息面板（版本/作者/许可证/仓库/分类/更新）+ 标签 |
| 配置 | 配置参数列表（名称/类型/必填/描述） |
| 使用说明 | 安装方式/运行环境/自动启动说明 |
| 评价 | 用户评价（占位，暂无数据） |

### 20.5 MCP 数据模型

```typescript
interface McpTool {
  id: string; name: string; description: string; icon: string
  author: string; version: string; license: string; repository: string
  installs: number; rating: number; category: string; tags: string[]
  features: string[]; official: boolean; installed: boolean
  config_schema: McpConfigField[]
  created_at: string; updated_at: string
}

interface McpConfigField {
  name: string; label: string
  type: 'string' | 'number' | 'boolean' | 'select'
  required: boolean; default?: any; options?: string[]; description?: string
}
```

### 20.6 MCP 分类

| key | 中文 |
|-----|------|
| code_execution | 代码执行 |
| search | 搜索 |
| data_analysis | 数据分析 |
| file_management | 文件管理 |
| notification | 通知 |
| database | 数据库 |
| dev_tools | 开发工具 |
| collaboration | 协作 |
| container | 容器 |
| custom | 自定义 |

---

## 21. Skills 技能管理模块

### 21.1 概述

Skills 模块提供 AI 智能体技能的完整管理功能：浏览、创建、编辑、删除、启用/禁用，以及从仓库导入和本地上传。

### 21.2 页面结构

```
SkillsView.vue
├── 页面标题 + "创建技能" 按钮
├── 状态横幅（API 错误提示 + 重试）
├── 统计卡片（技能总数 / 已启用 / 已禁用 / 不可用）
├── 分类筛选按钮（全部/搜索/代码/创意/分析/工具）
├── 分类概览面板（每个分类的总数/可用/禁用）
├── 技能列表标题 + 计数
└── 技能卡片网格
    └── SkillCard.vue（每个技能一张卡片）
```

### 21.3 SkillCard 组件

| 属性 | 说明 |
|------|------|
| Props | `skill: Skill` |
| Emits | `edit(skill)`, `delete(skill)`, `toggle(skill)` |

卡片展示内容：图标（Lucide 动态组件）+ 名称 + 内置标识 + 启用开关 + 描述 + 分类标签 + 操作按钮（编辑/删除，仅自定义技能）

### 21.4 SkillDialog 创建/编辑弹窗

| 标签页 | 功能 | 说明 |
|--------|------|------|
| 从仓库下载 | 选择仓库 → 获取技能列表 → 勾选 → 批量导入 | 支持 ClawHub/Anthropic/LangChain/CrewAI/AutoGen + 自定义地址 |
| 本地上传 | 拖拽或点击上传文件 → 校验格式 + 必需字段 | 支持 .json/.yaml/.yml/.md/.zip |
| 手动创建 | 填写表单（名称/描述/图标/分类/Prompt） | 编辑已有技能时直接进入此标签 |

**从仓库下载流程：**
1. 选择仓库（下拉菜单含预设仓库 + 自定义地址）
2. 点击"获取"加载技能列表
3. 搜索/筛选技能
4. 勾选要导入的技能（支持全选当前页）
5. 点击"拉取到本地"批量导入

**本地上传流程：**
1. 拖拽或点击上传 .json/.yaml/.yml/.md/.zip 文件
2. 自动校验：文件格式 → 必需字段（name/description/prompt）
3. 显示校验结果（通过/失败）
4. 点击"导入"确认

### 21.5 Skills 数据模型

```typescript
interface Skill {
  id: string; name: string; description: string; icon: string
  category: string; prompt: string; enabled: boolean
  is_builtin: boolean; user_id: string | null
  created_at: string; updated_at: string
}

interface SkillCreateRequest {
  name: string; description?: string; icon?: string
  category?: string; prompt?: string
}
```

### 21.6 Skills 分类

| key | 中文 |
|-----|------|
| search | 搜索 |
| code | 代码 |
| creative | 创意 |
| analysis | 分析 |
| tools | 工具 |
| custom | 自定义 |

### 21.7 图标映射（iconMap.ts）

支持 12 种 Lucide 图标：Globe, Code2, Image, BarChart3, FolderOpen, Zap, Search, FileText, Database, Palette, Music, Wrench。通过 `getSkillIcon(name)` 函数查找，未匹配时默认返回 Zap。

---

> 本文档 v1.4.0 基于实际代码实现全面更新。v1.4.0 重点新增了代理管理模块：智能体列表树、文件/工具/技能/Cron Jobs 四标签配置面板、基于 Vue Flow 的主子智能体关系图（拖动/缩放/锁定/最大化）、dagre 自动树布局、自定义节点/边组件；TopBar 新增面包屑导航；术语统一（主智能体/子智能体/Cron Jobs）。后续版本应完善搜索功能、通知系统和用户菜单。

---

## 22. 代理管理模块概述

### 22.1 需求背景

代理管理模块（左侧菜单"代理" → `/agents`）提供智能体（Agent）的集中管理功能：树形列表浏览、配置项管理（文件/工具/技能/Cron Jobs）、主子智能体关系图可视化。

### 22.2 核心功能

| 功能 | 说明 |
|------|------|
| 智能体列表树 | 左侧面板，主智能体为根节点，子智能体为子节点，支持搜索过滤、展开/折叠、状态图标 |
| 多标签配置面板 | 右侧面板四个标签页：文件 (Files)、工具 (Tools)、技能 (Skills)、Cron Jobs，点击标签切换 |
| 关系图可视化 | 点击眼睛图标切换，Vue Flow 绘制主子智能体连接关系图 |
| 智能体操作 | 新建子智能体（三点下拉菜单）、克隆、删除（不可删除智能体受保护）、启停状态 |
| 配置管理 | 每个标签页内添加/移除配置项（通过弹窗表单） |

### 22.3 术语规范（v1.4.0）

| 术语 | 说明 |
|------|------|
| 主智能体 | 顶层 Agent，type='main'，可拥有子智能体 |
| 子智能体 | 从属 Agent，type='sub'，挂载于主智能体下 |
| 通用子智能体 | 默认不可删除的子智能体 (sub-1)，具备与主智能体相同的全部工具 |
| 研究子智能体 | 默认子智能体 (sub-2)，专注于网络搜索和深入研究 |
| Cron Jobs | 原"提示词"功能重命名，type='prompt'，定时任务配置 |
| 文件 | 新增配置类型，type='file'，默认 7 个 .md 文件 |

---

## 23. 代理页面布局

### 23.1 页面层级

```
MainLayout.vue
└── work-area → <RouterView />
    └── AgentsView.vue (双栏布局: flex row)
        ├── panel-left (300px, 卡片容器)
        │   ├── panel-left-header
        │   │   ├── title-row: "代理列表" + 计数徽章 + 眼睛切换按钮
        │   │   └── search-box: 搜索输入框
        │   └── panel-left-body
        │       └── AgentListItem.vue（树形递归组件）
        │           └── [递归] AgentListItem（子智能体）
        └── panel-right (flex:1, 卡片容器)
            ├── Transition name="graph-mode" mode="out-in"
            │   ├── AgentGraph.vue（眼睛睁开时）
            │   └── AgentDetail.vue（眼睛闭上时）
            └── detail-empty（无选中时代理提示）
```

### 23.2 双栏切换逻辑

- `showRelationGraph: Ref<boolean>`（默认 `false`）由眼睛按钮切换
- `<Transition name="graph-mode" mode="out-in">` 提供视图切换动画（淡入缩放 / 淡出）
- 关系图模式时右侧全幅显示图，详情模式时显示配置标签面板

---

## 24. 代理核心组件设计

### 24.1 AgentListItem — 智能体列表树节点

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/agent/AgentListItem.vue` |
| Props | `agent: Agent`, `agents: Agent[]`, `selectedId`, `expandedIds`, `searchQuery`, `level` |
| Emits | `select`, `toggleExpand`, `toggleStatus`, `clone`, `delete`, `newSubAgent` |
| 功能 | 递归树节点组件，支持展开/折叠、三点下拉菜单、状态标签 |

**展示内容：** 名称 + 状态标签（运行中/已停止/错误）+ 类型标识（主智能体 Blue 徽章）+ 描述 + 统计（调用数/工具数/技能数/子智能体数）

**三点下拉菜单项：**

| 命令 | 图标 | 说明 |
|------|------|------|
| newSubAgent | UserPlus | 新建子智能体 |
| toggle | Pause/Play | 启动/停止（分隔线前） |
| clone | Copy | 克隆 |
| delete | Trash2 | 删除（分隔线前，红色，v-if="!agent.undeletable" 时显示） |

**v1.4.0 关键特性：**
- 不可删除智能体（`undeletable: true`）隐藏"删除"菜单项
- 搜索时展平显示所有匹配项，无搜索时树形递归渲染
- 选中状态蓝色渐变高亮 + "编辑中"标签

### 24.2 AgentDetail — 智能体详情配置面板

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/agent/AgentDetail.vue` |
| Props | `agent: Agent`, `agents: Agent[]` |
| Emits | `addConfig(type)`, `removeConfig(type, value)`, `toggleStatus`, `selectAgent(id)` |

**Header 区域：**
- 智能体名称 + 状态标签（Activity/Pause/Zap）+ 类型徽章（主智能体/子智能体）
- 描述文本 + 统计栏（调用数、最后活跃、工具数、技能数、文件数、Cron Jobs 数）
- 四个标签按钮：文件（黄色）/ 工具（蓝色）/ 技能（紫色）/ Cron Jobs（绿色）

**Tab 切换逻辑：**
- `activeTab: Ref<ConfigType>`（默认 `'file'`）
- `activeSection: Computed<ConfigSection>` 根据 activeTab 查找当前配置区
- 仅渲染当前激活标签页的配置区块，其余隐藏

**配置区块结构（每个标签页相同模式）：**
```
.config-section
├── .section-header
│   ├── .section-icon（颜色背景 + Lucide 图标）
│   ├── 标签名称 + 计数（"X 个已配置"）
│   └── .add-btn（"添加"按钮，触发 addConfig(type)）
└── .tags-wrap
    ├── .config-tag × N（可删除配置标签，hover 显示删除按钮）
    └── .empty-section（无配置时的空状态提示）
```

**四项配置区定义：**

| type | label | 图标 | 颜色 | key |
|------|-------|------|------|-----|
| file | 文件 (Files) | FileText | yellow (#eab308) | files |
| tool | 工具 (Tools) | Settings | blue (#3b82f6) | tools |
| skill | 技能 (Skills) | Sparkles | purple (#8b5cf6) | skills |
| prompt | Cron Jobs | Clock | green (#22c55e) | prompts |

### 24.3 AddConfigDialog — 添加配置弹窗

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/agent/AddConfigDialog.vue` |
| Props | `visible`, `type: ConfigType`, `agentName`, `agentType` |
| Emits | `close`, `add(type, value)` |

**弹窗内容：** 头部（类型图标 + "添加{类型}" + 目标智能体信息）、表单（名称 + 可选描述）、底部（取消/添加按钮）

**各类型占位提示：**

| type | 名称占位 | 描述占位 |
|------|---------|---------|
| file | 例如: config.yaml, data.json | 描述此文件的用途和内容... |
| tool | 例如: web_search, file_reader | 描述此工具的功能和用途... |
| skill | 例如: code_analysis, debugging | 描述此技能的能力和应用场景... |
| prompt | 例如: 每天执行一次, 每小时检查 | 输入 Cron 表达式和执行任务... |
| subagent | 例如: 数据处理子智能体 | 描述此子智能体的职责和功能... |

---

## 25. 代理关系图设计

### 25.1 整体架构

主子智能体关系图使用 Vue Flow（ReactFlow 的 Vue 3 移植）构建，dagre 自动布局，@vueuse/motion 动画。

### 25.2 AgentGraph — 主图组件

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/agent/AgentGraph.vue` |
| 依赖 | `useAgentGraph()` composable |
| 功能 | Vue Flow 画布容器，包含 header 控制栏、画布区域、空状态 |

**Header 控制栏：**
- 标题"主智能体关系图"
- "实时拓扑"徽章（蓝色描边圆角标签）
- 锁定按钮（Lock/Unlock 图标，切换 `isLocked` 状态）
- 最大化按钮（Maximize2/Minimize2 图标，切换 `isMaximized` 状态）

**Vue Flow 画布：**
```
<VueFlow v-model:nodes="graphNodes" v-model:edges="graphEdges"
  :node-types :edge-types
  :nodes-draggable="!isLocked"
  :pan-on-drag="!isLocked"
  :zoom-on-scroll="!isLocked"
  @node-click @pane-ready>
  <Background pattern-color="rgba(255,255,255,0.04)" />
  <Controls position="bottom-right" />
  <MiniMap position="bottom-left" />
</VueFlow>
```

**交互能力：**

| 操作 | 解锁状态 | 锁定状态 |
|------|---------|---------|
| 画布拖动 | ✓ | ✗ |
| 节点拖动 | ✓ | ✗ |
| 滚轮缩放 | ✓ | ✗ |
| Controls 缩放 | ✓ | ✓ |
| 节点点击 | ✓ | ✓ |
| MiniMap 导航 | ✓ | ✓ |

**最大化模式：** `isMaximized=true` 时组件使用 `position: fixed; inset: 0; z-index: 1000` 覆盖全屏，带动画过渡。

**锁定/解锁按钮：** 点击时旋转动画反馈（CSS transition）。

### 25.3 AgentNode — 自定义 Vue Flow 节点

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/agent/AgentNode.vue` |
| Vue Flow Props | `id`, `data: { agent, isMain }`, `selected` |

**节点卡片设计：**
- **主智能体节点：** `linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%)` 渐变背景，绿色边框 + teal 发光阴影
- **子智能体节点：** `linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%)` 渐变背景，紫色边框 + 紫色发光阴影
- **选中状态：** `box-shadow: 0 0 28px rgba(59, 130, 246, 0.4)` 蓝色增强发光

**卡片内容：**
1. 状态图标（Activity=运行中 / Pause=停止 / Zap=错误）+ 名称 + 类型标签
2. 三列统计网格（工具数 / 技能数 / 子智能体数或调用数）

**Handle 连接点：**
- 主智能体：Source Handle（Bottom，连接子智能体）
- 子智能体：Target Handle（Top，接收主智能体连接）
- 连接不可交互（`:connectable="false"`，`opacity: 0`），仅用于边附着

**拖拽交互：**
- `cursor: grab`（默认）/ `cursor: grabbing`（拖拽中）
- 选中状态蓝色增强发光

### 25.4 AgentEdge — 自定义 Vue Flow 边

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/agent/AgentEdge.vue` |
| Vue Flow Props | `sourceX/Y`, `targetX/Y`, `sourcePosition`, `targetPosition`, `id`, `data: { status }` |

**边样式：**
- 使用 `getBezierPath()` 计算贝塞尔曲线路径
- 活跃代理：蓝紫渐变（`#3b82f6` → `#8b5cf6`）实线 + 紫色箭头（`MarkerType.ArrowClosed`）
- 非活跃代理：灰色渐变（`#6b7280` → `#4b5563`）虚线 (`stroke-dasharray: 6,4`) + 灰色箭头
- 活跃边添加 `animated: true`，产生流动动画

**渐变实现：** 每条边内部定义唯一 ID 的 `<linearGradient>` + `<defs>`，通过 `stroke: url(#edge-grad-{id})` 引用。

### 25.5 useAgentGraph — 图数据 Composables

| 属性 | 说明 |
|------|------|
| 文件 | `src/composables/useAgentGraph.ts` |

**状态管理：**
- `graphNodes: Ref<Node[]>`（`ref` 非 `computed`，支持 Vue Flow v-model 更新位置）
- `graphEdges: Ref<Edge[]>`（`ref`）
- `watch([agentStore.mainAgent, agentStore.subAgents], applyLayout, { deep, immediate })` 监听代理变化重新布局

**构建逻辑：**
- `buildNodes()`: 从 `agentStore.mainAgent` + `agentStore.subAgents` 构建 Node[]，每个节点 `draggable: true`
- `buildEdges()`: 从主智能体向每个子智能体连边
- `applyLayout()`: 调用 dagre 执行 TB 布局

**dagre 布局参数：**
```typescript
const NODE_WIDTH = 240   // .node-card 宽度
const NODE_HEIGHT = 130  // 卡片预估高度
g.setGraph({ rankdir: 'TB', ranksep: 140, nodesep: 120, marginx: 80, marginy: 80 })
```

主智能体在 rank 0（顶部），所有子智能体在 rank 1 对称分布，居中于主智能体下方。

---

## 26. 代理状态管理

### 26.1 agentStore (src/stores/agent.ts)

| State | 类型 | 说明 |
|-------|------|------|
| agents | `Ref<Agent[]>` | 所有智能体 |
| selectedAgentId | `Ref<string \| null>` | 当前选中智能体 ID |
| loading | `Ref<boolean>` | 列表加载中 |
| error | `Ref<string \| null>` | 错误消息 |
| searchQuery | `Ref<string>` | 搜索关键词 |
| expandedIds | `Ref<Set<string>>` | 已展开的智能体 ID 集合 |

| Getter | 说明 |
|--------|------|
| selectedAgent | 当前选中智能体对象 |
| mainAgent | type='main' 的智能体 |
| subAgents | type='sub' 的所有智能体 |
| filteredAgents | 搜索时展平匹配，无搜索时返回主智能体（树根） |
| stats | { total, active, inactive, error } 计数 |

| Action | 说明 |
|--------|------|
| fetchAgents | 调用 agentApi.fetchAgents() 加载列表，默认选中主智能体 |
| selectAgent(id) | 设置 selectedAgentId |
| toggleExpand(id) | 在 expandedIds 中添加/移除 |
| expandAll / collapseAll | 全展开 / 全折叠 |
| toggleStatus(id) | 调用 agentApi.toggleAgentStatus() 切换运行/停止 |
| cloneAgent(id) | 调用 agentApi.cloneAgent() 克隆 |
| deleteAgent(id) | 调用 agentApi.deleteAgent() 删除 |
| addConfig(type, value) | 调用 agentApi.addConfig() 添加配置 |
| removeConfig(type, value) | 调用 agentApi.removeConfig() 移除配置 |
| createSubAgent(name) | 调用 agentApi.createAgent() 创建子智能体，自动展开主智能体并选中新节点 |

---

## 27. 代理 API 服务层

### 27.1 agentApi — Mock 实现

| 属性 | 说明 |
|------|------|
| 文件 | `src/services/agentApi.ts` |
| 说明 | Mock 实现，后端 Agent CRUD API 就绪后仅需替换本文件内部实现 |

**Mock 数据（v1.4.0）：**

| ID | 名称 | 类型 | 状态 | 说明 |
|----|------|------|------|------|
| main-agent | 主智能体 | main | active | 负责整体任务协调和分发 |
| sub-1 | 通用子智能体 | sub | active | `undeletable: true`，具备与主智能体相同的全部工具 |
| sub-2 | 研究子智能体 | sub | inactive | 专门用于使用网络搜索进行深入研究并综合分析结果 |

**默认文件（所有智能体共享 7 个 .md）：**
`AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `MEMORY.md`

**API 方法：**

| 方法 | 说明 |
|------|------|
| fetchAgents() | 返回所有智能体（deepClone） |
| createAgent(data) | 创建新子智能体（id: `sub-{timestamp}`），加入主智能体 subAgents |
| deleteAgent(id) | 删除智能体（`undeletable` 保护：抛出错误），从主智能体移除 |
| toggleAgentStatus(id) | 切换 active ↔ inactive 状态 |
| cloneAgent(id) | 克隆智能体（name + "(副本)"，id + "-clone-{timestamp}"） |
| addConfig(agentId, type, value) | 添加配置项（支持 tool/skill/file/prompt/subagent） |
| removeConfig(agentId, type, value) | 移除配置项 |

---

## 28. 代理类型定义

### 28.1 Agent 接口（src/types/agent.ts）

```typescript
export interface Agent {
  id: string
  name: string
  type: 'main' | 'sub'
  status: 'active' | 'inactive' | 'error'
  tools: string[]
  skills: string[]
  prompts: string[]
  files: string[]           // v1.4.0 新增
  subAgents?: string[]
  parentId?: string
  description?: string
  lastActive?: string
  callCount?: number
  undeletable?: boolean     // v1.4.0 新增
}
```

### 28.2 ConfigType 与配置映射

```typescript
export type ConfigType = 'tool' | 'skill' | 'prompt' | 'subagent' | 'file'

export const STATUS_LABELS: Record<string, string> = {
  active: '运行中', inactive: '已停止', error: '错误',
}

export const CONFIG_TYPE_MAP: Record<ConfigType, { label; color; bgClass }> = {
  tool:     { label: '工具',   color: '#3b82f6', bgClass: 'config--blue' },
  skill:    { label: '技能',   color: '#8b5cf6', bgClass: 'config--purple' },
  prompt:   { label: '提示词', color: '#22c55e', bgClass: 'config--green' },
  subagent: { label: '子代理', color: '#f97316', bgClass: 'config--orange' },
  file:     { label: '文件',   color: '#eab308', bgClass: 'config--yellow' },
}
```
