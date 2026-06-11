# Ke-Hermes 前端需求说明书 — v1.6.0

| 版本  | 日期       | 作者 | 变更说明                                                     |
| ----- | ---------- | ---- | ------------------------------------------------------------ |
| 1.0.0 | 2026-05-18 | -    | 初版：对话界面、普通/流式对话、Pinia 状态管理、基础目录结构  |
| 1.6.0 | 2026-06-11 | -    | 新增 12 个页面视图、认证体系（RSA+JWT+CAPTCHA+OAuth+SMS+邮箱）、智能体管理（CRUD+配置+文件+技能关联+关系图+CronJob）、模型管理、MCP 广场、Skills/Tools 管理、知识库（Mock）、定时任务（Mock）、概览仪表盘（ECharts）；Element Plus 暗色主题、TypeScript、vue-i18n、10 个 Pinia Store、12 个 API Service 模块、6 个 Composable |

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [路由设计](#3-路由设计)
4. [功能需求](#4-功能需求)
   - 4.1 [认证体系](#41-认证体系)
   - 4.2 [对话界面](#42-对话界面)
   - 4.3 [智能体管理](#43-智能体管理)
   - 4.4 [模型管理](#44-模型管理)
   - 4.5 [MCP 广场](#45-mcp-广场)
   - 4.6 [Skills 技能管理](#46-skills-技能管理)
   - 4.7 [Tools 工具管理](#47-tools-工具管理)
   - 4.8 [知识库](#48-知识库)
   - 4.9 [定时任务](#49-定时任务)
   - 4.10 [概览仪表盘](#410-概览仪表盘)
   - 4.11 [对话历史](#411-对话历史)
5. [状态设计](#5-状态设计)
6. [接口对接](#6-接口对接)
7. [目录结构](#7-目录结构)
8. [环境与配置](#8-环境与配置)
9. [依赖清单](#9-依赖清单)
10. [UI 设计规范](#10-ui-设计规范)

---

## 1. 项目概述

Ke-Hermes 前端是通用智能体服务平台的 Web 交互界面，采用 Vue 3 + TypeScript + Vite + Element Plus 技术栈。提供智能体对话、智能体管理、模型管理、MCP 广场、技能管理、工具管理、知识库、定时任务、概览仪表盘等全套功能，支持普通回复和 SSE 流式 token 输出两种对话模式。整体采用暗色主题（`#060b1a` 底色），左右布局（SideMenu 侧边栏 + TopBar 顶栏 + 中央工作区）。

**v1.6.0 实际实现覆盖：**

- **12 个页面视图**：对话主页、概览仪表盘、智能体管理、模型管理、Skills 管理、Tools 管理、MCP 广场、MCP 详情、定时任务、知识库、登录/注册（3 种方式）、OAuth 回调
- **完整认证体系**：账号密码登录（RSA 加密传输）、手机验证码登录、手机号注册、邮箱注册、OAuth 第三方登录（GitHub/Google/微信）、滑块验证码 + 图片验证码、JWT 双 Token 自动刷新
- **智能体全生命周期管理**：CRUD + 配置（工具/提示词/文件/子智能体）+ 文件编辑 + 技能关联 + 关系图可视化 + CronJob 查询 + 克隆 + 状态切换
- **10 个 Pinia Store**：auth、chat、ui、agent、model、skill、tool、mcp、scheduledTask、captcha、knowledgeBase
- **12 个 API Service 模块**：request（核心 HTTP + SSE）、authApi、captchaApi、oauthApi、agentApi、conversationApi、mcpApi、modelApi、skillApi、toolApi、scheduledTaskApi（Mock）、knowledgeBaseApi（Mock）

---

## 2. 技术栈

| 组件       | 技术                          | 用途                       |
| -------- | --------------------------- | ------------------------ |
| 框架       | Vue 3.5 (Composition API)   | UI 渲染与组件化               |
| 语言       | TypeScript 5.5              | 类型安全                    |
| 状态管理    | Pinia 2.2                   | 全局状态管理（10 个 Store）       |
| 路由       | Vue Router 4.4              | 客户端路由 + 全局鉴权守卫          |
| 构建       | Vite 5.4                    | 开发服务器与生产构建              |
| UI 组件库   | Element Plus 2.8            | UI 组件（自动按需导入）           |
| HTTP 请求  | Axios 1.7                   | HTTP 客户端 + 拦截器          |
| 流式请求    | fetch + ReadableStream      | SSE 流式响应解析              |
| 图表       | ECharts 6 + vue-echarts     | 概览仪表盘图表                 |
| 图形可视化   | @vue-flow/core + dagre      | 智能体关系图（节点+边+自动布局）      |
| 密码加密    | jsencrypt                   | RSA 公钥加密密码              |
| Markdown | marked                      | 对话消息 Markdown 渲染       |
| 图标       | lucide-vue-next             | 全局图标库                   |
| 动画       | @vueuse/motion              | Vue 动效                  |
| 国际化     | vue-i18n                    | 中文国际化                   |
| 样式       | SCSS + CSS Custom Properties | 暗色主题 + 组件样式             |
| 测试       | Vitest + jsdom + @vue/test-utils | 单元/组件测试               |

---

## 3. 路由设计

所有路由在 `src/router/index.ts` 中定义，采用懒加载（`() => import(...)`）。

| 路径 | 名称 | 视图组件 | Meta | 说明 |
|------|------|----------|------|------|
| `/` | `home` | `HomeView.vue` | `requiresAuth: true` | 对话主页（默认首页） |
| `/overview` | `overview` | `OverviewView.vue` | `requiresAuth: true`, `title: '概览'` | 概览仪表盘 |
| `/agents` | `agents` | `AgentsView.vue` | `requiresAuth: true`, `title: '代理管理中心'` | 智能体管理 |
| `/models` | `models` | `ModelsView.vue` | `requiresAuth: true`, `title: '模型'` | 模型提供商管理 |
| `/skills` | `skills` | `SkillsView.vue` | `requiresAuth: true`, `title: 'Skills'` | 技能管理 |
| `/tools` | `tools` | `ToolsView.vue` | `requiresAuth: true`, `title: 'Tools'` | 工具管理 |
| `/mcp` | `mcp-square` | `McpSquareView.vue` | `requiresAuth: true`, `title: 'MCP 广场'` | MCP 工具广场 |
| `/mcp/:id` | `mcp-detail` | `McpDetailView.vue` | `requiresAuth: true`, `title: 'MCP 详情'` | MCP 工具详情 |
| `/scheduled-tasks` | `scheduled-tasks` | `ScheduledTasksView.vue` | `requiresAuth: true`, `title: '定时任务'` | 定时任务管理 |
| `/knowledge-base` | `knowledge-base` | `KnowledgeBaseView.vue` | `requiresAuth: true`, `title: '知识库'` | 知识库管理 |
| `/login` | `login` | `LoginView.vue` | `guest: true` | 登录页 |
| `/register` | `register` | `RegisterView.vue` | `guest: true` | 手机号注册页 |
| `/register/email` | `register-email` | `EmailRegisterView.vue` | `guest: true` | 邮箱注册页 |
| `/oauth/callback` | `oauth-callback` | `OAuthCallbackView.vue` | `guest: true` | OAuth 回调处理页 |
| `/:pathMatch(.*)*` | `not-found` | — | — | 兜底重定向到 `/` |

### 路由守卫

- **`requiresAuth`**：未认证时自动跳转 `/login?redirect=<当前路径>`
- **`guest`**：已认证时自动跳转 `/`
- **Token 存储**：JWT Token 存储在 `sessionStorage`（`auth_tokens` 键），页面关闭后失效

### 布局系统

| 布局组件 | 适用路由 | 说明 |
|---------|---------|------|
| `MainLayout.vue` | 所有需登录页面 | `SideMenu`（左侧栏）+ `TopBar`（顶栏）+ `<RouterView>`（工作区） |
| `AuthLayout.vue` | `/login`、`/register`、`/register/email` | `BrandPanel`（左侧 40% 品牌展示）+ `<RouterView>`（右侧 60% 表单区） |
| 独立页面 | `/oauth/callback` | OAuth 回调处理，无布局 |

---

## 4. 功能需求

### 4.1 认证体系

#### F1.1 账号密码登录

调用 `POST /api/auth/login/account` 接口。

**流程：**
1. 前端 `GET /api/auth/public-key` 获取 RSA 公钥
2. 使用 `jsencrypt` 库以 PKCS1v15 模式加密密码
3. 密文 Base64 编码后发送到后端
4. 成功后获得 `{ accessToken, refreshToken, expiresIn }` + 用户信息
5. Token 写入 `sessionStorage`，Axios 拦截器自动注入后续请求

**登录表单：**
- `AccountLoginForm.vue`：账号（用户名/手机号/邮箱）+ 密码 + 验证码（滑块拼图，首次失败后触发）
- 密码输入框支持显示/隐藏切换（`PasswordInput.vue`）
- 登录失败 5 次后账号锁定 30 分钟，前端展示剩余锁定时间
- 支持 `GET /api/auth/fail-count?account=xxx` 查询失败次数

#### F1.2 手机验证码登录

调用 `POST /api/auth/login/phone` 接口。

- `PhoneLoginForm.vue`：手机号 + 短信验证码 + 滑块验证码
- 验证码 60 秒倒计时重发限制（`CountdownButton.vue`）
- 短信每日限 5 条，前端根据 `SMS_DAILY_LIMIT` 提示

#### F1.3 手机号注册

调用 `POST /api/auth/register/phone` 接口。

- `RegisterForm.vue`：手机号 + 短信验证码 + 昵称 + 密码 + 协议勾选
- `AgreementCheckbox.vue`：协议复选框，未勾选时有摇动动画提示

#### F1.4 邮箱注册

调用 `POST /api/auth/register/email` 接口。

- `EmailRegisterForm.vue`：邮箱 + 邮箱验证码 + 昵称 + 密码 + 协议勾选
- 邮箱验证码通过 `POST /api/email/send` 发送

#### F1.5 验证码

**滑块拼图验证码**（主要方式）：

- `SlidePuzzle.vue`：`GET /api/captcha/slide` 获取背景图 + 滑块图 + 缺口 Y 坐标
- 用户拖动滑块到目标位置 → `POST /api/captcha/slide/verify` 校验
- 容差阈值 `SLIDE_THRESHOLD`（默认 8px）
- 服务端通过 HTTP-only `captcha_session` Cookie 关联请求与会话

**图片验证码**（降级方案）：

- `ImageCaptcha.vue`：`GET /api/captcha/image` 获取 4 位字符图片
- 用户输入 → `POST /api/captcha/image/verify` 校验

**验证码弹窗**（`CaptchaModal.vue`）：统一管理验证码触发流程，支持挂起操作（`PendingAction`）——验证码通过后自动执行。

#### F1.6 OAuth 第三方登录

- `OAuthPanel.vue`：展示 GitHub / Google / 微信三个登录按钮
- `GET /api/oauth/auth-url?provider=xxx` 获取授权跳转 URL
- 用户授权后回调到 `/oauth/callback`，`OAuthCallbackView.vue` 调用 `POST /api/oauth/callback` 完成登录

#### F1.7 用户菜单与退出

- `TopBar.vue` 右侧用户头像下拉菜单：显示用户名、邮箱，提供退出登录按钮
- `POST /api/auth/logout` 退出后清除 Token + 用户信息，跳转登录页

---

### 4.2 对话界面

**布局**：`AppShell.vue` → `ChatMain.vue`（消息区）+ `RightPanel.vue`（历史面板）

#### F2.1 消息展示

- `MessageList.vue`：消息列表，自动滚动到底部（`scrollIntoView`）
- `MessageItem.vue`：
  - 用户消息：右对齐，深色气泡（`--color-bg-user-bubble`），`UserCircle` 头像
  - 智能体回复：左对齐，浅色气泡（`--color-bg-assistant-bubble`），`Sparkles` 头像
  - Markdown 渲染：使用 `marked` 库解析，支持标题/代码块（语法高亮样式）/表格/引用/链接
  - 流式输出中：光标闪烁动画
  - 包含 `TracePanel.vue`（若开启 trace）：显示 Agent/Tool 调用链的起止事件和输入/输出

#### F2.2 普通对话

调用 `POST /api/chat` 接口。请求体 `{ "message": "string", "thread_id?": "string" }`，响应 `{ "response": "string", "thread_id": "string" }`。

#### F2.3 流式对话（默认）

调用 `POST /api/chat/stream` 接口，通过 `fetch` + `ReadableStream` 解析 SSE。

**SSE 事件类型：**

| 事件类型 | 数据格式 | 说明 |
|---------|---------|------|
| `token` | `{"token": "string"}` | 逐字追加到当前回复 |
| `thread_id` | `{"thread_id": "string"}` | 对话线程 ID（流结束时发送） |
| `chain_start` | `{"name": "string", "type": "string"}` | Agent/Tool 调用开始 |
| `chain_end` | `{"name": "string", "type": "string"}` | Agent/Tool 调用结束 |
| `tool_start` | `{"name": "string", "input": {}}` | 工具调用开始 |
| `tool_end` | `{"name": "string", "output": "string"}` | 工具调用结束 |

- 发送请求后立即在消息列表中创建一条空的智能体回复（`content: ""`, `streaming: true`）
- 每个 `token` 事件到达后追加到回复文本中，实现逐字输出效果
- 流式完成后标记 `streaming: false`
- 流式过程中输入框和发送按钮禁用

#### F2.4 Trace 调用链（可开关）

- `InputBar.vue` 提供 `el-switch` 开关控制 trace 模式
- 开启后，SSE 中的 `chain_start/end` 和 `tool_start/end` 事件被收集
- `TracePanel.vue`：折叠面板展示每次调用的起止节点，含类型标签（agent/tool）、名称、输入/输出 JSON
- 状态存储在 `chatStore.traceEnabled` + `chatStore.traces`

#### F2.5 对话头部

- `ChatHeader.vue`：Agent 头像 + 标题 "Hermes 智能体" + 模型选择器（`el-select`）
- 模型列表从 `uiStore.selectedModel` 读取

#### F2.6 对话历史

- `RightPanel.vue`：右侧面板，可折叠（280px / 40px）
- 历史列表：通过 `GET /api/conversations` 获取，支持选中/删除
- 选中某个历史对话时，通过 `GET /api/conversations/{thread_id}` 加载消息列表到当前聊天区
- `thread_id` 在首次对话时由后端返回，前端保存用于后续续接

#### F2.7 thread_id 上下文管理

| 场景 | thread_id 行为 |
|------|---------------|
| 新对话 | 前端不传 → 后端自动生成 |
| 续接对话 | 前端传入上次返回的 thread_id → 后端从检查点恢复上下文 |
| 流式结尾 | SSE 流最后一条消息返回 thread_id，前端保存 |

---

### 4.3 智能体管理

**路由**：`/agents` → `AgentsView.vue`（左右双栏布局）

#### F3.1 智能体列表

- 左侧面板：智能体列表 + 搜索 + 新建按钮
- `AgentListItem.vue`：展示名称、类型（主/子）、状态标签（active/inactive/error）、描述
- 支持展开子智能体列表（主智能体下）
- `AgentFormDialog.vue`：创建/编辑智能体表单（名称、描述、系统提示词、关联模型）

#### F3.2 智能体详情

- 右侧面板：`AgentDetail.vue` 展示选中智能体的完整信息
- 基本信息：名称、类型、状态、描述、系统提示词、关联模型
- 工具列表：通过 `AgentTool` 关联表展示，支持添加（`ToolSelectDialog.vue`）/移除
- 技能列表：通过 `AgentSkill` 关联表展示，支持添加（`SkillSelectDialog.vue`）/移除
- 文件列表：`GET /api/agents/{id}/file-descriptions` 获取，支持点击编辑（`FileEditDialog.vue` + `MarkdownEditor.vue`）
- 子智能体列表：主智能体可查看/创建子智能体
- CronJob 列表：`GET /api/agents/{id}/cron-jobs` 获取定时任务
- 操作按钮：切换状态、克隆、删除（undeletable 的不可删除）

#### F3.3 智能体关系图

- `AgentGraph.vue`：使用 `@vue-flow/core` + `dagre` 自动布局
- `AgentNode.vue`：自定义节点（显示 agent 名称、类型图标、状态标签）
- `AgentEdge.vue`：自定义边（父子关系连线）
- `useAgentGraph.ts`：composable 管理 dagre 布局计算（TB 自上而下树形布局）

#### F3.4 配置管理

- `AddConfigDialog.vue`：添加工具/提示词/文件/子智能体的弹窗
- 工具/技能选择使用专用弹窗（`ToolSelectDialog.vue` / `SkillSelectDialog.vue`）
- 文件编辑：`FileEditDialog.vue` 内嵌 `MarkdownEditor.vue`（基于 `el-input` textarea + Markdown 预览）

#### F3.5 对接 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/agents` | GET | 获取智能体列表 |
| `/api/agents` | POST | 创建智能体（`AgentCreateRequest`） |
| `/api/agents/{id}` | PUT | 更新智能体（`AgentUpdateRequest`） |
| `/api/agents/{id}` | DELETE | 删除（主智能体级联删除子智能体） |
| `/api/agents/{id}/status` | PATCH | 切换 active/inactive/error |
| `/api/agents/{id}/clone` | POST | 克隆智能体（含文件内容） |
| `/api/agents/{id}/config` | POST/DELETE/PUT | 添加/移除/更新配置项 |
| `/api/agents/{id}/files/{filename}` | GET/PUT | 获取/保存文件内容 |
| `/api/agents/{id}/file-descriptions` | GET | 文件描述列表 |
| `/api/agents/{id}/skills` | GET/POST | 获取/添加技能关联 |
| `/api/agents/{id}/skills/{skill_id}` | DELETE | 移除技能关联 |
| `/api/agents/{id}/cron-jobs` | GET | 获取定时任务列表 |

---

### 4.4 模型管理

**路由**：`/models` → `ModelsView.vue`

#### F4.1 提供商管理

- 提供商列表 + 搜索 + 新建按钮
- 每个提供商卡片显示：名称、logo（emoji）、状态、API 地址、模型数量
- 新建/编辑表单：名称、API Base URL、API Key、描述、网站

#### F4.2 模型管理

- 每个提供商下嵌套展示其模型列表
- 模型信息：名称、展示名、类型（llm/vision/audio/embedding/image-gen/speech）、状态（active/beta/deprecated）、上下文窗口、参数列表
- 操作：新建、编辑、克隆（名称追加 "-clone"）、切换状态、删除

#### F4.3 对接 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/providers` | GET/POST | 获取/创建提供商 |
| `/api/providers/{id}` | PUT/DELETE | 更新/删除提供商（级联删除模型） |
| `/api/providers/{id}/models` | POST | 创建模型 |
| `/api/providers/{id}/models/{mid}` | PUT/DELETE | 更新/删除模型 |
| `/api/providers/{id}/models/{mid}/clone` | POST | 克隆模型 |
| `/api/providers/{id}/models/{mid}/status` | PATCH | 切换模型状态 |

---

### 4.5 MCP 广场

**路由**：`/mcp` → `McpSquareView.vue`，`/mcp/:id` → `McpDetailView.vue`

#### F5.1 工具列表

- 卡片网格布局 (`McpCard.vue`)
- 支持分类筛选（code_execution / search / data_analysis / file_management / notification / database / dev_tools / collaboration / container / custom）
- 支持搜索（名称 + 描述模糊匹配）
- 支持排序（installs / rating / updated_at）
- 每个卡片显示：名称、描述、图标、作者、版本、评分、安装量、官方标识、标签、是否已安装

#### F5.2 工具详情与安装

- `McpDetailView.vue`：完整工具描述 + 配置字段表单 + 安装/卸载按钮
- 安装时填写配置 JSON（如有 config_schema），调用 `POST /api/mcp/tools/{id}/install`
- 卸载调用 `DELETE /api/mcp/tools/{id}/uninstall`

#### F5.3 对接 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/mcp/tools` | GET | 工具列表（category/search/sort） |
| `/api/mcp/tools/{id}` | GET | 工具详情 |
| `/api/mcp/tools/{id}/install` | POST | 安装工具 |
| `/api/mcp/tools/{id}/uninstall` | DELETE | 卸载工具 |

---

### 4.6 Skills 技能管理

**路由**：`/skills` → `SkillsView.vue`

#### F6.1 技能列表

- 卡片网格布局 (`SkillCard.vue`)，支持分页
- 支持分类筛选（search / code / creative / analysis / tools / custom）
- 支持搜索（按名称模糊匹配）
- 每张卡片显示：名称、描述、图标、分类、状态（enabled/disabled）、是否内置（is_builtin）

#### F6.2 技能操作

- 新建/编辑：`SkillDialog.vue` 弹窗表单
- 上传：`POST /api/skill/upload_skills`，支持 zip/tar.gz/tar.bz2/tar.xz 压缩包
- 批量删除：多选后 `DELETE /api/skill/batch`
- 启用/禁用切换：`PATCH /api/skill/{id}/toggle`

#### F6.3 对接 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/skill/list` | GET | 分页列表 |
| `/api/skill/search` | GET | 按名称模糊搜索 |
| `/api/skill` | POST | 创建技能 |
| `/api/skill/{id}` | GET/PUT/DELETE | 详情/更新/删除 |
| `/api/skill/{id}/toggle` | PATCH | 启用/禁用切换 |
| `/api/skill/batch` | DELETE | 批量删除 |
| `/api/skill/upload_skills` | POST | 上传技能压缩包 |

---

### 4.7 Tools 工具管理

**路由**：`/tools` → `ToolsView.vue`

#### F7.1 工具列表

- 卡片网格布局 (`ToolCard.vue`)，支持无限滚动加载（每页 12 条）
- 支持分类筛选 + 来源筛选（builtin / third_party）+ 状态筛选 + 关键字搜索
- 每张卡片显示：名称、展示名、描述、分类、来源、状态、版本、作者、标签

#### F7.2 工具操作

- 新建/编辑：`ToolDialog.vue` 弹窗表单（第三方工具）
- 详情：`ToolDetailDrawer.vue` 抽屉面板
- 启用/禁用切换：`PATCH /api/tools/{id}/toggle`
- 删除：仅第三方工具可删除，内置工具不可删除

#### F7.3 对接 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/tools/list` | GET | 分页列表 + 筛选 |
| `/api/tools` | POST | 创建第三方工具 |
| `/api/tools/{id}` | GET/PUT/DELETE | 详情/更新/删除 |
| `/api/tools/{id}/toggle` | PATCH | 启用/禁用切换 |
| `/api/tools/by-agent/{id}` | GET | 按智能体筛选工具 |

---

### 4.8 知识库

**路由**：`/knowledge-base` → `KnowledgeBaseView.vue`

**当前状态**：Mock 实现（`knowledgeBaseApi.ts`），数据存储在内存中，模拟 200-500ms 网络延迟。

#### F8.1 知识库列表

- 卡片网格 (`KbCard.vue`)，每张显示名称、描述、文档数量、状态、统计（`KbStatCard.vue`）
- 支持创建（`KbCreateDialog.vue`）、编辑、删除

#### F8.2 知识库详情

- `KbDetail.vue`：多 Tab 面板
  - **概览 Tab**（`KbOverviewTab.vue`）：统计指标、`KbConfigSummary.vue` 配置摘要
  - **文档 Tab**（`KbDocsTab.vue`）：文档列表 + 上传（`KbUploadDialog.vue`）+ 删除/重试 + 状态标记（`KbDocStatusBadge.vue`）+ 索引流水线动画（`KbIndexingPipeline.vue`）
  - **配置 Tab**（`KbConfigTab.vue`）：索引配置表单
  - **搜索 Tab**（`KbSearchTab.vue`）：搜索输入 + 结果列表
  - **图谱 Tab**（`KbGraphTab.vue`）：文档关系图

---

### 4.9 定时任务

**路由**：`/scheduled-tasks` → `ScheduledTasksView.vue`

**当前状态**：Mock 实现（`scheduledTaskApi.ts`），6 个预置任务 + 8 条运行记录。

#### F9.1 任务管理

- 任务列表 + 搜索 + 状态筛选
- 支持创建、编辑、克隆、删除、启用/暂停切换
- 每条任务显示：名称、描述、cron 表达式、可读标签、状态（active/paused/error）、目标类型（chat/tool/skill）、目标内容、上次运行时间、下次运行时间、标签
- 可展开查看运行记录列表

---

### 4.10 概览仪表盘

**路由**：`/overview` → `OverviewView.vue`

使用 ECharts 6 + vue-echarts，暗色主题配色。

#### F10.1 指标卡片

- 今日活跃用户数（KPI 卡片，含环比变化百分比）
- 今日请求量
- 在线智能体数
- 系统健康评分

#### F10.2 图表

- **活跃用户趋势图**：area chart，7 天数据
- **请求量趋势图**：area chart，7 天数据
- **模型使用占比**：pie/doughnut chart

#### F10.3 信息面板

- 系统健康状态：CPU / 内存 / 磁盘 / 网络
- 最近事件日志列表
- 团队成员列表（头像 + 状态）

---

### 4.11 对话历史

#### F11.1 历史面板

- `RightPanel.vue`：位于对话页右侧，可折叠（280px / 40px）
- 列表项显示对话标题和时间
- 支持选中加载、删除
- "新对话"按钮：清空当前对话，生成新 thread_id

#### F11.2 对接 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/conversations` | GET | 对话列表（按 updated_at 倒序） |
| `/api/conversations/{thread_id}` | GET | 加载对话消息 |
| `/api/conversations/{thread_id}` | PATCH | 重命名对话 |
| `/api/conversations/{thread_id}` | DELETE | 删除对话 + 检查点 |

---

## 5. 状态设计

### 5.1 Pinia Store 总览

| Store | 文件 | 核心状态 | 说明 |
|-------|------|---------|------|
| `auth` | `stores/auth.ts` | `tokens`, `user`, `loginLoading`, `loginError`, `agreedProtocolVersion` | 认证状态 + 登录/注册/Token 刷新 |
| `chat` | `stores/chat.ts` | `messages`, `loading`, `threadId`, `traceEnabled`, `traces` | 对话消息 + SSE 流式 + Trace 调用链 |
| `ui` | `stores/ui.ts` | `sidebarCollapsed`, `rightPanelCollapsed`, `selectedModel`, `histories`, `activeThreadId`, `searchQuery` | 全局 UI 布局 + 对话历史 |
| `agent` | `stores/agent.ts` | `agents`, `selectedAgentId`, `cronJobs`, `expandedIds`, `currentFileContent`, `fileDescriptions` | 智能体管理全状态 |
| `model` | `stores/model.ts` | `providers`, `selectedProviderId`, `providerSearch`, `modelSearch`, `modelTypeFilter`, `rightTab` | 模型管理 |
| `skill` | `stores/skill.ts` | `skills`, `total`, `page`, `pageSize` | 技能管理 + 分页 |
| `tool` | `stores/tool.ts` | `tools`, `total`, `page`, `loadingMore` | 工具管理 + 无限滚动 |
| `mcp` | `stores/mcp.ts` | `tools`, `currentTool`, `detailLoading` | MCP 广场 |
| `scheduledTask` | `stores/scheduledTask.ts` | `tasks`, `runs`, `taskSearch`, `taskFilter`, `runFilter`, `expandedTaskId` | 定时任务（Mock） |
| `captcha` | `stores/captcha.ts` | `modalVisible`, `captchaType`, `pendingAction`, `smsCountdown`, `dailySmsCount` | 验证码弹窗 + 短信倒计时 |
| `knowledgeBase` | `stores/knowledgeBase.ts` | `kbs`, `selectedKb`, `selectedDoc`, `viewMode`, `searchQuery` | 知识库（Mock） |

### 5.2 Chat Store 详细设计

```typescript
interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean       // true 表示正在流式接收
  traces?: TraceEntry[]     // Agent/Tool 调用链（开启 trace 时）
  timestamp: number
}

interface TraceEntry {
  id: string
  type: 'chain_start' | 'chain_end' | 'tool_start' | 'tool_end'
  name: string
  input?: string
  output?: string
  timestamp: number
}

interface ChatState {
  messages: ChatMessage[]
  loading: boolean
  threadId: string | null
  traceEnabled: boolean
  traces: TraceEntry[]
}
```

**Actions:**

| Action | 说明 |
|--------|------|
| `sendMessage(msg)` | 追加用户消息，发起 SSE 流式请求，创建流式回复占位 |
| `appendToken(token)` | 向最后一条 assistant 消息追加 token |
| `finishStreaming()` | 标记流式完成，设置 loading=false |
| `setError(err)` | 在最后一条 assistant 消息追加错误文本 |
| `clearMessages()` | 清空消息列表 + 重置 threadId |
| `loadConversation(threadId)` | 从历史对话加载消息列表 |

### 5.3 UI Store 详细设计

```typescript
interface UIState {
  sidebarCollapsed: boolean
  rightPanelCollapsed: boolean
  plusMenuOpen: boolean
  searchQuery: string
  selectedModel: string
  histories: ConversationItem[]
  activeThreadId: string | null
}
```

**Actions:**

| Action | 说明 |
|--------|------|
| `fetchHistories()` | 获取对话历史列表 |
| `deleteHistory(threadId)` | 删除指定对话历史 |
| `toggleSidebar()` | 切换侧边栏折叠 |
| `toggleRightPanel()` | 切换右侧面板折叠 |
| `newConversation()` | 开始新对话 |

---

## 6. 接口对接

### 6.1 HTTP 基础设施（`services/request.ts`）

- Axios 实例：`baseURL: /api`，15 秒超时
- 请求拦截器：从 `sessionStorage` 读取 `auth_tokens`，注入 `Authorization: Bearer <accessToken>` 头
- 响应拦截器：
  - 检查 `code !== 0` → 抛出 `ApiError`（含 `code`、`message`）
  - 401 时自动调用 `/api/auth/refresh` 刷新 Token（去重锁防止并发刷新）
  - 刷新成功后重试原请求
  - 刷新失败 → 清除 Token + 跳转登录页

**统一响应格式：**

```typescript
interface ApiResponse<T> {
  code: number        // 0 = 成功
  data: T | null
  message: string     // "ok" 或错误描述
  requestId: string
  timestamp: number
}
```

**SSE 流式请求：**

```typescript
async function sendStreamRequest(
  url: string,
  body: object,
  onToken: (token: string) => void,
  onComplete: (threadId: string) => void,
  onEvent?: (event: StreamEvent) => void,
  onError?: (error: Error) => void
): Promise<void>
```

- 使用 `fetch` + `ReadableStream.getReader()` 解析 SSE
- 按 `\n\n` 分割事件，解析 `data:` 行中的 JSON
- 处理 JSON 跨行拼接（`\n` 被 Reader 分割的情况）

### 6.2 API Service 模块清单

| Service | 接口数 | 说明 |
|---------|--------|------|
| `authApi.ts` | 9 | 登录/注册/刷新/公钥/失败查询 |
| `captchaApi.ts` | 5 | 滑块拼图/图片验证码 + 短信发送 |
| `oauthApi.ts` | 2 | OAuth URL + 回调 |
| `agentApi.ts` | 17 | 智能体 CRUD + 配置 + 文件 + 技能 + CronJob |
| `conversationApi.ts` | 4 | 对话历史 CRUD |
| `mcpApi.ts` | 4 | MCP 工具列表/详情/安装/卸载 |
| `modelApi.ts` | 9 | 提供商/模型 CRUD + 克隆 + 状态 |
| `skillApi.ts` | 9 | 技能 CRUD + 上传 + 批量 + 搜索 |
| `toolApi.ts` | 6 | 工具 CRUD + 切换 |
| `scheduledTaskApi.ts` | — | Mock 实现，6 个预置任务 |
| `knowledgeBaseApi.ts` | — | Mock 实现，5 个知识库 |

### 6.3 错误处理

| 场景 | 状态码 | 处理方式 |
|------|--------|---------|
| 空消息 | 422 | 前端 `min_length=1` 校验，不发送请求 |
| 未认证 | 401 | 自动刷新 Token，失败则跳转登录页 |
| 业务错误 | 200 (code≠0) | 根据 `code` 映射到 i18n 错误消息 |
| 网络错误 | — | `el-message` 提示连接失败 |
| 服务器错误 | 500 | `el-message` 提示服务异常 |
| 登录锁定 | 200 (AUTH_001) | 显示剩余锁定时间 |
| Token 过期 | 200 (AUTH_002) | 自动刷新 Token |

---

## 7. 目录结构

```
frontend/
├── src/
│   ├── main.ts                          # Vue 应用入口（挂载 Pinia/Router/i18n/ElementPlus）
│   ├── App.vue                          # 根组件（<RouterView />）
│   ├── views/                           # 页面级组件（12 个）
│   │   ├── HomeView.vue                 # 对话主页（AppShell）
│   │   ├── OverviewView.vue             # 概览仪表盘（ECharts）
│   │   ├── AgentsView.vue               # 智能体管理（双栏布局）
│   │   ├── ModelsView.vue               # 模型管理
│   │   ├── SkillsView.vue               # 技能管理
│   │   ├── ToolsView.vue                # 工具管理（无限滚动）
│   │   ├── McpSquareView.vue            # MCP 广场
│   │   ├── McpDetailView.vue            # MCP 详情
│   │   ├── ScheduledTasksView.vue       # 定时任务（Mock）
│   │   ├── KnowledgeBaseView.vue        # 知识库（Mock）
│   │   ├── LoginView.vue                # 登录页
│   │   ├── RegisterView.vue             # 手机号注册页
│   │   ├── EmailRegisterView.vue        # 邮箱注册页
│   │   └── OAuthCallbackView.vue        # OAuth 回调处理页
│   ├── components/                      # 通用组件
│   │   ├── MainLayout.vue               # 认证后根布局（SideMenu + TopBar + RouterView）
│   │   ├── AppShell.vue                 # 聊天三栏布局
│   │   ├── ChatMain.vue                 # 聊天主区域（ChatHeader + MessageList + InputBar）
│   │   ├── ChatHeader.vue               # 对话头部（含模型选择器）
│   │   ├── MessageList.vue              # 消息列表（自动滚动）
│   │   ├── MessageItem.vue              # 单条消息（Markdown 渲染 + TracePanel）
│   │   ├── InputBar.vue                 # 消息输入栏（含 trace 开关）
│   │   ├── TracePanel.vue               # Agent/Tool Trace 调用链面板
│   │   ├── SideMenu.vue                 # 侧边菜单（分组菜单 + 搜索）
│   │   ├── RightPanel.vue               # 右侧历史面板（对话列表）
│   │   ├── TopBar.vue                   # 顶部栏（面包屑 + 通知铃铛 + 用户菜单）
│   │   ├── auth/                        # 认证组件（11 个文件）
│   │   │   ├── AuthLayout.vue           #   认证页布局（品牌 + 表单）
│   │   │   ├── BrandPanel.vue           #   品牌展示面板（Logo + 标语 + FeatureGrid）
│   │   │   ├── FeatureGrid.vue          #   功能亮点网格
│   │   │   ├── LoginCard.vue            #   登录/注册卡片容器
│   │   │   ├── LoginTabs.vue            #   账号/手机登录 Tab 切换
│   │   │   ├── AccountLoginForm.vue     #   账号密码登录表单
│   │   │   ├── PhoneLoginForm.vue       #   手机验证码登录表单
│   │   │   ├── RegisterForm.vue         #   手机号注册表单
│   │   │   ├── EmailRegisterForm.vue    #   邮箱注册表单
│   │   │   ├── AgreementCheckbox.vue    #   协议勾选复选框
│   │   │   ├── OAuthPanel.vue           #   第三方登录按钮组
│   │   │   └── RegisterLink.vue         #   登录/注册导航链接
│   │   ├── captcha/                     # 验证码组件（3 个文件）
│   │   │   ├── CaptchaModal.vue         #   验证码弹窗容器
│   │   │   ├── SlidePuzzle.vue          #   滑块拼图验证码
│   │   │   └── ImageCaptcha.vue         #   图片验证码
│   │   ├── common/                      # 通用小组件（3 个文件）
│   │   │   ├── CountdownButton.vue      #   验证码倒计时按钮
│   │   │   ├── FormError.vue            #   表单错误展示
│   │   │   └── PasswordInput.vue        #   密码输入框（含显示/隐藏切换）
│   │   ├── agent/                       # 智能体组件（11 个文件）
│   │   │   ├── AgentListItem.vue        #   智能体列表项
│   │   │   ├── AgentDetail.vue          #   智能体详情面板
│   │   │   ├── AgentGraph.vue           #   智能体关系图（Vue Flow）
│   │   │   ├── AgentNode.vue            #   关系图自定义节点
│   │   │   ├── AgentEdge.vue            #   关系图自定义边
│   │   │   ├── AgentFormDialog.vue      #   创建/编辑智能体弹窗
│   │   │   ├── AddConfigDialog.vue      #   添加配置项弹窗
│   │   │   ├── FileEditDialog.vue       #   文件编辑弹窗
│   │   │   ├── MarkdownEditor.vue       #   Markdown 编辑器
│   │   │   ├── SkillSelectDialog.vue    #   技能选择弹窗
│   │   │   └── ToolSelectDialog.vue     #   工具选择弹窗
│   │   ├── knowledgeBase/               # 知识库组件（13 个文件）
│   │   │   ├── KbCard.vue               #   知识库卡片
│   │   │   ├── KbDetail.vue             #   知识库详情（多 Tab）
│   │   │   ├── KbOverviewTab.vue        #   概览 Tab
│   │   │   ├── KbDocsTab.vue            #   文档 Tab
│   │   │   ├── KbConfigTab.vue          #   配置 Tab
│   │   │   ├── KbSearchTab.vue          #   搜索 Tab
│   │   │   ├── KbGraphTab.vue           #   图谱 Tab
│   │   │   ├── KbCreateDialog.vue       #   创建知识库弹窗
│   │   │   ├── KbUploadDialog.vue       #   上传文档弹窗
│   │   │   ├── KbConfigSummary.vue      #   配置摘要
│   │   │   ├── KbDocStatusBadge.vue     #   文档状态标记
│   │   │   ├── KbStatCard.vue           #   统计卡片
│   │   │   └── KbIndexingPipeline.vue   #   索引流水线动画
│   │   ├── mcp/
│   │   │   └── McpCard.vue              # MCP 工具卡片
│   │   ├── skill/
│   │   │   ├── SkillCard.vue            #   技能卡片
│   │   │   ├── SkillDialog.vue          #   技能创建/编辑弹窗
│   │   │   └── iconMap.ts              #   技能图标映射
│   │   └── tool/
│   │       ├── ToolCard.vue             #   工具卡片
│   │       ├── ToolDialog.vue           #   工具创建/编辑弹窗
│   │       ├── ToolDetailDrawer.vue     #   工具详情抽屉
│   │       └── iconMap.ts              #   工具图标映射
│   ├── composables/                     # 组合式函数（6 个）
│   │   ├── useAuth.ts                   #   认证流程编排
│   │   ├── useCaptcha.ts                #   验证码流程封装
│   │   ├── useCountdown.ts              #   通用倒计时
│   │   ├── usePasswordEncrypt.ts        #   RSA 密码加密
│   │   ├── useAgentGraph.ts             #   智能体关系图布局（dagre）
│   │   └── useAgreement.ts              #   协议勾选逻辑
│   ├── stores/                          # Pinia 状态管理（11 个）
│   │   ├── auth.ts                      #   认证状态
│   │   ├── chat.ts                      #   对话状态
│   │   ├── ui.ts                        #   全局 UI 布局
│   │   ├── agent.ts                     #   智能体管理
│   │   ├── model.ts                     #   模型管理
│   │   ├── skill.ts                     #   技能管理
│   │   ├── tool.ts                      #   工具管理
│   │   ├── mcp.ts                       #   MCP 广场
│   │   ├── scheduledTask.ts             #   定时任务（Mock）
│   │   ├── captcha.ts                   #   验证码弹窗
│   │   └── knowledgeBase.ts             #   知识库（Mock）
│   ├── services/                        # API 服务层（12 个模块）
│   │   ├── request.ts                   #   Axios 实例 + 拦截器 + SSE 流式请求
│   │   ├── authApi.ts                   #   认证接口
│   │   ├── captchaApi.ts                #   验证码 + 短信接口
│   │   ├── oauthApi.ts                  #   OAuth 接口
│   │   ├── agentApi.ts                  #   智能体 CRUD + 文件 + 技能 + CronJob
│   │   ├── conversationApi.ts           #   对话历史接口
│   │   ├── mcpApi.ts                    #   MCP 工具接口
│   │   ├── modelApi.ts                  #   模型/提供商接口
│   │   ├── skillApi.ts                  #   技能接口
│   │   ├── toolApi.ts                   #   工具接口
│   │   ├── scheduledTaskApi.ts          #   定时任务接口（Mock）
│   │   └── knowledgeBaseApi.ts          #   知识库接口（Mock）
│   ├── types/                           # TypeScript 类型定义（10 个文件）
│   │   ├── api.ts                       #   ApiResponse, PaginatedResponse
│   │   ├── auth.ts                      #   AuthTokens, UserInfo, LoginRequest
│   │   ├── agent.ts                     #   Agent, AgentInfo, SkillBrief, CronJobBrief
│   │   ├── chat.ts                      #   ChatMessage, TraceEntry
│   │   ├── captcha.ts                   #   SlidePuzzleData, ImageCaptchaData
│   │   ├── model.ts                     #   Provider, AIModel, ModelParam
│   │   ├── mcp.ts                       #   McpTool, McpConfigField
│   │   ├── skill.ts                     #   Skill, SkillCreateRequest
│   │   ├── tool.ts                      #   Tool, ToolCreateRequest
│   │   ├── components.ts                #   PendingAction, CaptchaResult
│   │   ├── knowledgeBase.ts             #   KB, KBDoc, IndexConfig, SearchResult
│   │   ├── scheduledTask.ts             #   CronTask, RunRecord
│   │   └── router.d.ts                  #   路由 Meta 类型扩展
│   ├── router/
│   │   └── index.ts                     #   路由配置 + 全局守卫
│   ├── locales/
│   │   ├── index.ts                     #   i18n 初始化（vue-i18n, zh-CN）
│   │   └── zh-CN.ts                     #   中文语言文件（认证/校验/错误码/对话）
│   └── assets/
│       └── styles/
│           ├── variables.css            #   CSS 自定义属性（暗色主题 100+ 变量）
│           ├── main.css                 #   全局基础样式
│           ├── fonts.css                #   字体定义
│           └── mixins.scss              #   SCSS mixins（glass-card, respond-md/sm）
├── public/
│   └── favicon.ico
├── tests/                               # 测试文件
├── docs/
│   ├── requirements.md                  # 本文件
│   └── Ke Hermes 详细设计说明书-1.2.0.md   # 详细设计说明书
├── index.html                           # HTML 入口
├── vite.config.ts                       # Vite 配置（含 proxy + ElementPlus 自动导入）
├── tsconfig.json                        # TypeScript 配置
└── package.json                         # 依赖配置
```

---

## 8. 环境与配置

### 8.1 环境变量（`.env`）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `VITE_API_BASE_URL` | `/api` | API 基础路径 |
| `VITE_ALLOW_PASTE_PASSWORD` | — | 是否允许粘贴密码到密码输入框（安全开关） |

### 8.2 Vite 开发服务器

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 端口 | `5173` | 开发服务器端口 |
| Proxy `/api` | `http://127.0.0.1:8000` | API 代理到后端 |
| Build target | `ES2020` | 构建目标 |
| Code splitting | `element-plus`, `vue-vendor` | 手动代码分割 |

### 8.3 Element Plus 自动导入

使用 `unplugin-vue-components` + `ElementPlusResolver` 实现组件的按需自动导入，无需手动注册。

---

## 9. 依赖清单

### 9.1 运行时依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `vue` | ^3.5 | Vue 3 核心 |
| `vue-router` | ^4.4 | 客户端路由 |
| `pinia` | ^2.2 | 状态管理 |
| `element-plus` | ^2.8 | UI 组件库 |
| `axios` | ^1.7 | HTTP 客户端 |
| `echarts` | ^6.1 | 图表库 |
| `vue-echarts` | ^8.0 | Vue ECharts 集成 |
| `@vue-flow/core` | ^1.48 | 图形可视化引擎 |
| `@vue-flow/background` | ^1.3 | 图形背景 |
| `@vue-flow/controls` | ^1.1 | 图形控件 |
| `@vue-flow/minimap` | ^1.5 | 图形缩略图 |
| `dagre` | ^0.8 | 图形自动布局算法 |
| `@vueuse/motion` | ^2.2 | Vue 动效 |
| `jsencrypt` | ^3.3 | RSA 密码加密 |
| `lucide-vue-next` | ^0.400 | 图标库 |
| `marked` | ^18.0 | Markdown 渲染 |
| `vue-i18n` | ^9.14 | 国际化 |

### 9.2 开发依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `vite` | ^5.4 | 构建工具 |
| `@vitejs/plugin-vue` | ^5.0 | Vite Vue 插件 |
| `unplugin-vue-components` | ^0.27 | Element Plus 自动导入 |
| `typescript` | ~5.5 | TypeScript |
| `vue-tsc` | ^2.1 | Vue TS 类型检查 |
| `vitest` | ^2.1 | 测试运行 |
| `@vue/test-utils` | ^2.4 | Vue 组件测试 |
| `jsdom` | ^24.0 | DOM 测试环境 |
| `sass` | ^1.80 | SCSS 预处理器 |
| `prettier` | ^3.3 | 代码格式化 |

---

## 10. UI 设计规范

### 10.1 主题

- **整体风格**：暗色主题，底色 `--color-bg-page: #060b1a`
- **侧边栏**：深色半透明背景，220px / 56px 可折叠
- **工作区**：略亮的背景色，内容卡片使用 glass-morphism 效果（`mixins.scss: glass-card`）
- **Element Plus 组件**：全部继承暗色主题 CSS 变量

### 10.2 消息气泡

- 用户消息：右对齐，深色/品牌色背景，浅色文字
- 智能体回复：左对齐，半透明浅色背景，深色文字（暗色主题下为浅色文字）
- 流式输出时：智能体回复区域显示光标闪烁动画
- 加载状态：输入框和发送按钮禁用 + 骨架屏/loading

### 10.3 响应式

- `AuthLayout`：移动端（<768px）隐藏品牌面板，仅显示表单
- `OverviewView`：仪表盘网格自适应列数
- `SideMenu`：移动端默认折叠

### 10.4 图标

- 统一使用 `lucide-vue-next` 图标库
- 菜单项、按钮、状态标记、空状态均使用相应图标

### 10.5 交互反馈

- Element Plus `ElMessage` 全局消息提示（成功/错误/警告）
- `ElMessageBox` 确认弹窗（删除操作等）
- `ElLoading` 指令：数据加载时显示加载遮罩
- 协议未勾选时：`AgreementCheckbox` 抖动动画

### 10.6 动画

- `@vueuse/motion`：页面切换和组件出现动画
- 知识库：索引流水线 CSS 动画（`KbIndexingPipeline.vue`）
- 侧边栏：过渡动画（Element Plus collapse transition）

---

> 本文档 v1.6.0 基于实际前端代码实现更新。涵盖 12 个页面视图、10 个 Pinia Store、12 个 API Service 模块、6 个 Composable、50+ 组件。认证体系支持 6 种登录/注册方式，智能体管理覆盖完整生命周期，MCP 广场/Skills/Tools 提供完整 CRUD 管理，知识库和定时任务当前为 Mock 实现待对接后端 API。
