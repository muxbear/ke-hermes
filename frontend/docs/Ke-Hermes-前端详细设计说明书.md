# Ke-Hermes 详细设计说明书 — v1.6.0


| 版本  | 日期       | 作者 | 变更说明                                                     |
| ----- | ---------- | ---- | ------------------------------------------------------------ |
| 1.0.0 | 2026-05-18 | -    | 登录模块详细设计初版，基于需求说明书 v1.1.0                  |
| 1.1.0 | 2026-05-18 | -    | 完成前端重构实施：JS→TS 迁移、登录模块全部组件、暗色主题、测试套件、Element Plus 集成 |
| 1.2.0 | 2026-05-18 | -    | 新增聊天模块详细设计：基于 requirements.md 进行全面需求分析，补充 AppShell 三栏布局、消息流、SSE 流式对话、Markdown 渲染、chatStore/uiStore 状态管理的完整设计方案 |
| 1.2.1 | 2026-05-19 | -    | 测试目录迁移至 tests/、路由改为 AuthLayout 嵌套结构、普通对话 API 已实现、ChatHeader 模型选择器已实现、auth store 持久化增强、captcha store 新增 smsErrorCount、useAuth 密码加密降级策略 |
| 1.2.2 | 2026-05-22 | -    | chatStore 增加 threadId 状态管理、sendStreamRequest/sendChatRequest 支持 thread_id 参数、SSE 解析增加 onThreadId 回调、clearMessages 重置 threadId、ChatMessage 增加 thread_id 流转 |
| 1.3.0 | 2026-05-26 | -    | 新增 MainLayout 根布局组件重构路由结构；新增 MCP 广场模块（列表/详情/安装/卸载）；新增 Skills 技能管理模块（CRUD/仓库导入/本地上传）；新增 conversationApi 服务对接后端对话历史 API；RightPanel 接入真实对话历史数据；SideMenu 增加可折叠菜单分组 + 路由导航；uiStore 重构 HistoryItem/activeThreadId；chatStore 增加 loadConversation |
| 1.4.0 | 2026-05-28 | -    | 新增代理管理模块（Part D）：智能体列表树、多标签配置面板（文件/工具/技能/Cron Jobs）、Vue Flow 主子智能体关系图（拖动/缩放/锁定/最大化）、dagre 自动布局、自定义节点边组件、Agent Store/API/Types 完整设计；TopBar 新增面包屑导航；术语统一（主智能体/子智能体/Cron Jobs）；新增 vue-flow/dagre/vueuse-motion 依赖 |
| 1.5.0 | 2026-06-05 | -    | 新增概览仪表盘（OverviewView + ECharts 图表，Part E）；新增模型管理模块（ModelsView/ModelStore/ModelApi/Model Types，Provider + Model CRUD）；新增定时任务模块（ScheduledTasksView/ScheduledTaskStore/Types，Mock 实现）；Agent API 从 Mock 切换到真实后端接口（含文件操作）；Agent Store 新增文件编辑状态（FileEditDialog + MarkdownEditor）；Skill Store 重构为分页查询 + 上传 + 批量删除 + 搜索；SideMenu 新增搜索功能 + 菜单项更新（概览/模型/定时任务）；路由新增 3 个页面；Stores 从 7 个扩展到 9 个；API Services 从 7 个扩展到 9 个；Types 从 7 个扩展到 10 个；视图从 8 个扩展到 12 个；新增 ECharts 依赖 |
| 1.7.0 | 2026-06-17 | -    | 新增知识库模块（KnowledgeBaseView + 16 个 KB 组件 + knowledgeBaseApi 23 个端点 + knowledgeBase Store + 5s 轮询索引状态 + d3-force 知识图谱，Part F）；新增 Tools 工具管理模块（ToolsView + 3 组件 + toolApi + toolStore，Part G）；新增后台管理模块（AdminView/UserManagementView/RbacView/MenuConfigView + 10 个 admin 组件 + 4 个 admin store + adminApi，Mock 实现，Part H）；更新路由（新增 6 个页面：/knowledge-base, /tools, /admin, /admin/users, /admin/rbac, /admin/menu-config）；更新主路由重定向（/ → /overview）；视图从 12 个扩展到 18 个；Stores 从 9 个扩展到 15 个；API Services 从 9 个扩展到 13 个；Types 从 10 个扩展到 14 个；组件从 ~48 个扩展到 ~63 个；新增 TracePanel 对话追踪面板；新增 useKnowledgeGraph composable |


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

