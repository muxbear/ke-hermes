# ke-hermes Frontend

Vue 3 前端应用，TypeScript + Element Plus。

## 技术栈

- **框架**: Vue 3 (Composition API) + TypeScript 5.5
- **构建**: Vite 5
- **UI**: Element Plus 2 (自动按需导入 unplugin-vue-components)
- **状态**: Pinia
- **路由**: Vue Router 4 (history 模式)
- **HTTP**: Axios (拦截器注入 Token + 自动刷新)
- **流式**: SSE (fetch ReadableStream) 用于对话
- **国际化**: vue-i18n
- **样式**: SCSS
- **图表**: ECharts 6 + vue-echarts (概览仪表盘)
- **测试**: Vitest + jsdom + @vue/test-utils

## 目录结构

```
frontend/src/
├── main.ts             # 应用入口, 挂载 Pinia/Router/i18n/ElementPlus
├── App.vue             # 根组件
├── views/              # 页面级组件 (12 个)
│   ├── HomeView.vue    # 对话页面
│   ├── OverviewView.vue # 概览仪表盘 (ECharts)
│   ├── AgentsView.vue  # 智能体管理
│   ├── ModelsView.vue  # 模型管理
│   ├── SkillsView.vue  # 技能管理
│   ├── McpSquareView.vue # MCP 广场
│   ├── McpDetailView.vue # MCP 详情
│   ├── ScheduledTasksView.vue # 定时任务
│   ├── LoginView.vue   # 登录
│   ├── RegisterView.vue # 手机号注册
│   ├── EmailRegisterView.vue # 邮箱注册
│   └── OAuthCallbackView.vue # OAuth 回调
├── components/         # 通用组件
│   ├── auth/           #   登录/注册布局
│   ├── captcha/        #   滑块验证码
│   ├── common/         #   通用小组件
│   ├── mcp/            #   MCP 工具卡片
│   ├── skill/          #   技能卡片/弹窗
│   ├── agent/          #   智能体列表/详情/图/节点/边/弹窗
│   ├── MainLayout.vue  #   认证后根布局 (SideMenu + TopBar + RouterView)
│   ├── AppShell.vue    #   聊天三栏布局
│   ├── ChatMain.vue    #   聊天主区域 (ChatHeader + MessageList + InputBar)
│   ├── ChatHeader.vue  #   对话头部 (含模型选择器)
│   ├── MessageList.vue #   消息列表 (自动滚动)
│   ├── MessageItem.vue #   单条消息 (Markdown 渲染)
│   ├── InputBar.vue    #   消息输入栏
│   ├── SideMenu.vue    #   侧边菜单 (含搜索)
│   ├── RightPanel.vue  #   右侧历史面板
│   └── TopBar.vue      #   顶部栏 (面包屑)
├── composables/        # 组合式函数 (useAuth, useCaptcha, useCountdown, useAgentGraph 等)
├── stores/             # Pinia stores (auth, captcha, chat, ui, agent, mcp, model, scheduledTask, skill)
├── services/           # API 层
│   ├── request.ts      #   Axios 实例 + 拦截器 + SSE 流式请求
│   ├── authApi.ts      #   认证接口
│   ├── captchaApi.ts   #   验证码接口
│   ├── oauthApi.ts     #   OAuth 接口
│   ├── agentApi.ts     #   智能体 CRUD + 文件接口
│   ├── conversationApi.ts # 对话历史接口
│   ├── mcpApi.ts       #   MCP 工具接口
│   ├── modelApi.ts     #   模型/提供商接口
│   ├── scheduledTaskApi.ts # 定时任务接口 (Mock)
│   └── skillApi.ts     #   技能接口
├── router/             # 路由配置 + 全局守卫
├── types/              # TypeScript 类型定义 (10 个模块)
└── locales/            # i18n 语言文件
```

## 路由

| 路径 | 权限 | 说明 |
|------|------|------|
| `/` | 需登录 | 主页 (对话界面) |
| `/overview` | 需登录 | 概览仪表盘 |
| `/agents` | 需登录 | 智能体管理 |
| `/models` | 需登录 | 模型管理 |
| `/skills` | 需登录 | 技能管理 |
| `/scheduled-tasks` | 需登录 | 定时任务 |
| `/mcp` | 需登录 | MCP 广场 |
| `/mcp/:id` | 需登录 | MCP 详情 |
| `/login` | 游客 | 登录 |
| `/register` | 游客 | 手机号注册 |
| `/register/email` | 游客 | 邮箱注册 |
| `/oauth/callback` | 游客 | OAuth 回调 |

- 需登录页面未认证 → 跳转 `/login?redirect=xxx`
- 已认证访问游客页面 → 跳转 `/`

## 环境变量

- `VITE_API_BASE_URL` — API 基础路径 (默认 `/api`)
- `VITE_ALLOW_PASTE_PASSWORD` — 是否允许粘贴密码

## 常用命令

```bash
cd frontend
npm install          # 安装依赖
npm run dev          # 启动开发服务器 (localhost:5173)
npm run build        # 生产构建
npm run lint         # ESLint
npm run format       # Prettier 格式化
npm run test         # 运行测试
npm run type-check   # TypeScript 类型检查
```

## 代码规范

- **组件**: PascalCase 文件名, `<script setup lang="ts">`
- **Composables**: 文件名 `useXxx.ts`, 驼峰命名
- **Stores**: Pinia Composition API 风格 (`defineStore`)
- **API**: 统一使用 `src/services/request.ts` 导出的 axios 实例, 响应格式 `ApiResponse<T>`
- **Token**: `auth_tokens` 存储在 localStorage (持久) / sessionStorage (会话), request.ts 拦截器自动读取
- **测试文件**: `tests/` 目录, 命名 `*.test.ts`
- **类型检查**: `vue-tsc --build` 通过后才能构建