**Part E — 模型/概览/定时任务模块（v1.5.0 新增）**
29. [概览仪表盘模块](#29-概览仪表盘模块)
30. [模型管理模块](#30-模型管理模块)
31. [定时任务模块](#31-定时任务模块)

**Part F — 知识库模块（v1.6.0 新增）**
32. [知识库模块概述](#32-知识库模块概述)
33. [知识库页面布局](#33-知识库页面布局)
34. [知识库核心组件设计](#34-知识库核心组件设计)
35. [知识图谱可视化设计](#35-知识图谱可视化设计)
36. [知识库状态管理](#36-知识库状态管理)
37. [知识库 API 服务层](#37-知识库-api-服务层)
38. [知识库类型定义](#38-知识库类型定义)

**Part G — 工具管理模块（v1.6.0 新增）**
39. [工具管理模块概述](#39-工具管理模块概述)
40. [工具管理页面布局](#40-工具管理页面布局)
41. [工具管理状态管理](#41-工具管理状态管理)
42. [工具管理 API 服务层](#42-工具管理-api-服务层)

**Part H — 后台管理模块（v1.6.0 新增）**
43. [后台管理模块概述](#43-后台管理模块概述)
44. [仪表盘页面](#44-仪表盘页面)
45. [人员管理页面](#45-人员管理页面)
46. [角色权限页面](#46-角色权限页面)
47. [菜单配置页面](#47-菜单配置页面)

---

## 1. 概述

### 1.1 文档目的

本文档为 Ke-Hermes 前端（桌面版）的详细设计说明书 v1.6.0，基于实际代码库编写。文档覆盖八大核心模块：

- **Part A — 基础架构与登录模块**：TypeScript 技术栈、暗色主题、国际化、测试套件
- **Part B — 聊天模块**：AppShell 三栏布局、SSE 流式对话（含 thread_id 上下文管理）、Markdown 渲染、TracePanel 追踪面板、状态管理、对话历史对接
- **Part C — MCP 广场与技能模块**：MCP 工具广场（浏览/详情/安装/卸载）、Skills 技能管理（分页/上传/批量删除/搜索）
- **Part D — 代理管理模块**：智能体列表树、多标签配置面板（文件/工具/技能/Cron Jobs）、Vue Flow 主子智能体关系图、真实后端 API 对接（含文件编辑）
- **Part E — 概览/模型/定时任务模块**：概览仪表盘（ECharts 图表）、模型管理（Provider/Model CRUD + 7 种模型类型）、定时任务（Cron 任务 + 运行日志，Mock）
- **Part F — 知识库模块（v1.6.0 新增）**：知识库 CRUD、文档上传与索引管理、8 阶段索引流水线可视化、知识图谱可视化（d3-force）、分块编辑、混合检索（向量/BM25/混合）
- **Part G — 工具管理模块（v1.6.0 新增）**：工具卡片网格 + 无限滚动、内置/第三方工具分类、工具详情抽屉、启用/禁用切换
- **Part H — 后台管理模块（v1.6.0 新增，Mock）**：管理仪表盘、人员管理（部门树 + 用户 CRUD）、角色权限（权限树 + 三态复选框 + 数据范围）、菜单配置（资源树编辑）

文档供前端开发人员编码实现、代码审查和后期维护使用。

### 1.2 技术选型


| 类别       | 选型                      | 版本     |
| -------- | ----------------------- | ------ |
| 框架       | Vue 3                   | ^3.5   |
| 类型系统     | TypeScript              | ~5.5   |
| 路由       | Vue Router              | ^4.4   |
| 状态管理     | Pinia                   | ^2.2   |
| 构建工具     | Vite                    | ^5.4   |
| 测试框架     | Vitest                  | ^2.1   |
| 单元测试工具   | @vue/test-utils         | ^2.4   |
| 组件测试环境   | jsdom                   | ^24.0  |
| UI 组件库   | Element Plus            | ^2.8   |
| HTTP 客户端 | Axios                   | ^1.7   |
| CSS 方案   | SCSS + CSS Variables    | -      |
| 加密       | JSEncrypt               | ^3.3   |
| 国际化      | vue-i18n                | ^9.14  |
| 图标       | lucide-vue-next         | ^0.400 |
| Markdown | marked                  | ^18.0  |
| 组件自动导入   | unplugin-vue-components | ^0.27  |
| 代码格式化    | Prettier                | ^3.3   |
| SCSS     | sass                    | ^1.80  |
| 图引擎      | @vue-flow/core          | ^1.48  |
| 图背景      | @vue-flow/background    | ^1.3   |
| 图控件      | @vue-flow/controls      | ^1.1   |
| 图小地图     | @vue-flow/minimap       | ^1.5   |
| 图布局      | dagre                   | ^0.8   |
| 力导向图      | d3-force                | ^3.0   |
| 动画引擎     | @vueuse/motion          | ^2.2   |
| 图表引擎     | echarts + vue-echarts   | ^6     |


### 1.3 适用模块

- **Part A**：PC Web 端登录/注册页面、OAuth 回调处理、路由守卫、Token 刷新、权限校验
- **Part B**：智能体对话界面（三栏布局）、流式 SSE 对话、Markdown 渲染、对话历史管理、TracePanel 追踪面板
- **Part C**：MCP 工具广场、Skills 技能管理（仓库导入/本身上传/手动创建）
- **Part D**：智能体列表管理、配置面板（文件/工具/技能/Cron Jobs）、主子智能体关系图、智能体 CRUD（对接真实后端 API）、文件编辑（MarkdownEditor）
- **Part E**：概览仪表盘（系统指标、资源监控、图表可视化）、模型管理（Provider + Model CRUD、7 种模型类型、筛选搜索）、定时任务（Cron 任务管理 + 运行日志记录，Mock）
- **Part F**：知识库管理（KB CRUD + 文档上传/索引 + 8 阶段状态机可视化 + 知识图谱提取 + 分块编辑 + 混合检索）、对接真实后端 API、5s 轮询索引进度
- **Part G**：工具管理（内置/第三方工具浏览 + 卡片网格 + 无限滚动 + 详情抽屉 + 源分类筛选）、对接真实后端 API
- **Part H**：后台管理仪表盘 + 人员管理（部门树 + 用户 CRUD）+ 角色权限（RBAC + 权限树 + 三态复选框 + 数据范围选择器）+ 菜单配置（资源树编辑）。全 Mock 实现

### 1.4 相关文档

- [Ke-Hermes 需求说明书-登录模块（桌面版）-1.1.0](./Ke%20Hermes%20需求说明书-登录模块（桌面版）-1.1.0.md)
- [ke-hermes 前端需求文档（聊天模块）](./requirements.md)

---

## 2. 项目架构

### 2.1 目录结构（v1.6.0）

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
    │   └── index.ts                   # 路由表（MainLayout + AuthLayout 嵌套路由）+ 前置守卫
    │
    ├── stores/                        # v1.6.0：15 个 Pinia Store
    │   ├── auth.ts                    # Token/用户/登录状态
    │   ├── captcha.ts                 # 验证码/倒计时状态
    │   ├── chat.ts                    # 聊天消息 + SSE 流式 + loadConversation
    │   ├── ui.ts                      # UI 状态（侧栏/面板/模型）+ 对话历史
    │   ├── agent.ts                   # 智能体状态（v1.4.0 新增）
    │   ├── mcp.ts                     # MCP 工具状态（v1.3.0 新增）
    │   ├── model.ts                   # 模型/提供商状态（v1.5.0 新增）
    │   ├── scheduledTask.ts           # 定时任务状态（v1.5.0 新增，Mock）
    │   ├── skill.ts                   # Skills 技能状态（v1.3.0 新增）
    │   ├── tool.ts                    # 工具管理状态（v1.6.0 新增）
    │   ├── knowledgeBase.ts           # 知识库状态（v1.6.0 新增）
    │   ├── admin.ts                   # 后台管理仪表盘状态（v1.6.0 新增，Mock）
    │   ├── userManagement.ts          # 人员管理状态（v1.6.0 新增，Mock）
    │   ├── rbac.ts                    # 角色权限状态（v1.6.0 新增，Mock）
    │   └── menuConfig.ts              # 菜单配置状态（v1.6.0 新增，Mock）
    │
    ├── types/                         # v1.6.0：14 个类型模块
    │   ├── api.ts                     # ApiResponse<T>, SendSmsRequest
    │   ├── auth.ts                    # AuthTokens, UserInfo, Request/Response
    │   ├── captcha.ts                 # SlidePuzzleData, SlideVerifyRequest
    │   ├── components.ts              # FeatureItem, OAuthProvider, CaptchaResult
    │   ├── agent.ts                   # Agent, ConfigType, STATUS_LABELS, CONFIG_TYPE_MAP（v1.4.0 新增）
    │   ├── mcp.ts                     # McpTool, McpConfigField, InstallMcpRequest（v1.3.0 新增）
    │   ├── model.ts                   # Provider, AIModel, ModelType, ModelParam（v1.5.0 新增）
    │   ├── scheduledTask.ts           # CronTask, RunRecord, TaskStatus, RunStatus（v1.5.0 新增）
    │   ├── skill.ts                   # Skill, SkillCreateRequest, CATEGORY_LABELS（v1.3.0 新增）
    │   └── router.d.ts                # RouteMeta 扩展
    │
    ├── services/
    │   ├── request.ts                 # Axios 实例 + 拦截器 + SSE + sendChatRequest
    │   ├── authApi.ts                 # 认证接口（8 个）
    │   ├── captchaApi.ts              # 验证码 + 短信接口（5 个）
    │   ├── oauthApi.ts                # OAuth 接口（2 个）
    │   ├── agentApi.ts                # 智能体 API（12 个，真实后端对接）（v1.4.0 新增，v1.5.0 切换真实 API）
    │   ├── conversationApi.ts         # 对话历史 CRUD（4 个）（v1.3.0 新增）
    │   ├── mcpApi.ts                  # MCP 接口（4 个）（v1.3.0 新增）
    │   ├── modelApi.ts                # 模型/提供商接口（9 个）（v1.5.0 新增）
    │   ├── scheduledTaskApi.ts        # 定时任务接口（Mock）（v1.5.0 新增）
    │   └── skillApi.ts                # Skills 接口（9 个，含上传/批量/搜索）（v1.3.0 新增，v1.5.0 增强）
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
    │   │   ├── AddConfigDialog.vue    # 添加配置弹窗（v1.4.0 新增）
    │   │   ├── FileEditDialog.vue     # 文件内容编辑弹窗（v1.5.0 新增）
    │   │   └── MarkdownEditor.vue     # Markdown 编辑器（v1.5.0 新增）
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
Views (HomeView, OverviewView, AgentsView, ModelsView, SkillsView, McpSquareView, ...)
  └── Components (MainLayout, AppShell, SkillCard, McpCard, AgentNode, FileEditDialog, ...)
       └── Composables (useAuth, useCaptcha, useCountdown, useAgentGraph, ...)
            ├── Stores (auth, captcha, chat, ui, agent, mcp, model, scheduledTask, skill)
            └── Services (request, authApi, captchaApi, oauthApi, agentApi, conversationApi, mcpApi, modelApi, scheduledTaskApi, skillApi)
                 └── Types (auth, api, captcha, components, agent, mcp, model, scheduledTask, skill)
```

### 2.3 v1.3.0 → v1.5.0 实施偏差


| 设计项          | v1.3.0/v1.4 计划             | v1.5.0 实施                                                                                     | 原因                       |
| ------------ | -------------------------- | --------------------------------------------------------------------------------------------- | ------------------------ |
| Agent API    | Mock 实现（agentApi.ts，8 个方法） | 对接后端真实 API（12 个方法，含文件操作），snake_case→camelCase 转换                                              | 后端 Agents API 已实现        |
| Agent 文件管理   | 仅配置项列表                     | 完整文件编辑：FileEditDialog + MarkdownEditor + 文件描述列表                                               | 后端 AgentFile API 已实现     |
| Skill Store  | 全量加载（fetchSkills）          | 分页查询（fetchSkillsPaginated）+ 搜索（searchSkills）+ 上传（uploadSkillPackage）+ 批量删除（batchRemoveSkills） | 后端 Skills 分页/搜索/上传接口已就绪  |
| 概览仪表盘        | 无                          | 完整实现：ECharts 图表 + 统计卡片 + 系统指标 + 用户排名 + 模型提供商 + 操作日志                                           | 需求新增                     |
| 模型管理         | 无                          | 完整实现：Provider CRUD + Model CRUD（7 种类型）+ 筛选搜索 + 使用统计 + 状态切换                                    | 后端 Providers API 已实现     |
| 定时任务         | 无                          | Mock 实现：Cron 任务 CRUD + 运行日志 + 预设 Cron 表达式 + 状态筛选                                              | 后端 ScheduledTask API 待实现 |
| 路由           | 5 个需认证页面                   | 8 个需认证页面：+ overview + models + scheduled-tasks                                                | 新增功能模块                   |
| 菜单导航         | 聊天/控制/代理/设置/后台 5 组         | 增强搜索功能，菜单项新增概览/模型/定时任务                                                                        | 新增页面入口                   |
| Stores 总数    | 7                          | 9（+model +scheduledTask）                                                                      | 新增模块                     |
| API Services | 7                          | 9（+modelApi +scheduledTaskApi）                                                                | 新增模块                     |
| Types        | 7                          | 10（+model +scheduledTask + 扩展 agent）                                                          | 新增类型定义                   |
| 视图数量         | 8                          | 12（+OverviewView +ModelsView +ScheduledTasksView，+ 拆分 EmailRegisterView）                      | 新增页面                     |


### 2.4 v1.2.2 → v1.3.0 实施偏差


| 设计项       | v1.2.2 计划                                   | v1.3.0 实施                                                        | 原因                     |
| --------- | ------------------------------------------- | ---------------------------------------------------------------- | ---------------------- |
| 对话历史      | RightPanel 硬编码 5 条预设                        | 对接后端 Conversation API，动态加载                                       | 后端对话历史 CRUD 已实现        |
| 路由结构      | HomeView 直接包裹 AppShell                      | 新增 MainLayout 作为认证页面根布局，HomeView/SkillsView/McpSquareView 为嵌套子路由 | 支持多页面导航                |
| 侧栏导航      | 静态菜单无路由                                     | SideMenu 使用 vue-router 导航，菜单可折叠分组，支持路由高亮                         | 支持 MCP 广场和 Skills 页面入口 |
| MCP 广场    | 无                                           | 完整实现：列表（搜索/分类/排序）+ 详情（概述/配置/使用说明/评价）+ 安装/卸载                      | 需求"前端增加了 MCP 广场功能"     |
| Skills 管理 | 无                                           | 完整实现：列表（分类筛选/统计）+ CRUD + 仓库导入 + 本地上传 + 手动创建                      | 需求"前端添加技能功能模块"         |
| Token 存储  | request.ts 读写 localStorage + sessionStorage | 统一使用 sessionStorage                                              | 简化策略，标签页级别隔离           |


---

## 3. 路由设计

### 3.1 路由表（v1.3.0 重构）


| 路径                 | 名称              | 组件 (懒加载)                                              | Meta                                |
| ------------------ | --------------- | ----------------------------------------------------- | ----------------------------------- |
| `/`                | home            | MainLayout → `@/views/HomeView.vue` (child)           | requiresAuth: true                  |
| `/overview`        | overview        | MainLayout → `@/views/OverviewView.vue` (child)       | requiresAuth: true, title: '概览'     |
| `/models`          | models          | MainLayout → `@/views/ModelsView.vue` (child)         | requiresAuth: true, title: '模型'     |
| `/scheduled-tasks` | scheduled-tasks | MainLayout → `@/views/ScheduledTasksView.vue` (child) | requiresAuth: true, title: '定时任务'   |
| `/`                | home            | MainLayout → `@/views/HomeView.vue` (child)           | requiresAuth: true                  |
| `/skills`          | skills          | MainLayout → `@/views/SkillsView.vue` (child)         | requiresAuth: true, title: 'Skills' |
| `/agents`          | agents          | MainLayout → `@/views/AgentsView.vue` (child)         | requiresAuth: true, title: '代理'     |
| `/mcp`             | mcp-square      | MainLayout → `@/views/McpSquareView.vue` (child)      | requiresAuth: true, title: 'MCP 广场' |
| `/mcp/:id`         | mcp-detail      | MainLayout → `@/views/McpDetailView.vue` (child)      | requiresAuth: true, title: 'MCP 详情' |
| `/login`           | login           | AuthLayout → `@/views/LoginView.vue` (child)          | guest: true, title: '登录'            |
| `/register`        | register        | AuthLayout → `@/views/RegisterView.vue` (child)       | guest: true, title: '注册'            |
| `/register/email`  | register-email  | AuthLayout → `@/views/EmailRegisterView.vue` (child)  | guest: true, title: '邮箱注册'          |
| `/oauth/callback`  | oauth-callback  | `@/views/OAuthCallbackView.vue`                       | guest: true, title: '第三方登录'         |
| `/:pathMatch(.*)*` | not-found       | — (redirect → /)                                      | —                                   |


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


| State                 | 类型                  | 说明          |
| --------------------- | ------------------- | ----------- |
| tokens                | `AuthTokens | null` | JWT Token 对 |
| user                  | `UserInfo | null`   | 当前用户信息      |
| loginLoading          | `boolean`           | 登录请求进行中     |
| loginError            | `string | null`     | 最近登录错误消息    |
| agreedProtocolVersion | `string | null`     | 已同意的协议版本    |



| Action                    | 说明                                               |
| ------------------------- | ------------------------------------------------ |
| loginWithPassword         | 调用 authApi.accountLogin → setTokens + setUser    |
| loginWithPhone            | 调用 authApi.phoneLogin → setTokens + setUser      |
| logout                    | 调用 authApi.logout → clearTokens                  |
| refreshAccessToken        | 去重锁机制，防止并发刷新                                     |
| setTokens(t, rememberMe?) | rememberMe=true → localStorage，反之 sessionStorage |
| clearTokens               | 清空 tokens + user                                 |


### 5.2 captchaStore (src/stores/captcha.ts)


| State         | 类型                     | 说明          |
| ------------- | ---------------------- | ----------- |
| modalVisible  | `boolean`              | 验证码弹窗可见性    |
| captchaType   | `'slide' | 'image'`    | 验证码类型       |
| pendingAction | `PendingAction | null` | 验证通过后的待处理操作 |
| smsCountdown  | `number`               | 短信重发倒计时     |
| smsErrorCount | `number`               | 短信发送失败次数    |
| dailySmsCount | `number`               | 当日已发送短信次数   |


### 5.3 MCP Store (src/stores/mcp.ts)（v1.3.0 新增）


| State         | 类型               | 说明        |
| ------------- | ---------------- | --------- |
| tools         | `McpTool[]`      | MCP 工具列表  |
| currentTool   | `McpTool | null` | 当前查看的工具详情 |
| loading       | `boolean`        | 列表加载中     |
| detailLoading | `boolean`        | 详情加载中     |
| error         | `string | null`  | 错误消息      |



| Getter         | 说明       |
| -------------- | -------- |
| installedTools | 已安装的工具列表 |
| officialTools  | 官方工具列表   |



| Action              | 说明                              |
| ------------------- | ------------------------------- |
| fetchTools(params?) | 获取工具列表（支持 category/search/sort） |
| fetchToolById(id)   | 获取工具详情                          |
| installTool(id)     | 安装工具（调用 API + 更新本地状态）           |
| uninstallTool(id)   | 卸载工具（调用 API + 更新本地状态）           |


### 5.4 Model Store (src/stores/model.ts)（v1.5.0 新增）


| State              | 类型                        | 说明           |
| ------------------ | ------------------------- | ------------ |
| providers          | `Ref<Provider[]>`         | 所有提供商（含嵌套模型） |
| selectedProviderId | `Ref<string | null>`      | 当前选中的提供商 ID  |
| loading            | `Ref<boolean>`            | 加载中          |
| error              | `Ref<string | null>`      | 错误消息         |
| providerSearch     | `Ref<string>`             | 提供商搜索关键词     |
| modelSearch        | `Ref<string>`             | 模型搜索关键词      |
| modelTypeFilter    | `Ref<ModelType | 'all'>`  | 模型类型筛选       |
| rightTab           | `Ref<'models' | 'usage'>` | 右侧面板标签页      |



| Getter             | 说明                                                  |
| ------------------ | --------------------------------------------------- |
| selectedProvider   | 当前选中的提供商（默认第一个）                                     |
| filteredProviders  | 按名称搜索过滤的提供商列表                                       |
| filteredModels     | 当前提供商的模型列表（按 search + typeFilter 过滤）                |
| totalModels        | 所有提供商模型总数                                           |
| typeCounts         | 全局模型类型统计: `{ [ModelType]: count }`                  |
| providerTypeCounts | 当前提供商模型类型统计                                         |
| providerStats      | 当前提供商统计: `{ total, totalCalls, inUse, deprecated }` |



| Action                                 | 说明                                  |
| -------------------------------------- | ----------------------------------- |
| fetchAll                               | 调用 modelApi.fetchProviders() 加载所有数据 |
| selectProvider(id)                     | 切换选中提供商，重置搜索/筛选                     |
| saveProvider(data)                     | 创建或更新提供商（根据 id 是否存在判断）              |
| deleteProvider(id)                     | 删除提供商                               |
| saveModel(data)                        | 创建或更新模型                             |
| deleteModel(providerId, modelId)       | 删除模型                                |
| cloneModel(providerId, modelId)        | 克隆模型                                |
| toggleModelStatus(providerId, modelId) | 切换模型状态                              |


### 5.5 ScheduledTask Store (src/stores/scheduledTask.ts)（v1.5.0 新增）


| State          | 类型                        | 说明       |
| -------------- | ------------------------- | -------- |
| tasks          | `Ref<CronTask[]>`         | 定时任务列表   |
| runs           | `Ref<RunRecord[]>`        | 运行记录列表   |
| loading        | `Ref<boolean>`            | 加载中      |
| error          | `Ref<string | null>`      | 错误消息     |
| taskSearch     | `Ref<string>`             | 任务搜索关键词  |
| taskFilter     | `Ref<TaskStatus | 'all'>` | 任务状态筛选   |
| runFilter      | `Ref<RunStatus | 'all'>`  | 运行记录状态筛选 |
| expandedTaskId | `Ref<string | null>`      | 展开的任务 ID |



| Getter        | 说明                                                                |
| ------------- | ----------------------------------------------------------------- |
| activeTasks   | 运行中的任务列表                                                          |
| nextTask      | 下一个将要执行的任务                                                        |
| filteredTasks | 按搜索 + 状态筛选后的任务列表                                                  |
| filteredRuns  | 按任务 + 状态筛选后的运行记录                                                  |
| taskStats     | 任务统计: `{ total, active, paused, error }`                          |
| runStats      | 运行统计: `{ total, success, failed, running, skipped, successRate }` |



| Action               | 说明                       |
| -------------------- | ------------------------ |
| fetchAll             | 加载任务列表 + 运行记录（Mock）      |
| createTask(data)     | 创建新任务（Mock）              |
| toggleTaskStatus(id) | 切换任务 active/paused（Mock） |
| cloneTask(id)        | 克隆任务（Mock）               |
| deleteTask(id)       | 删除任务（Mock）               |
| toggleExpand(id)     | 展开/折叠任务详情                |


### 5.6 Skill Store (src/stores/skill.ts)（v1.3.0 新增，v1.5.0 增强）


| State    | 类型              | 说明              |
| -------- | --------------- | --------------- |
| skills   | `Skill[]`       | 技能列表            |
| total    | `number`        | 技能总数            |
| loading  | `boolean`       | 加载中             |
| error    | `string | null` | 错误消息            |
| page     | `number`        | 当前页码（v1.5.0 新增） |
| pageSize | `number`        | 每页条数（v1.5.0 新增） |



| Getter         | 说明                                                   |
| -------------- | ---------------------------------------------------- |
| builtinSkills  | 内置技能（is_builtin=true）                                |
| customSkills   | 自定义技能（is_builtin=false）                              |
| enabledSkills  | 已启用的技能                                               |
| disabledSkills | 已禁用的技能                                               |
| categoryStats  | 分类统计: `{ [category]: { total, enabled, disabled } }` |



| Action                                            | 说明                                         |
| ------------------------------------------------- | ------------------------------------------ |
| fetchSkills(category?)                            | 获取技能列表（全量，兼容旧版）                            |
| fetchSkillsPaginated(category?, page?, pageSize?) | **v1.5.0 新增**：分页查询技能列表                     |
| searchSkills(name, page?, pageSize?)              | **v1.5.0 新增**：按名称模糊搜索                      |
| addSkill(data)                                    | 创建技能                                       |
| editSkill(id, data)                               | 更新技能                                       |
| removeSkill(id)                                   | 删除技能                                       |
| batchRemoveSkills(ids)                            | **v1.5.0 新增**：批量删除技能                       |
| toggleSkillEnabled(id, enabled)                   | 切换启用/禁用（乐观更新 + 失败回滚）                       |
| uploadSkillPackage(file)                          | **v1.5.0 新增**：上传技能压缩包（multipart/form-data） |


### 5.5 chatStore & uiStore

详见 [Part B — 聊天状态管理](#17-聊天状态管理)。

---

## 6. 类型定义

### 文件清单（v1.3.0 扩展）


| 文件                       | 导出类型                                                                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `types/api.ts`           | `ApiResponse<T>`, `SendSmsRequest`                                                                                                               |
| `types/auth.ts`          | `AuthTokens`, `UserInfo`, `AccountLoginRequest`, `PhoneLoginRequest`, `RegisterRequest`, `EmailRegisterRequest`, `AuthResponse`, `LoginFailInfo` |
| `types/captcha.ts`       | `SlidePuzzleData`, `SlideVerifyRequest`, `SlideVerifyResponse`, `ImageCaptchaData`                                                               |
| `types/components.ts`    | `LoginTabItem`, `FeatureItem`, `OAuthProvider`, `CaptchaResult`, `PendingAction`                                                                 |
| `types/mcp.ts`           | `McpTool`, `McpConfigField`, `InstallMcpRequest`, `MCP_CATEGORY_LABELS`, `MCP_CATEGORY_FILTERS`                                                  |
| `types/model.ts`         | `Provider`, `AIModel`, `ModelParam`, `ModelType`, `ModelStatus`, `ProviderStatus`, `MODEL_TYPE_META` (v1.5.0 新增)                                 |
| `types/scheduledTask.ts` | `CronTask`, `RunRecord`, `TaskStatus`, `RunStatus`, `TargetType`, `CreateTaskRequest`, `CRON_PRESETS` (v1.5.0 新增)                                |
| `types/skill.ts`         | `Skill`, `SkillCreateRequest`, `CATEGORY_LABELS`, `CATEGORY_FILTERS`                                                                             |
| `types/router.d.ts`      | 扩展 `RouteMeta: { title?, requiresAuth?, guest? }`                                                                                                |


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

### 7.2 API 模块（v1.5.0 扩展）


| 模块               | 接口方法                                                                                                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| authApi          | accountLogin, phoneLogin, register, emailRegister, logout, refreshToken, getFailCount, getPublicKey                                                               |
| captchaApi       | getSlidePuzzle, verifySlide, sendSms, getImageCaptcha, verifyImageCaptcha                                                                                         |
| oauthApi         | getAuthUrl, handleCallback                                                                                                                                        |
| conversationApi  | fetchConversations, fetchConversationMessages, renameConversation, deleteConversation                                                                             |
| agentApi         | fetchAgents, createAgent, deleteAgent, toggleAgentStatus, cloneAgent, addConfig, updateConfig, removeConfig, getFileContent, saveFileContent, getFileDescriptions |
| mcpApi           | fetchMcpTools, fetchMcpToolById, installMcpTool, uninstallMcpTool                                                                                                 |
| modelApi         | fetchProviders, createProvider, updateProvider, deleteProvider, createModel, updateModel, deleteModel, cloneModel, toggleModelStatus                              |
| scheduledTaskApi | fetchTasks, fetchRuns, createTask, toggleTaskStatus, deleteTask, cloneTask（Mock 实现）                                                                               |
| skillApi         | fetchSkills, fetchSkillsPaginated, searchSkills, createSkill, fetchSkill, updateSkill, deleteSkill, batchRemoveSkills, toggleSkill, uploadSkillPackage            |


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


| 场景   | 存储             | 有效期     |
| ---- | -------------- | ------- |
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


| 文件                                       | 数量  | 覆盖内容                                                    |
| ---------------------------------------- | --- | ------------------------------------------------------- |
| `stores/auth.test.ts`                    | 7   | 登录成功/失败, Token 持久化, 登出, 并发刷新去重锁, 刷新失败处理                 |
| `stores/captcha.test.ts`                 | 5   | modal 显隐, pendingAction, canSendSms, 倒计时, reset         |
| `composables/useCountdown.test.ts`       | 5   | 初始值, 每秒递减, isActive, stop, 不超 0                         |
| `composables/usePasswordEncrypt.test.ts` | 2   | 公钥获取缓存, 加密输出非空                                          |
| `router/guards.test.ts`                  | 4   | 未登录→/login, 已登录→/login 被拦截, 未登录可访问 guest 路由, query 参数保留 |


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

### 12.1 v1.5.0 文件变更统计


| 类型              | 数量  | 说明                                                                                                                                                                     |
| --------------- | --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 新增视图            | 3   | OverviewView, ModelsView, ScheduledTasksView                                                                                                                           |
| 新增 Stores       | 2   | model.ts, scheduledTask.ts                                                                                                                                             |
| 新增 API Services | 2   | modelApi.ts, scheduledTaskApi.ts                                                                                                                                       |
| 新增 Types        | 2   | model.ts, scheduledTask.ts                                                                                                                                             |
| 新增组件            | 2   | FileEditDialog.vue, MarkdownEditor.vue                                                                                                                                 |
| 重构文件            | 8   | agentApi.ts（Mock→真实API）, agent store（+文件状态）, skill store（+分页/上传/批量）, SideMenu.vue（+搜索）, router/index.ts（+3 路由）, TopBar.vue（+面包屑）, agent types（+文件类型）, skillApi.ts（+方法） |
| 新增依赖            | 1   | echarts + vue-echarts                                                                                                                                                  |


### 12.2 v1.3.0 文件变更统计


| 类型   | 数量  | 说明                                                                                                                                                                                |
| ---- | --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 新增文件 | 15  | MainLayout, McpCard, SkillCard, SkillDialog, iconMap, conversationApi, mcpApi, skillApi, mcp store, skill store, mcp types, skill types, SkillsView, McpSquareView, McpDetailView |
| 重构文件 | 6   | router/index.ts, stores/ui.ts, stores/chat.ts, services/request.ts, SideMenu.vue, RightPanel.vue                                                                                  |


### 12.3 npm 脚本


| 命令                   | 用途            |
| -------------------- | ------------- |
| `npm run dev`        | 启动 Vite 开发服务器 |
| `npm run build`      | 并行类型检查 + 生产构建 |
| `npm run type-check` | 仅类型检查         |
| `npm run test`       | 运行测试          |
| `npm run lint`       | ESLint 检查     |
| `npm run format`     | Prettier 格式化  |


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


| 项目       | 技术                           | 说明                                          |
| -------- | ---------------------------- | ------------------------------------------- |
| 布局       | Flexbox 三栏                   | SideMenu(左) + MainColumn(中) + RightPanel(右) |
| 页面框架     | MainLayout                   | SideMenu + TopBar + RouterView，支持多页面导航      |
| 流式通信     | fetch + ReadableStream       | 手动解析 SSE `data: { "token": "..." }\n\n` 格式  |
| Markdown | marked 库                     | 智能体回复渲染为富文本                                 |
| 自动滚动     | watch + nextTick + scrollTop | 监听 messages.length 和 lastContent 变化         |


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


| 属性  | 说明                                        |
| --- | ----------------------------------------- |
| 文件  | `src/components/MainLayout.vue`           |
| 功能  | 认证页面根布局，包含 SideMenu + TopBar + RouterView |
| 样式  | `display: flex; height: 100vh;`           |


### 15.2 AppShell


| 属性   | 说明                             |
| ---- | ------------------------------ |
| 文件   | `src/components/AppShell.vue`  |
| 功能   | 聊天页三栏布局（ChatMain + RightPanel） |
| 状态依赖 | uiStore（sidebar/panel 折叠态）     |


### 15.3 SideMenu（v1.5.0 更新）


| 属性  | 说明                                                  |
| --- | --------------------------------------------------- |
| 文件  | `src/components/SideMenu.vue`                       |
| 功能  | 可折叠左侧导航菜单，支持菜单分组折叠/展开、路由导航、路由高亮、**菜单搜索**（v1.5.0 新增） |


**v1.5.0 新增搜索功能：**

- 顶部搜索输入框（Search 图标），聚焦时展开搜索面板
- 搜索所有菜单项（按名称 + 拼音匹配），实时过滤显示结果
- 搜索结果按分组归类显示，点击结果项直接导航并清除搜索
- 未匹配时显示"未找到相关菜单"空状态
- 点击外部（`onClickOutside`）关闭搜索面板

**菜单分组（v1.5.0）：**


| 分组  | 项目                                                     |
| --- | ------------------------------------------------------ |
| 聊天  | 对话 (→ /), 概览 (→ /overview)                             |
| 控制  | 概览, 实例, 会话, 使用情况, 定时任务 (→ /scheduled-tasks)            |
| 代理  | 代理 (→ /agents), 技能 Hub (→ /skills), 节点, 模型 (→ /models) |
| 设置  | 配置, 文档                                                 |
| 后台  | 后台                                                     |


- 分组可点击折叠/展开（ChevronDown 旋转动画）
- 菜单项通过 `isItemActive()` 匹配 `route.path` 高亮
- 点击菜单项调用 `router.push(item.route)` 导航

### 15.4 RightPanel（v1.3.0 重构）


| 属性   | 说明                                               |
| ---- | ------------------------------------------------ |
| 文件   | `src/components/RightPanel.vue`                  |
| 功能   | 可折叠右侧历史对话面板，对接后端 Conversation API                |
| 数据来源 | `uiStore.histories`（通过 `fetchHistories()` 从后端获取） |
| 点击历史 | `chatStore.loadConversation(threadId)` → 加载消息并渲染 |
| 删除历史 | `uiStore.deleteHistory(threadId)` → 后端删除 + 本地更新  |


### 15.5 TopBar（v1.5.0 更新）


| 属性  | 说明                          |
| --- | --------------------------- |
| 文件  | `src/components/TopBar.vue` |
| 功能  | 顶部栏：面包屑导航 + 搜索框 + 通知 + 用户菜单 |


**v1.4.0 变更：**

- 搜索框从左侧移至右侧（靠右对齐）
- 左侧新增面包屑：根据 `useRoute()` 显示当前激活菜单的全路径（如 `聊天 > 对话`、`代理 > 代理`），路由映射在 `breadcrumb` computed 中
- 面包屑样式：分组名灰色 + ChevronRight 分隔符 + 当前项高亮

**路由到面包屑映射：**


| 路由                 | 面包屑          |
| ------------------ | ------------ |
| `/`                | 聊天 > 对话      |
| `/overview`        | 聊天 > 概览      |
| `/agents`          | 代理 > 代理      |
| `/models`          | 代理 > 模型      |
| `/skills`          | 代理 > 技能 Hub  |
| `/scheduled-tasks` | 控制 > 定时任务    |
| `/mcp`             | MCP > MCP 广场 |


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


| State      | 类型                   | 说明        |
| ---------- | -------------------- | --------- |
| `messages` | `Ref<ChatMessage[]>` | 所有消息      |
| `loading`  | `Ref<boolean>`       | 等待流式回复中   |
| `threadId` | `Ref<string | null>` | 当前对话线程 ID |



| Action                  | 说明                                 |
| ----------------------- | ---------------------------------- |
| `sendMessage(text)`     | 发送消息 → SSE 流式接收 → onDone 中自动刷新历史列表 |
| `clearMessages()`       | 清空消息 + 重置 loading + 重置 threadId    |
| `loadConversation(tid)` | **v1.3.0 新增**：从后端加载指定对话的消息并渲染      |


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


| State                 | 类型              | 默认值             | 说明            |
| --------------------- | --------------- | --------------- | ------------- |
| `sidebarCollapsed`    | `boolean`       | `false`         | 左侧菜单折叠态       |
| `rightPanelCollapsed` | `boolean`       | `false`         | 右侧面板折叠态       |
| `plusMenuOpen`        | `boolean`       | `false`         | 附件弹出菜单        |
| `searchQuery`         | `string`        | `''`            | 搜索框输入         |
| `selectedModel`       | `string`        | `'DeepSeek V4'` | 当前选中模型        |
| `histories`           | `HistoryItem[]` | `[]`            | 对话历史列表（从后端获取） |
| `activeThreadId`      | `string | null` | `null`          | 当前活跃对话线程 ID   |



| Action                                   | 说明                               |
| ---------------------------------------- | -------------------------------- |
| `fetchHistories()`                       | **v1.3.0 新增**：从后端获取对话列表          |
| `deleteHistory(thread_id)`               | **v1.3.0 更新**：调用后端 API 删除 + 本地移除 |
| `newConversation()`                      | 重置 activeThreadId + 关闭菜单         |
| `toggleSidebar()` / `toggleRightPanel()` | 翻转折叠态                            |


**v1.3.0 核心变更：**

- `HistoryItem` 接口从 `{id: number, title: string}` → `{thread_id: string, title: string}`
- `activeHistoryId: number` → `activeThreadId: string | null`
- `histories` 从硬编码预设 → `fetchHistories()` 从后端动态加载
- `deleteHistory` 从本地过滤 → 调用 `conversationApi.deleteConversation(thread_id)`

---

## 18. 聊天 API 接口对接

### 18.1 后端接口清单


| 接口                        | 方法     | 请求体                        | 响应体                                | 用途   |
| ------------------------- | ------ | -------------------------- | ---------------------------------- | ---- |
| `/api/chat`               | POST   | `{"message","thread_id?"}` | `{"response","thread_id"}`         | 普通对话 |
| `/api/chat/stream`        | POST   | `{"message","thread_id?"}` | SSE 流                              | 流式对话 |
| `/api/conversations`      | GET    | —                          | `[{thread_id, title, updated_at}]` | 对话列表 |
| `/api/conversations/{id}` | GET    | —                          | `{thread_id, title, messages}`     | 对话消息 |
| `/api/conversations/{id}` | PATCH  | `{title}`                  | `{thread_id, title}`               | 重命名  |
| `/api/conversations/{id}` | DELETE | —                          | —                                  | 删除对话 |


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


| 需求编号    | 需求描述                                 | 实现状态      | 实现文件                                                |
| ------- | ------------------------------------ | --------- | --------------------------------------------------- |
| F1 对话界面 | 上方消息列表 + 下方输入区，左右对齐，自动滚动             | 完全实现 + 超越 | AppShell, MessageList, MessageItem, InputBar        |
| F2 普通对话 | POST /api/chat，完整回复                  | 已实现       | request.ts sendChatRequest()                        |
| F3 流式对话 | POST /api/chat/stream，SSE 逐 token 推送 | 完全实现      | request.ts sendStreamRequest, chatStore.sendMessage |
| F4 状态管理 | Pinia chatStore                      | 完全实现 + 超越 | chatStore + uiStore + mcpStore + skillStore         |
| F5 界面样式 | 暗色主题                                 | 已升级       | v1.1.0 暗色主题 + Legacy 兼容层                            |


### 19.2 待实现项


| 项目        | 优先级 | 说明                                                  |
| --------- | --- | --------------------------------------------------- |
| 定时任务后端对接  | P1  | ScheduledTasksView 当前全 Mock 实现，需后端 API              |
| 搜索功能      | P3  | TopBar 搜索框无实际搜索逻辑                                   |
| 通知功能      | P3  | TopBar 铃铛按钮无交互                                      |
| 用户菜单完善    | P3  | 可补充个人设置等入口                                          |
| 注册表单提交    | P2  | RegisterForm 和 EmailRegisterForm 的 submit 为 TODO 占位 |
| MCP 创建功能  | P3  | "创建 MCP"按钮 TODO 占位                                  |
| 概览仪表盘后端对接 | P3  | OverviewView 数据全部 Mock，需后端统计 API                    |


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


| 属性    | 说明                             |
| ----- | ------------------------------ |
| Props | `tool: McpTool`                |
| Emits | `click(tool)`, `install(tool)` |


卡片展示内容：图标 + 名称 + 官方标识 + 作者 + 描述 + 标签 + 安装数 + 评分 + 安装/已安装按钮

### 20.4 McpDetailView 详情页


| 标签页  | 内容                                         |
| ---- | ------------------------------------------ |
| 概述   | 简介 + 核心功能列表 + 信息面板（版本/作者/许可证/仓库/分类/更新）+ 标签 |
| 配置   | 配置参数列表（名称/类型/必填/描述）                        |
| 使用说明 | 安装方式/运行环境/自动启动说明                           |
| 评价   | 用户评价（占位，暂无数据）                              |


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


| key             | 中文   |
| --------------- | ---- |
| code_execution  | 代码执行 |
| search          | 搜索   |
| data_analysis   | 数据分析 |
| file_management | 文件管理 |
| notification    | 通知   |
| database        | 数据库  |
| dev_tools       | 开发工具 |
| collaboration   | 协作   |
| container       | 容器   |
| custom          | 自定义  |


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


| 属性    | 说明                                              |
| ----- | ----------------------------------------------- |
| Props | `skill: Skill`                                  |
| Emits | `edit(skill)`, `delete(skill)`, `toggle(skill)` |


卡片展示内容：图标（Lucide 动态组件）+ 名称 + 内置标识 + 启用开关 + 描述 + 分类标签 + 操作按钮（编辑/删除，仅自定义技能）

### 21.4 SkillDialog 创建/编辑弹窗


| 标签页   | 功能                        | 说明                                                    |
| ----- | ------------------------- | ----------------------------------------------------- |
| 从仓库下载 | 选择仓库 → 获取技能列表 → 勾选 → 批量导入 | 支持 ClawHub/Anthropic/LangChain/CrewAI/AutoGen + 自定义地址 |
| 本地上传  | 拖拽或点击上传文件 → 校验格式 + 必需字段   | 支持 .json/.yaml/.yml/.md/.zip                          |
| 手动创建  | 填写表单（名称/描述/图标/分类/Prompt）  | 编辑已有技能时直接进入此标签                                        |


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


| key      | 中文  |
| -------- | --- |
| search   | 搜索  |
| code     | 代码  |
| creative | 创意  |
| analysis | 分析  |
| tools    | 工具  |
| custom   | 自定义 |


### 21.7 图标映射（iconMap.ts）

支持 12 种 Lucide 图标：Globe, Code2, Image, BarChart3, FolderOpen, Zap, Search, FileText, Database, Palette, Music, Wrench。通过 `getSkillIcon(name)` 函数查找，未匹配时默认返回 Zap。

---

---

## 22. 代理管理模块概述

### 22.1 需求背景

代理管理模块（左侧菜单"代理" → `/agents`）提供智能体（Agent）的集中管理功能：树形列表浏览、配置项管理（文件/工具/技能/Cron Jobs）、主子智能体关系图可视化。

### 22.2 核心功能


| 功能      | 说明                                                           |
| ------- | ------------------------------------------------------------ |
| 智能体列表树  | 左侧面板，主智能体为根节点，子智能体为子节点，支持搜索过滤、展开/折叠、状态图标                     |
| 多标签配置面板 | 右侧面板四个标签页：文件 (Files)、工具 (Tools)、技能 (Skills)、Cron Jobs，点击标签切换 |
| 关系图可视化  | 点击眼睛图标切换，Vue Flow 绘制主子智能体连接关系图                               |
| 智能体操作   | 新建子智能体（三点下拉菜单）、克隆、删除（不可删除智能体受保护）、启停状态                        |
| 配置管理    | 每个标签页内添加/移除配置项（通过弹窗表单）                                       |


### 22.3 术语规范（v1.4.0）


| 术语        | 说明                                 |
| --------- | ---------------------------------- |
| 主智能体      | 顶层 Agent，type='main'，可拥有子智能体       |
| 子智能体      | 从属 Agent，type='sub'，挂载于主智能体下       |
| 通用子智能体    | 默认不可删除的子智能体 (sub-1)，具备与主智能体相同的全部工具 |
| 研究子智能体    | 默认子智能体 (sub-2)，专注于网络搜索和深入研究        |
| Cron Jobs | 原"提示词"功能重命名，type='prompt'，定时任务配置   |
| 文件        | 新增配置类型，type='file'，默认 7 个 .md 文件   |


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


| 属性    | 说明                                                                                     |
| ----- | -------------------------------------------------------------------------------------- |
| 文件    | `src/components/agent/AgentListItem.vue`                                               |
| Props | `agent: Agent`, `agents: Agent[]`, `selectedId`, `expandedIds`, `searchQuery`, `level` |
| Emits | `select`, `toggleExpand`, `toggleStatus`, `clone`, `delete`, `newSubAgent`             |
| 功能    | 递归树节点组件，支持展开/折叠、三点下拉菜单、状态标签                                                            |


**展示内容：** 名称 + 状态标签（运行中/已停止/错误）+ 类型标识（主智能体 Blue 徽章）+ 描述 + 统计（调用数/工具数/技能数/子智能体数）

**三点下拉菜单项：**


| 命令          | 图标         | 说明                                        |
| ----------- | ---------- | ----------------------------------------- |
| newSubAgent | UserPlus   | 新建子智能体                                    |
| toggle      | Pause/Play | 启动/停止（分隔线前）                               |
| clone       | Copy       | 克隆                                        |
| delete      | Trash2     | 删除（分隔线前，红色，v-if="!agent.undeletable" 时显示） |


**v1.4.0 关键特性：**

- 不可删除智能体（`undeletable: true`）隐藏"删除"菜单项
- 搜索时展平显示所有匹配项，无搜索时树形递归渲染
- 选中状态蓝色渐变高亮 + "编辑中"标签

### 24.2 AgentDetail — 智能体详情配置面板


| 属性    | 说明                                                                                |
| ----- | --------------------------------------------------------------------------------- |
| 文件    | `src/components/agent/AgentDetail.vue`                                            |
| Props | `agent: Agent`, `agents: Agent[]`                                                 |
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


| type   | label       | 图标       | 颜色               | key     |
| ------ | ----------- | -------- | ---------------- | ------- |
| file   | 文件 (Files)  | FileText | yellow (#eab308) | files   |
| tool   | 工具 (Tools)  | Settings | blue (#3b82f6)   | tools   |
| skill  | 技能 (Skills) | Sparkles | purple (#8b5cf6) | skills  |
| prompt | Cron Jobs   | Clock    | green (#22c55e)  | prompts |


### 24.3 AddConfigDialog — 添加配置弹窗


| 属性    | 说明                                                      |
| ----- | ------------------------------------------------------- |
| 文件    | `src/components/agent/AddConfigDialog.vue`              |
| Props | `visible`, `type: ConfigType`, `agentName`, `agentType` |
| Emits | `close`, `add(type, value)`                             |


**弹窗内容：** 头部（类型图标 + "添加{类型}" + 目标智能体信息）、表单（名称 + 可选描述）、底部（取消/添加按钮）

**各类型占位提示：**


| type     | 名称占位                         | 描述占位                |
| -------- | ---------------------------- | ------------------- |
| file     | 例如: config.yaml, data.json   | 描述此文件的用途和内容...      |
| tool     | 例如: web_search, file_reader  | 描述此工具的功能和用途...      |
| skill    | 例如: code_analysis, debugging | 描述此技能的能力和应用场景...    |
| prompt   | 例如: 每天执行一次, 每小时检查            | 输入 Cron 表达式和执行任务... |
| subagent | 例如: 数据处理子智能体                 | 描述此子智能体的职责和功能...    |


---

## 25. 代理关系图设计

### 25.1 整体架构

主子智能体关系图使用 Vue Flow（ReactFlow 的 Vue 3 移植）构建，dagre 自动布局，@vueuse/motion 动画。

### 25.2 AgentGraph — 主图组件


| 属性  | 说明                                    |
| --- | ------------------------------------- |
| 文件  | `src/components/agent/AgentGraph.vue` |
| 依赖  | `useAgentGraph()` composable          |
| 功能  | Vue Flow 画布容器，包含 header 控制栏、画布区域、空状态  |


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


| 操作          | 解锁状态 | 锁定状态 |
| ----------- | ---- | ---- |
| 画布拖动        | ✓    | ✗    |
| 节点拖动        | ✓    | ✗    |
| 滚轮缩放        | ✓    | ✗    |
| Controls 缩放 | ✓    | ✓    |
| 节点点击        | ✓    | ✓    |
| MiniMap 导航  | ✓    | ✓    |


**最大化模式：** `isMaximized=true` 时组件使用 `position: fixed; inset: 0; z-index: 1000` 覆盖全屏，带动画过渡。

**锁定/解锁按钮：** 点击时旋转动画反馈（CSS transition）。

### 25.3 AgentNode — 自定义 Vue Flow 节点


| 属性             | 说明                                          |
| -------------- | ------------------------------------------- |
| 文件             | `src/components/agent/AgentNode.vue`        |
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


| 属性             | 说明                                                                                     |
| -------------- | -------------------------------------------------------------------------------------- |
| 文件             | `src/components/agent/AgentEdge.vue`                                                   |
| Vue Flow Props | `sourceX/Y`, `targetX/Y`, `sourcePosition`, `targetPosition`, `id`, `data: { status }` |


**边样式：**

- 使用 `getBezierPath()` 计算贝塞尔曲线路径
- 活跃代理：蓝紫渐变（`#3b82f6` → `#8b5cf6`）实线 + 紫色箭头（`MarkerType.ArrowClosed`）
- 非活跃代理：灰色渐变（`#6b7280` → `#4b5563`）虚线 (`stroke-dasharray: 6,4`) + 灰色箭头
- 活跃边添加 `animated: true`，产生流动动画

**渐变实现：** 每条边内部定义唯一 ID 的 `<linearGradient>` + `<defs>`，通过 `stroke: url(#edge-grad-{id})` 引用。

### 25.5 useAgentGraph — 图数据 Composables


| 属性  | 说明                                 |
| --- | ---------------------------------- |
| 文件  | `src/composables/useAgentGraph.ts` |


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

### 26.1 agentStore (src/stores/agent.ts)（v1.5.0 更新）


| State              | 类型                             | 说明                       |
| ------------------ | ------------------------------ | ------------------------ |
| agents             | `Ref<Agent[]>`                 | 所有智能体                    |
| selectedAgentId    | `Ref<string | null>`           | 当前选中智能体 ID               |
| loading            | `Ref<boolean>`                 | 列表加载中                    |
| error              | `Ref<string | null>`           | 错误消息                     |
| searchQuery        | `Ref<string>`                  | 搜索关键词                    |
| expandedIds        | `Ref<Set<string>>`             | 已展开的智能体 ID 集合            |
| currentFileContent | `Ref<AgentFileContent | null>` | **v1.5.0 新增**：当前编辑的文件内容  |
| fileLoading        | `Ref<boolean>`                 | **v1.5.0 新增**：文件加载中      |
| selectedFilename   | `Ref<string | null>`           | **v1.5.0 新增**：当前选中的文件名   |
| fileDescriptions   | `Ref<Record<string, string>>`  | **v1.5.0 新增**：文件名 → 描述映射 |



| Getter         | 说明                                    |
| -------------- | ------------------------------------- |
| selectedAgent  | 当前选中智能体对象                             |
| mainAgent      | type='main' 的智能体                      |
| subAgents      | type='sub' 的所有智能体                     |
| filteredAgents | 搜索时展平匹配，无搜索时返回主智能体（树根）                |
| stats          | { total, active, inactive, error } 计数 |



| Action                                      | 说明                                                       |
| ------------------------------------------- | -------------------------------------------------------- |
| fetchAgents                                 | **v1.5.0 变更**：调用后端真实 API `/agents` 加载列表，默认选中主智能体         |
| selectAgent(id)                             | 设置 selectedAgentId                                       |
| toggleExpand(id)                            | 在 expandedIds 中添加/移除                                     |
| expandAll / collapseAll                     | 全展开 / 全折叠                                                |
| toggleStatus(id)                            | 调用 agentApi.toggleAgentStatus() 切换运行/停止                  |
| cloneAgent(id)                              | 调用 agentApi.cloneAgent() 克隆                              |
| deleteAgent(id)                             | 调用 agentApi.deleteAgent() 删除                             |
| addConfig(type, value)                      | 调用 agentApi.addConfig() 添加配置                             |
| updateConfig(type, value, newValue, desc)   | **v1.5.0 新增**：调用 agentApi.updateConfig() 更新文件配置          |
| removeConfig(type, value)                   | 调用 agentApi.removeConfig() 移除配置                          |
| createSubAgent(name)                        | 调用 agentApi.createAgent() 创建子智能体                         |
| fetchFileContent(agentId, filename)         | **v1.5.0 新增**：调用 agentApi.getFileContent() 加载文件内容        |
| saveFileContent(agentId, filename, content) | **v1.5.0 新增**：调用 agentApi.saveFileContent() 保存文件内容       |
| fetchFileDescriptions(agentId)              | **v1.5.0 新增**：调用 agentApi.getFileDescriptions() 加载文件描述列表 |


---

## 27. 代理 API 服务层（v1.5.0 重构）

### 27.1 agentApi — 真实后端 API 对接


| 属性  | 说明                                                                     |
| --- | ---------------------------------------------------------------------- |
| 文件  | `src/services/agentApi.ts`                                             |
| 说明  | **v1.5.0 重大变更**：从 Mock 实现切换为后端真实 API 调用；所有请求通过 `request.ts` Axios 实例发送 |


**字段转换（snake_case ↔ camelCase）：**

`toAgent()` 函数负责将后端 snake_case 字段转换为前端 camelCase：

- `sub_agents` → `subAgents`
- `parent_id` → `parentId`
- `last_active` → `lastActive`
- `call_count` → `callCount`
- `undeletable` → `undeletable`

**API 方法（共 12 个，均对接后端真实接口）：**


| 方法                                                   | HTTP   | 端点                               | 说明                                     |
| ---------------------------------------------------- | ------ | -------------------------------- | -------------------------------------- |
| fetchAgents()                                        | GET    | `/agents`                        | 获取智能体列表（`res.data.data.agents` 路径提取）   |
| createAgent(data)                                    | POST   | `/agents`                        | 创建智能体（name, description, parent_id）    |
| deleteAgent(id)                                      | DELETE | `/agents/{id}`                   | 删除智能体（主智能体级联删除子智能体）                    |
| toggleAgentStatus(id)                                | PATCH  | `/agents/{id}/status`            | 切换 active ↔ inactive                   |
| cloneAgent(id)                                       | POST   | `/agents/{id}/clone`             | 克隆智能体（含文件内容）                           |
| addConfig(agentId, type, value, desc?)               | POST   | `/agents/{id}/config`            | 添加配置项（tool/skill/prompt/file/subagent） |
| updateConfig(agentId, type, value, newValue?, desc?) | PUT    | `/agents/{id}/config`            | 更新配置（文件重命名/修改描述）                       |
| removeConfig(agentId, type, value)                   | DELETE | `/agents/{id}/config`            | 移除配置项（子智能体类型会删除子智能体）                   |
| getFileContent(agentId, filename)                    | GET    | `/agents/{id}/files/{filename}`  | 获取文件内容（首访自动创建空记录）                      |
| saveFileContent(agentId, filename, content)          | PUT    | `/agents/{id}/files/{filename}`  | 保存文件内容（upsert）                         |
| getFileDescriptions(agentId)                         | GET    | `/agents/{id}/file-descriptions` | 获取文件描述列表                               |


**v1.5.0 新增组件：**

- `FileEditDialog.vue`：文件内容编辑弹窗（调用 `getFileContent` / `saveFileContent`）
- `MarkdownEditor.vue`：Markdown 编辑器（支持语法高亮 + 预览）

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

## 29. 概览仪表盘模块

### 29.1 概述

概览仪表盘（`OverviewView.vue`，路由 `/overview`）提供系统运营状态的集中可视化展示，使用 **ECharts 6** 进行图表渲染。

### 29.2 页面结构

```
OverviewView.vue
├── 页面标题 + 时间周期切换按钮（日/月/年）
├── 统计卡片行（4 个卡片）
│   ├── 总用户数（Users 图标，紫蓝渐变）
│   ├── 活跃智能体（Bot 图标，青绿渐变）
│   ├── 今日调用（Activity 图标，橙黄渐变）
│   └── 成功率（Shield 图标，翠绿渐变）
│   （每个卡片含趋势箭头 + 百分比 + 副标题）
├── 图表区（2 列网格）
│   ├── 调用趋势图（ECharts 折线图 + 面积渐变）
│   ├── 智能体使用分布（ECharts 南丁格尔玫瑰饼图）
│   ├── Token 消耗统计（ECharts 柱状图 + 趋势线）
│   └── 响应时间分布（ECharts 热力/柱状图）
├── 系统资源区
│   ├── CPU 使用率（进度条）
│   ├── 内存使用率（进度条）
│   ├── 磁盘 I/O（进度条）
│   └── 网络带宽（进度条）
├── 功能区（2 列）
│   ├── 顶级用户排名表（用户名/角色/调用数/Tokens/在线状态，含排名徽章）
│   └── 模型提供商卡片（名称/模型数/用量进度条/热门模型）
├── 系统指标行（API 延迟 / 队列长度 / 错误率 / 正常运行时间）
└── 操作日志区（时间线 + 事件类型图标 + 时间戳）
```

### 29.3 技术实现


| 组件   | 技术                      | 说明                                |
| ---- | ----------------------- | --------------------------------- |
| 图表渲染 | ECharts 6 + vue-echarts | `shallowRef` 持有实例，响应式 `option` 更新 |
| 响应式  | `watch` + `resize`      | 监听 `period` 切换 + 窗口尺寸变化重新渲染       |
| 数据   | Mock（静态定义）              | 6 组数据集：统计/趋势/使用分布/Token/响应时间/延迟   |
| 周期切换 | `ref<Period>('day')`    | day / month / year 三按钮切换，更新所有图表数据 |
| 时钟   | `setInterval`           | 每秒更新一次 `currentTime` 显示           |


### 29.4 ECharts 实例管理

```typescript
// 使用 shallowRef 避免深度响应式导致的性能问题
const trendChart = shallowRef<echarts.ECharts>()
const usageChart = shallowRef<echarts.ECharts>()

// 每个图表的 initOption 使用 computed 动态计算
// watch 监听数据变化自动调用 setOption(opt, { notMerge: true })
// onUnmounted 中 dispose 清理
```

---

## 30. 模型管理模块

### 30.1 概述

模型管理页面（`ModelsView.vue`，路由 `/models`）提供 AI 模型和提供商的集中管理功能。

### 30.2 页面结构

```
ModelsView.vue（双面板布局）
├── panel-left（提供商列表，280px）
│   ├── header：搜索框 + "添加"按钮
│   └── provider-list
│       └── ProviderItem × N（logo + 名称 + 状态点 + 模型计数）
├── panel-right（模型详情）
│   ├── header：提供商信息 + 状态徽章 + 操作按钮（编辑/删除）
│   ├── 标签切换：models | usage（使用统计）
│   ├── 筛选栏：搜索框 + 类型筛选（全部/LLM/Vision/Audio/Video/Embedding/Image-Gen/Speech）
│   └── model-grid
│       └── ModelCard × N
│           ├── 头部：模型图标（emoji）+ display_name + 状态徽章
│           ├── 信息行：类型标签 / 上下文窗口 / 调用次数 / 发布日期
│           ├── 参数列表（可折叠）: { key: label = value }
│           ├── usedByAgents 标签
│           └── 操作：编辑 / 克隆 / 切换状态 / 删除
└── 弹窗：
    ├── ProviderDialog（名称/图标/API Base/API Key/描述/官网）
    ├── ModelDialog（display_name/name/type/status/context_window/description/params 编辑器）
    └── DeleteConfirm（级联删除警告）


### 30.3 模型数据模型

```typescript
type ModelType = 'llm' | 'vision' | 'audio' | 'video' | 'embedding' | 'image-gen' | 'speech'
type ModelStatus = 'active' | 'beta' | 'deprecated' | 'inactive'
type ProviderStatus = 'connected' | 'error' | 'unconfigured'

interface ModelParam { key: string; label: string; value: number | string; min?: number; max?: number; step?: number; type: 'number' | 'text' | 'select'; options?: string[] }

interface AIModel {
  id: string; name: string; displayName: string
  type: ModelType; status: ModelStatus
  contextWindow?: number; usedByAgents: string[]
  callCount: number; params: ModelParam[]
  description: string; releaseDate?: string
}

interface Provider {
  id: string; name: string; logo: string
  status: ProviderStatus; apiBase: string; apiKey: string
  models: AIModel[]; description: string; website: string
}
```

### 30.4 模型类型元数据


| type      | 标签    | emoji | 颜色     |
| --------- | ----- | ----- | ------ |
| llm       | 大语言模型 | 💬    | indigo |
| vision    | 视觉模型  | 👁️   | purple |
| audio     | 音频模型  | 🎵    | green  |
| video     | 视频模型  | 🎬    | pink   |
| embedding | 向量模型  | 🔢    | cyan   |
| image-gen | 图像生成  | 🎨    | amber  |
| speech    | 语音合成  | 🗣️   | teal   |


### 30.5 modelApi 服务


| 方法                                     | HTTP   | 端点                                        | 说明             |
| -------------------------------------- | ------ | ----------------------------------------- | -------------- |
| fetchProviders()                       | GET    | `/providers`                              | 获取所有提供商（含嵌套模型） |
| createProvider(data)                   | POST   | `/providers`                              | 创建提供商          |
| updateProvider(id, data)               | PUT    | `/providers/{id}`                         | 更新提供商          |
| deleteProvider(id)                     | DELETE | `/providers/{id}`                         | 删除提供商（级联删除模型）  |
| createModel(providerId, data)          | POST   | `/providers/{id}/models`                  | 创建模型           |
| updateModel(providerId, modelId, data) | PUT    | `/providers/{id}/models/{modelId}`        | 更新模型           |
| deleteModel(providerId, modelId)       | DELETE | `/providers/{id}/models/{modelId}`        | 删除模型           |
| cloneModel(providerId, modelId)        | POST   | `/providers/{id}/models/{modelId}/clone`  | 克隆模型           |
| toggleModelStatus(providerId, modelId) | PATCH  | `/providers/{id}/models/{modelId}/status` | 切换状态           |


字段转换函数 `toProvider()` / `toModel()` 负责 snake_case → camelCase 映射。

---

---

## 31. 定时任务模块

### 31.1 概述

定时任务管理页面（`ScheduledTasksView.vue`，路由 `/scheduled-tasks`）提供 Cron 定时任务的集中管理。当前为 **Mock 实现**，后端 API 就绪后切换到真实接口。

### 31.2 页面结构

```
ScheduledTasksView.vue
├── header：标题 + 统计卡片行（总数/运行中/已暂停/异常 + 趋势箭头）
├── 工具栏：搜索框 + 状态筛选 + "创建任务"按钮
├── task-list
│   └── TaskItem × N（可展开）
│       ├── 基本信息：名称 + 描述 + 状态徽章 + 标签
│       ├── Cron 信息：表达式 + 标签 + 下次执行时间
│       ├── 执行统计：成功率 + 总次数 + 平均耗时 + 上次运行时间
│       └── 操作：启动/暂停 / 克隆 / 删除
│       └── [展开] 运行日志面板
│           ├── 运行筛选（全部/成功/失败/运行中/跳过）
│           └── RunRecord × N
│               ├── 状态图标 + 触发方式（定时/手动）
│               ├── 开始时间 + 耗时
│               └── 输出摘要
└── 创建/编辑弹窗
    ├── 名称 + 描述
    ├── Cron 表达式（可选择预设：每分钟/每5分钟/每小时/每天/每周一/每月1日 等 8 个）
    ├── 目标类型下拉（代理 Agent / 技能 Skill / 工具 Tool / 提示词 Prompt）
    ├── 目标选择 + 标签
    └── 提交按钮
```

### 31.3 定时任务数据模型

```typescript
type TaskStatus = 'active' | 'paused' | 'error'
type RunStatus = 'success' | 'failed' | 'running' | 'skipped'
type TargetType = 'agent' | 'skill' | 'tool' | 'prompt'

interface CronTask {
  id: string; name: string; description: string
  cron: string; cronLabel: string
  status: TaskStatus
  target: string; targetType: TargetType
  lastRun: string | null; nextRun: string
  successRate: number; totalRuns: number
  avgDuration: string; tags: string[]
}

interface RunRecord {
  id: string; taskId: string; taskName: string
  status: RunStatus
  startTime: string; duration: string
  output: string
  trigger: 'scheduled' | 'manual'
}
```

### 31.4 Cron 预设表达式


| 标签        | 表达式            |
| --------- | -------------- |
| 每分钟       | `* * * * *`    |
| 每 5 分钟    | `*/5 * * * *`  |
| 每 15 分钟   | `*/15 * * * *` |
| 每小时       | `0 * * * *`    |
| 每天 00:00  | `0 0 * * *`    |
| 每天 02:00  | `0 2 * * *`    |
| 每周一 03:00 | `0 3 * * 1`    |
| 每月 1 日    | `0 0 1 * *`    |


### 31.5 scheduledTaskApi（Mock 实现）

所有方法操作内存中的 mockTasks 和 mockRuns 数组，无网络请求：

- `fetchTasks()` / `fetchRuns()` — 返回 mock 数据
- `createTask(data)` — 创建任务（id: `st-{timestamp}`，默认 status: active）
- `toggleTaskStatus(id)` — 切换 active/paused/error
- `deleteTask(id)` — 删除任务
- `cloneTask(id)` — 克隆任务（name + "(副本)"，id + "-clone"）

### 31.6 待后端对接

定时任务模块当前为全 Mock 实现。后端需提供 ScheduledTask CRUD API 后，操作与 agentApi/modelApi 模式一致：添加字段转换函数 → 替换 service 函数实现 → 删除 Memory 数组。

---

## Part F — 知识库模块（v1.6.0 新增）

### 32. 知识库模块概述

知识库管理页面（`KnowledgeBaseView.vue`，路由 `/knowledge-base`）提供完整的 RAG 知识库管理功能——知识库 CRUD、文档上传与索引管理、知识图谱可视化、分块级编辑、混合检索。对接真实后端 API（23 个端点），使用 5s 轮询刷新索引进度。

### 33. 知识库页面布局

```
KnowledgeBaseView.vue
├── KbStatCard.vue                 ← 统计概览栏（知识库数/文档数/实体数/关系数）
├── 列表/网格切换 + 搜索框 + "创建知识库"按钮
├── KbCard.vue × N                 ← 知识库卡片列表
│   ├── 名称 + 描述 + 状态徽章
│   ├── 文档数/分块数/实体数/关系数
│   └── 操作：详情 / 编辑 / 删除
├── KbCreateDialog.vue             ← 创建知识库弹窗
│   ├── 名称 + 描述 + 标签
│   └── 初始索引配置（切片策略/大小/重叠等）
└── KbDetail.vue                   ← 知识库详情视图（选中后展示）
    ├── KbOverviewTab.vue           ← 概览标签：统计卡片 + 最近文档 + 实体/关系趋势
    ├── KbDocsTab.vue               ← 文档标签
    │   ├── 上传按钮 → KbUploadDialog.vue（多文件上传）
    │   ├── 文档列表（分页 + 状态筛选 + 搜索）
    │   ├── KbDocStatusBadge.vue    ← 文档状态徽章（queued/parsing/chunking/.../indexed/failed）
    │   ├── KbIndexingPipeline.vue  ← 8 阶段索引流水线可视化
    │   └── KbDocDetailDrawer.vue   ← 文档详情抽屉
    │       ├── 基本信息 + 流水线进度
    │       ├── 分块列表（分页）
    │       └── KbFragmentEditor.vue ← 分块内容编辑器（重嵌入）
    ├── KbConfigTab.vue             ← 配置标签
    │   ├── 切片策略（fixed/recursive/semantic/markdown）
    │   ├── 嵌入模型选择 + 维度
    │   ├── 稀疏检索算法 + BM25 参数
    │   ├── 实体/关系提取模型
    │   ├── 重排序模型 + topK + 混合权重
    │   └── KbConfigSummary.vue     ← 配置摘要卡片
    ├── KbGraphTab.vue              ← 知识图谱标签（d3-force 力导向图）
    │   ├── KbGraphNode.vue × N     ← 实体节点（8 种类型颜色区分）
    │   ├── KbGraphEdge.vue × N     ← 关系边
    │   └── 实体类型筛选 + 重提取按钮
    └── KbSearchTab.vue             ← 检索标签
        ├── 搜索框 + 检索模式（向量/BM25/混合）
        ├── alpha 混合权重滑块
        └── 搜索结果列表（含相关度分数）
```

### 34. 知识库核心组件设计

#### 34.1 KbIndexingPipeline — 8 阶段流水线可视化

知识库文档索引过程展示为 8 阶段进度条：排队 → 解析 → 切片 → 向量化 → BM25 → 抽取 → 已索引。每个阶段显示状态（pending/active/done/failed）+ 进度百分比。

#### 34.2 KbDocDetailDrawer + KbFragmentEditor

文档详情抽屉展示文档信息 + 分块列表。每个分块可展开查看内容并支持在线编辑，保存后自动触发重嵌入。

#### 34.3 KbUploadDialog

多文件上传弹窗，支持拖拽或浏览选择，最多 20 个文件同时上传。上传后自动入队索引。

### 35. 知识图谱可视化设计

知识图谱使用 **d3-force** 力导向布局，实体节点按类型着色（8 种颜色），关系边带标签，支持拖拽/缩放/悬停高亮。Entity 类型：

| type | 标签 | 颜色 |
|------|------|------|
| person | 人物 | blue |
| organization | 组织 | green |
| product | 产品 | orange |
| concept | 概念 | purple |
| algorithm | 算法 | red |
| location | 地点 | teal |
| time | 时间 | gray |
| event | 事件 | pink |

### 36. 知识库状态管理

**knowledgeBase Store (`src/stores/knowledgeBase.ts`)：**

```typescript
// State
kbs: KnowledgeBase[]; selectedKb: KnowledgeBase | null
selectedDoc: KbDocument | null; viewMode: 'grid' | 'list'
stats: KbStats | null; searchQuery: string; loading: boolean

// Actions
fetchKbs()                    // GET /knowledge-bases
selectKb(id)                  // GET /knowledge-bases/:id
createKb(data)                // POST /knowledge-bases
updateKb(id, data)            // PUT /knowledge-bases/:id
deleteKb(id)                  // DELETE /knowledge-bases/:id
uploadDocs(kbId, files)       // POST /knowledge-bases/:id/documents/upload (multipart)
deleteDoc(kbId, docId)        // DELETE /knowledge-bases/:id/documents/:id
retryDoc(kbId, docId)         // POST /knowledge-bases/:id/documents/:id/retry
reindexKb(kbId)               // POST /knowledge-bases/:id/reindex (10min timeout)
fetchGraph(kbId)              // GET /knowledge-bases/:id/graph
reExtractGraph(kbId)          // POST /knowledge-bases/:id/graph/re-extract
startIndexPolling(kbId)       // 5s 间隔轮询 indexing-activity
stopIndexPolling()            // 停止轮询
```

### 37. 知识库 API 服务层

**knowledgeBaseApi (`src/services/knowledgeBaseApi.ts`)：** 对接 23 个后端端点：

| 方法 | HTTP | 端点 | 说明 |
|------|------|------|------|
| fetchKnowledgeBases | GET | `/knowledge-bases` | 知识库列表 |
| fetchKnowledgeBase | GET | `/knowledge-bases/:id` | 知识库详情 |
| createKnowledgeBase | POST | `/knowledge-bases` | 创建知识库 |
| updateKnowledgeBase | PUT | `/knowledge-bases/:id` | 更新知识库 |
| deleteKnowledgeBase | DELETE | `/knowledge-bases/:id` | 删除知识库 |
| fetchStats | GET | `/knowledge-bases/stats` | 统计信息 |
| uploadDocuments | POST | `/knowledge-bases/:id/documents/upload` | 上传文档（multipart） |
| fetchDocuments | GET | `/knowledge-bases/:id/documents` | 文档列表（分页） |
| fetchDocument | GET | `/knowledge-bases/:id/documents/:docId` | 文档详情 |
| deleteDocument | DELETE | `/knowledge-bases/:id/documents/:docId` | 删除文档 |
| retryDocument | POST | `/knowledge-bases/:id/documents/:docId/retry` | 重试失败文档 |
| fetchGraphData | GET | `/knowledge-bases/:id/graph` | 知识图谱数据 |
| reExtractGraph | POST | `/knowledge-bases/:id/graph/re-extract` | 重提取图谱 |
| fetchIndexingActivity | GET | `/knowledge-bases/:id/indexing-activity` | 索引活动 |
| fetchAvailableModels | GET | `/knowledge-bases/available-models` | 可用模型筛选 |
| fetchAvailableProviders | GET | `/knowledge-bases/available-providers` | 可用提供商筛选 |
| reindexKnowledgeBase | POST | `/knowledge-bases/:id/reindex` | 重索引 |
| fetchDocumentChunks | GET | `.../chunks` | 文档分块列表 |
| fetchChunkDetail | GET | `.../chunks/:chunkId` | 分块详情 |
| updateChunkContent | PUT | `.../chunks/:chunkId` | 更新分块 |
| deleteChunk | DELETE | `.../chunks/:chunkId` | 删除分块 |
| batchChunkOp | POST | `.../chunks/batch` | 批量操作 |

### 38. 知识库类型定义

**`src/types/knowledgeBase.ts`（v1.6.0 新增）：**

```typescript
interface IndexConfig {
  chunk_strategy: string; chunk_size: number; chunk_overlap: number
  embedding_model: string; embedding_dim: number
  sparse_algo: string; bm25_k1: number; bm25_b: number
  entity_model: string; relation_model: string; enable_graph: boolean
  reranker_model: string; enable_reranker: boolean
  top_k: number; hybrid_alpha: number
}

interface KnowledgeBase {
  id: string; name: string; description: string; status: string
  config: IndexConfig; tags: string[]
  docs_count: number; chunks_count: number
  entities_count: number; relations_count: number
  size_bytes: number; created_at: string; updated_at: string
}

interface KbDocument {
  id: string; kb_id: string; name: string; type: string
  size_bytes: number; status: DocStatus; progress: number
  chunks_count: number; entities_count: number; relations_count: number
  uploaded_at: string; indexed_at: string | null; error_message: string
}

type DocStatus = 'queued' | 'parsing' | 'chunking' | 'embedding'
  | 'bm25' | 'extracting' | 'indexed' | 'failed'

interface KbEntity { id: string; name: string; type: string; mentions: number }
interface KbRelation { id: string; from_entity: string; to_entity: string; label: string; weight: number }
```

---

## Part G — 工具管理模块（v1.6.0 新增）

### 39. 工具管理模块概述

工具管理页面（`ToolsView.vue`，路由 `/tools`）提供内置和第三方工具的集中浏览与管理——卡片网格展示、无限滚动分页、来源/分类/状态筛选、工具详情抽屉、启用/禁用切换。对接真实后端 API。

### 40. 工具管理页面布局

```
ToolsView.vue
├── 统计栏：总数 / 内置 / 第三方 / 启用 / 禁用 / 不可用
├── 来源标签切换（全部 / 内置 / 第三方）
├── 搜索框 + 分类筛选 chips + 状态筛选
├── ToolCard.vue × N（卡片网格 + 无限滚动）
│   ├── 图标 + 名称 + 显示名称
│   ├── 源标签（内置/第三方）+ 分类标签 + 状态指示
│   ├── 版本号 + 作者
│   └── 操作：切换启用 / 编辑 / 删除
├── ToolDetailDrawer.vue          ← 右侧滑出详情抽屉
│   ├── 基本信息（名称/显示名/描述/版本/作者/分类）
│   ├── 参数定义列表
│   ├── 标签 + 关联智能体列表
│   └── 创建/更新时间
└── ToolDialog.vue                ← 创建/编辑工具弹窗
    ├── 名称 + 显示名 + 描述
    ├── 分类 + 图标
    ├── 参数定义（动态添加/删除）
    └── 标签编辑
```

### 41. 工具管理状态管理

**toolStore (`src/stores/tool.ts`)：**

```typescript
// State
tools: Tool[]; total: number; page: number; pageSize: number
loading: boolean; loadingMore: boolean; hasMore: boolean
categories: string[]; sourceFilter: string

// Actions
fetchTools(params)    // GET /tools/list（分页 + 筛选）
loadMore()            // 追加下一页（无限滚动）
addTool(data)         // POST /tools
editTool(id, data)    // PUT /tools/:id
removeTool(id)        // DELETE /tools/:id
toggleToolEnabled(id) // PATCH /tools/:id/toggle
```

### 42. 工具管理 API 服务层

**toolApi (`src/services/toolApi.ts`)：**

| 方法 | HTTP | 端点 | 说明 |
|------|------|------|------|
| fetchTools | GET | `/tools/list` | 工具列表（分页 + 筛选：source/category/status/keyword） |
| createTool | POST | `/tools` | 创建第三方工具 |
| updateTool | PUT | `/tools/:id` | 更新工具 |
| deleteTool | DELETE | `/tools/:id` | 删除工具（内置工具不可删） |
| toggleTool | PATCH | `/tools/:id/toggle` | 切换启用/禁用 |

---

## Part H — 后台管理模块（v1.6.0 新增，Mock）

### 43. 后台管理模块概述

后台管理子系统包含 4 个页面，路由前缀 `/admin`。**当前均为 Mock 实现**（内存数据，无 HTTP 请求），后端 API 就绪后切换。

### 44. 仪表盘页面

**AdminView.vue（路由 `/admin`）** — 14 个功能瓷砖（系统设置/菜单配置/通知管理/计费/人员管理/RBAC/API密钥/审计/AI配置/特性配置/插件/集成/数据管理/DevOps）+ 系统信息卡片 + 更新日志时间线 + 补丁更新 + 推荐资源。全 Mock。

### 45. 人员管理页面

**UserManagementView.vue（路由 `/admin/users`）** — 左栏部门树（递归 DepartmentTreeNode，10 个部门）+ 右栏用户列表（卡片/表格视图切换 + 搜索/部门筛选 + 创建/编辑/删除）。全 Mock。

### 46. 角色权限页面

**RbacView.vue（路由 `/admin/rbac`）** — 左栏角色列表（5 个内置角色：超级管理员/管理员/经理/成员/访客）+ 右栏双标签：
- **功能权限**：PermissionTreeNode 层级树（目录→菜单→按钮），三态复选框（全选/半选/未选）
- **数据权限**：DataScopeSelector 每个数据资源选择范围（全部/部门及子部门/本部门/本人/无）

全 Mock，超级管理员角色只读。

### 47. 菜单配置页面

**MenuConfigView.vue（路由 `/admin/menu-config`）** — 左栏 MenuConfigTreeNode 资源树（目录/菜单/按钮三级递归）+ 右栏三标签：
- **基本信息**：标签/权限键/路径/图标/排序/状态
- **按钮资源**：选中菜单的子按钮列表
- **角色覆盖**：拥有此权限的角色列表

全 Mock，支持创建/编辑/删除节点。

**后台管理 Store/API 汇总：**

| Store | API Service | 数据来源 | 核心功能 |
|-------|------------|----------|----------|
| adminStore | adminApi | Mock | 14 个仪表盘瓷砖 + 系统统计 + 更新日志 |
| userManagementStore | adminApi | Mock | 部门树 + 用户 CRUD + 卡片/表格视图 |
| rbacStore | adminApi | Mock | 5 个角色 + 权限树（三态）+ 数据范围 |
| menuConfigStore | adminApi | Mock | 资源树编辑 + 角色覆盖 |

---

> 本文档 v1.6.0 基于实际代码实现全面更新。v1.6.0 重点新增了知识库模块（KnowledgeBaseView + 16 个 KB 组件 + knowledgeBaseApi 23 个端点 + knowledgeBase Store + d3-force 知识图谱 + 5s 轮询索引状态 + 8 阶段流水线可视化）、Tools 工具管理模块（ToolsView + 3 组件 + 无限滚动 + toolApi + toolStore）、后台管理模块（AdminView/UserManagementView/RbacView/MenuConfigView 共 4 页面 + 10 个 admin 组件 + 4 个 admin Store + adminApi，全 Mock）；路由新增 6 个页面（/knowledge-base, /tools, /admin, /admin/users, /admin/rbac, /admin/menu-config）；主路由重定向从 /chat 变更为 /overview；Stores 从 9 个扩展到 15 个；API Services 从 9 个扩展到 13 个；Types 从 10 个扩展到 14 个；视图从 12 个扩展到 18 个；组件从 ~48 个扩展到 ~63 个；新增 d3-force 依赖用于知识图谱力导向布局；新增 TracePanel 对话追踪面板；新增 useKnowledgeGraph composable。

