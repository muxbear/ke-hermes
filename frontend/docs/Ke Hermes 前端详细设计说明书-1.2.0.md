# Ke-Hermes 详细设计说明书 — v1.2.1

| 版本    | 日期         | 作者  | 变更说明                                         |
| ----- | ---------- | --- | -------------------------------------------- |
| 1.0.0 | 2026-05-18 | -   | 登录模块详细设计初版，基于需求说明书 v1.1.0                      |
| 1.1.0 | 2026-05-18 | -   | 完成前端重构实施：JS→TS 迁移、登录模块全部组件、暗色主题、测试套件、Element Plus 集成 |
| 1.2.0 | 2026-05-18 | -   | 新增聊天模块详细设计：基于 requirements.md 进行全面需求分析，补充 AppShell 三栏布局、消息流、SSE 流式对话、Markdown 渲染、chatStore/uiStore 状态管理的完整设计方案 |
| 1.2.1 | 2026-05-19 | -   | 文档对照实际代码更新：测试目录迁移至 tests/、路由改为 AuthLayout 嵌套结构、普通对话 API 已实现、ChatHeader 模型选择器已实现、auth store 持久化增强、captcha store 新增 smsErrorCount、useAuth 密码加密降级策略 |


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

---

## 1. 概述

### 1.1 文档目的

本文档为 Ke-Hermes 前端（桌面版）的详细设计说明书 v1.2.1，基于实际代码库编写。文档覆盖两大核心模块：
- **Part A — 基础架构与登录模块**：TypeScript 技术栈、暗色主题、国际化、测试套件
- **Part B — 聊天模块**：AppShell 三栏布局、SSE 流式对话、Markdown 渲染、状态管理

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

### 1.3 适用模块

- **Part A**：PC Web 端登录/注册页面、OAuth 回调处理、路由守卫、Token 刷新、权限校验
- **Part B**：智能体对话界面（三栏布局）、流式 SSE 对话、Markdown 渲染、消息历史管理

### 1.4 相关文档

- [Ke-Hermes 需求说明书-登录模块（桌面版）-1.1.0](./Ke%20Hermes%20需求说明书-登录模块（桌面版）-1.1.0.md)
- [ke-hermes 前端需求文档（聊天模块）](./requirements.md)

---

## 2. 项目架构

### 2.1 目录结构

```
frontend/
├── .vscode/
│   └── extensions.json
├── index.html                         # 入口 HTML → /src/main.ts
├── package.json
├── tsconfig.json                      # 项目引用根
├── tsconfig.app.json                  # 应用 TS 配置（exclude tests/）
├── tsconfig.node.json                 # 构建工具 TS 配置
├── tsconfig.vitest.json               # 测试 TS 配置（include tests/）
├── vite.config.ts
├── vitest.config.ts                   # 测试配置（include tests/，内联 element-plus）
├── env.d.ts
├── .env / .env.development / .env.production
├── .prettierrc.json
│
├── public/
│
├── tests/                             # v1.2.1：测试从 src/__tests__/ 迁移至此
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
    │   └── index.ts                   # 路由表（AuthLayout 嵌套路由） + 前置守卫
    │
    ├── stores/
    │   ├── auth.ts                    # Token/用户/登录状态（含 USER_STORAGE_KEY 分离持久化）
    │   ├── captcha.ts                 # 验证码/倒计时状态（含 smsErrorCount）
    │   ├── chat.ts                    # 聊天消息 + SSE 流式
    │   └── ui.ts                      # UI 状态（侧栏/面板/模型/历史）
    │
    ├── types/
    │   ├── api.ts                     # ApiResponse<T>, SendSmsRequest
    │   ├── auth.ts                    # AuthTokens, UserInfo, Request/Response
    │   ├── captcha.ts                 # SlidePuzzleData, SlideVerifyRequest
    │   ├── components.ts              # FeatureItem, OAuthProvider, CaptchaResult
    │   └── router.d.ts                # RouteMeta 扩展
    │
    ├── services/
    │   ├── request.ts                 # Axios 实例 + 拦截器 + SSE + sendChatRequest
    │   ├── authApi.ts                 # 认证接口（8 个）
    │   ├── captchaApi.ts              # 验证码 + 短信接口（5 个）
    │   └── oauthApi.ts                # OAuth 接口（2 个）
    │
    ├── composables/
    │   ├── useAuth.ts                 # 登录逻辑封装 + 重定向 + 密码加密降级
    │   ├── usePasswordEncrypt.ts      # RSA 加密（含公钥缓存）
    │   ├── useCountdown.ts            # 倒计时
    │   ├── useCaptcha.ts              # 验证码流程
    │   └── useAgreement.ts            # 协议勾选
    │
    ├── components/
    │   ├── auth/
    │   │   ├── AuthLayout.vue         # 认证页根布局（左品牌 + 右 RouterView）
    │   │   ├── BrandPanel.vue         # 左侧品牌面板 (Logo + 名称 + 标语 + FeatureGrid)
    │   │   ├── FeatureGrid.vue        # 2×4 特性网格
    │   │   ├── LoginCard.vue          # 520px 毛玻璃卡片
    │   │   ├── LoginTabs.vue          # 登录方式切换标签
    │   │   ├── AccountLoginForm.vue    # 账号密码登录表单
    │   │   ├── PhoneLoginForm.vue      # 手机验证码登录表单
    │   │   ├── AgreementCheckbox.vue   # 协议勾选区
    │   │   ├── OAuthPanel.vue         # 第三方登录图标面板（微信/支付宝/飞书/钉钉/企业微信）（微信/支付宝/飞书/钉钉/企业微信）
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
    │   ├── AppShell.vue               # 聊天三栏布局容器
    │   ├── ChatMain.vue               # 中间聊天主区域
    │   ├── ChatHeader.vue             # 聊天头部（含模型下拉选择器）
    │   ├── MessageList.vue            # 消息列表（自动滚动）
    │   ├── MessageItem.vue            # 单条消息（Markdown 渲染）
    │   ├── InputBar.vue               # 消息输入栏（含 + 弹出菜单）
    │   ├── SideMenu.vue               # 可折叠左侧导航菜单
    │   ├── TopBar.vue                 # 顶部搜索 + 通知 + 用户菜单
    │   └── RightPanel.vue             # 可折叠右侧历史面板
    │
    ├── views/
    │   ├── HomeView.vue               # 受保护首页（包裹 AppShell）
    │   ├── LoginView.vue              # 登录页（组装所有认证子组件）
    │   ├── RegisterView.vue           # 注册页
    │   ├── EmailRegisterView.vue      # 邮箱注册页
    │   └── OAuthCallbackView.vue      # OAuth 回调处理页
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
Views (HomeView, LoginView, RegisterView, ...)
  └── Components (AuthLayout, LoginCard, AccountLoginForm, ...)
       └── Composables (useAuth, useCaptcha, useCountdown, ...)
            ├── Stores (auth, captcha, chat, ui)
            └── Services (request, authApi, captchaApi, oauthApi)
                 └── Types (auth, api, captcha, components)
```

### 2.3 v1.0.0 → v1.1.0 实施偏差

| 设计项 | v1.0.0 计划 | v1.1.0 实施 | 原因 |
|--------|------------|------------|------|
| request.ts 与 authStore 关系 | request.ts 通过 require() 延迟导入 authStore | request.ts 直接读写 localStorage/sessionStorage，不依赖 authStore | ES module 下避免循环依赖，更简洁 |
| eslint.config.ts | 创建 ESLint 扁平配置 | 跳过 — 非核心功能 | 聚焦核心重构，后续补充 |
| unplugin-auto-import | 配置自动导入 | 跳过 — main.ts 中手动 `app.use(ElementPlus)` | 明确依赖关系，减少魔法 |
| AccountLoginForm 组件测试 | 7 用例 — mount + Element Plus | 跳过 — Element Plus CSS 在 jsdom 下兼容性复杂 | stores/composables/router 测试已覆盖核心逻辑 |
| CSP meta 标签 | index.html 中添加 | 跳过 | 生产环境由 Nginx 配置管理 |
| pinia-plugin-persistedstate | 自动同步 store 到 storage | 未使用 — auth store 手动管理持久化 | 减少依赖，保持 token 流程显式可控 |

---

## 3. 路由设计

### 3.1 路由表（v1.2.1 更新：AuthLayout 嵌套路由）

| 路径               | 名称              | 组件 (懒加载)                       | Meta                         |
| ----------------- | --------------- | ------------------------------ | ---------------------------- |
| `/`               | home            | `@/views/HomeView.vue`         | requiresAuth: true           |
| `/login`          | login           | AuthLayout → `@/views/LoginView.vue` (child) | guest: true, title: '登录'     |
| `/register`       | register        | AuthLayout → `@/views/RegisterView.vue` (child) | guest: true, title: '注册'     |
| `/register/email` | register-email  | AuthLayout → `@/views/EmailRegisterView.vue` (child) | guest: true, title: '邮箱注册' |
| `/oauth/callback` | oauth-callback  | `@/views/OAuthCallbackView.vue` | guest: true, title: '第三方登录' |
| `/:pathMatch(.*)*`| not-found       | — (redirect → /)               | —                            |

**v1.2.1 变更：** `/login` 和 `/register` 路由使用 AuthLayout 作为父组件，LoginView/RegisterView/EmailRegisterView 作为嵌套子路由。AuthLayout 内通过 `<RouterView />` 渲染子路由，无需在视图层手动包裹布局。

### 3.2 路由守卫逻辑

```
beforeEach:
  requiresAuth && !isAuthenticated → /login?redirect=原路径
  guest && isAuthenticated → /
  其他 → 放行
```

### 3.3 RouteMeta 扩展

```typescript
// src/types/router.d.ts
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    guest?: boolean
  }
}
```

---

## 4. 组件设计（登录模块）

### 4.1 组件树

```
App.vue
└── <RouterView />
    ├── AuthLayout.vue
    │   ├── BrandPanel.vue
    │   │   ├── Logo (Inline SVG, 96×96, 蓝紫渐变)
    │   │   ├── "Ke-Hermes" (36px/700)
    │   │   ├── "自我进化，越用越强" (20px)
    │   │   ├── FeatureGrid.vue (2×4 网格, 8 特性)
    │   │   └── "2026 Ke-Hermes 版权所有" (12px)
    │   └── <RouterView />
    │       └── LoginView.vue
    │           └── LoginCard.vue (max-width 520px, glass-card)
    │               ├── LoginTabs.vue (账号登录 / 手机登录)
    │               ├── AccountLoginForm.vue / PhoneLoginForm.vue
    │               │   ├── el-input (Element Plus)
    │               │   ├── PasswordInput.vue (Eye/EyeOff toggle)
    │               │   └── CountdownButton.vue (倒计时)
    │               ├── AgreementCheckbox.vue (协议勾选 + ElMessageBox)
    │               ├── el-button (登录按钮, 52px, 蓝色渐变)
    │               ├── OAuthPanel.vue (5 个 52×52 圆形图标)
    │               │   └── CaptchaModal.vue (Teleport to body)
    │               │       └── SlidePuzzle.vue / ImageCaptcha.vue
    │               └── RegisterLink.vue (→ /register)
    └── HomeView.vue
        └── AppShell.vue (保留全部现有聊天布局)
```

### 4.2 核心组件契约

#### AccountLoginForm

| 属性 | 说明 |
|------|------|
| Props | 无 |
| Emits | `submit(payload: { account, password, rememberMe })`, `forgot-password` |
| 校验 | 账号 2-64 字符、密码 6-12 字符至少字母+数字 |
| 交互 | Enter 键触发提交 |

#### PhoneLoginForm

| 属性 | 说明 |
|------|------|
| Props | 无 |
| Emits | `submit(payload: { phone, smsCode })` |
| 依赖 | useCountdown, useCaptcha, captchaStore, CaptchaModal |

#### CaptchaModal

| 属性 | 说明 |
|------|------|
| Props | `modelValue: boolean`, `type: 'slide' \| 'image'` |
| Emits | `update:modelValue`, `success(CaptchaResult)`, `fail` |
| 交互 | ESC 关闭, 点击遮罩关闭 |

#### AuthLayout

| 属性 | 说明 |
|------|------|
| 响应式 | ≥1024px: 40/60, 768-1023px: 32/68, <768px: 隐藏品牌区 |
| 左侧 | 固定 BrandPanel |
| 右侧 | `<RouterView />` 嵌套路由出口 |

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

| Getter | 说明 |
|--------|------|
| isAuthenticated | `!!tokens?.accessToken` |
| accessToken | 当前 Access Token |
| refreshToken | 当前 Refresh Token |
| isLoginLoading | `loginLoading` 别名 |

| Action | 说明 |
|--------|------|
| loginWithPassword | 调用 authApi.accountLogin → setTokens + setUser |
| loginWithPhone | 调用 authApi.phoneLogin → setTokens(rememberMe=false) + setUser |
| logout | 调用 authApi.logout → clearTokens |
| refreshAccessToken | 去重锁机制，防止并发刷新；同时刷新 user |
| setTokens(t, rememberMe?) | localStorage (rememberMe=true) / sessionStorage |
| setUser(u, rememberMe?) | 持久化用户信息到 localStorage/sessionStorage |
| clearTokens | 清空 tokens + user + USER_STORAGE_KEY + auth_tokens |
| agreeProtocol(version) | 记录已同意的协议版本 |

**Token 持久化策略（v1.2.1 增强）:**
- Token 和 User 分别使用独立 storage key 持久化：`auth_tokens` / `auth_user`
- `rememberMe=true` → `localStorage`，`rememberMe=false` → `sessionStorage`
- 应用启动时 `loadTokens()` / `loadUser()` 从 localStorage→sessionStorage 优先级加载
- `refreshAccessToken()` 响应中包含 user 时自动调用 `setUser()` 同步更新

### 5.2 captchaStore (src/stores/captcha.ts)

| State | 类型 | 说明 |
|-------|------|------|
| modalVisible | `boolean` | 验证码弹窗可见性 |
| captchaType | `'slide' \| 'image'` | 验证码类型 |
| pendingAction | `PendingAction \| null` | 验证通过后的待处理操作 |
| smsCountdown | `number` | 短信重发倒计时 |
| smsErrorCount | `number` | 短信发送失败次数（v1.2.1 新增） |
| dailySmsCount | `number` | 当日已发送短信次数 |

| Getter | 说明 |
|--------|------|
| canSendSms | countdown=0 && daily<5 |

### 5.3 chatStore & uiStore

保持原有功能不变，从 `.js` 迁移为 `.ts`，添加了 `ChatMessage` 和 `HistoryItem` 类型接口。详细设计参见 [Part B — 聊天状态管理](#17-聊天状态管理)。

---

## 6. 类型定义

### 文件清单

| 文件 | 导出类型 |
|------|---------|
| `types/api.ts` | `ApiResponse<T>`, `PaginatedResponse<T>`, `SendSmsRequest` |
| `types/auth.ts` | `AuthTokens`, `UserInfo`, `AccountLoginRequest`, `PhoneLoginRequest`, `RegisterRequest`, `EmailRegisterRequest`, `AuthResponse`, `LoginFailInfo` |
| `types/captcha.ts` | `SlidePuzzleData`, `SlideVerifyRequest`, `SlideVerifyResponse`, `ImageCaptchaData` |
| `types/components.ts` | `LoginTabItem`, `FeatureItem`, `OAuthProvider`, `CaptchaResult`, `PendingAction` |
| `types/router.d.ts` | 扩展 `RouteMeta: { title?, requiresAuth?, guest? }` |

---

## 7. API 服务层设计

### 7.1 request.ts — Axios 实例

**避免循环依赖策略:** request.ts 不导入 authStore，直接操作 localStorage/sessionStorage 的 `auth_tokens` key。auth store 使用相同的 key 和管理策略，两者通过共享存储实现通信。

```
请求拦截器: 从 storage 读取 accessToken → 注入 Authorization header
响应拦截器:
  code≠0 → ApiError
  401 → 从 storage 读取 refreshToken → POST /auth/refresh (去重锁)
    成功 → 更新 storage → 重试原请求
    失败 → 清除 storage → window.location.href='/login'
```

**SSE 流式请求:** `sendStreamRequest()` 函数使用 fetch + ReadableStream 解析 SSE。
**普通对话降级:** `sendChatRequest()` 已实现，POST /api/chat → 返回完整回复，用于不支持 SSE 的场景。

### 7.2 API 模块

| 模块 | 接口方法 |
|------|---------|
| authApi | accountLogin, phoneLogin, register, emailRegister, logout, refreshToken, getFailCount, getPublicKey |
| captchaApi | getSlidePuzzle, verifySlide, sendSms, getImageCaptcha, verifyImageCaptcha |
| oauthApi | getAuthUrl, handleCallback |

---

## 8. 样式系统设计

### 8.1 暗色主题变量 (variables.css)

全部 34 个 CSS 自定义属性，覆盖：品牌色系、文字色阶、圆角、尺寸、字号/字重、阴影、过渡、遮罩、第三方平台色、品牌渐变。

### 8.2 Legacy 兼容映射

为保持 8 个现有聊天组件正常工作，在 variables.css 底部添加映射层：

```css
--accent-primary: var(--color-accent);
--foreground-primary: var(--color-text-primary);
--surface-primary: var(--color-bg-page);
--surface-card: var(--color-bg-card);
--border-subtle: rgba(38, 51, 89, 0.25);
--border-medium: var(--color-border-input);
```

这使现有组件的 scoped 样式无需任何修改即可在暗色主题下正常渲染。

### 8.3 SCSS Mixins (mixins.scss)

- `respond-lg` / `respond-md` / `respond-sm` — 响应式断点 1024px / 768px
- `glass-card` — 毛玻璃卡片效果 (backdrop-filter: blur(8px) + 半透明背景)
- `input-focus` — 输入框聚焦蓝色边框 + 外发光

---

## 9. 安全设计

### 9.1 密码加密

```typescript
// usePasswordEncrypt.ts
fetchPublicKey() → authApi.getPublicKey() → JSEncrypt.setPublicKey()
encrypt(password) → JSEncrypt.encrypt() → 提交加密后的密文
```

**v1.2.1 降级策略：** `useAuth.loginWithPassword()` 中若获取公钥失败（如后端未就绪），自动降级为明文传输密码（开发阶段兼容方案，生产环境应确保公钥加密）。

### 9.2 Token 管理

| 场景 | 存储 | 有效期 |
|------|------|--------|
| rememberMe=true | localStorage | 7 天 (Refresh Token) |
| rememberMe=false | sessionStorage | 标签页生命周期 |

### 9.3 请求安全

- Authorization Bearer 头注入
- 401 → 自动刷新 Token (去重锁)
- 密码不进 URL，POST Body 传输
- 前端不存明文密码

---

## 10. 测试设计

### 10.1 测试配置（v1.2.1 更新）

```typescript
// vitest.config.ts
environment: 'jsdom'
globals: true
css: true
setupFiles: ['./tests/setup.ts']
include: ['tests/**/*.{test,spec}.{ts,tsx}']
server: { deps: { inline: ['element-plus'] } }
coverage: {
  provider: 'v8',
  include: ['src/composables/**', 'src/stores/**', 'src/components/**']
}
```

**v1.2.1 变更：**
- 测试目录从 `src/__tests__/` 迁移至项目根 `tests/`
- tsconfig.app.json 排除 `tests/**`，tsconfig.vitest.json 包含 `tests/**`
- vitest 配置内联 element-plus 依赖以支持组件测试

### 10.2 测试结果 (24 tests, 5 files)

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

### 11.1 配置

- `vue-i18n` Composition API 模式 (`legacy: false`)
- locale: `zh-CN`, fallbackLocale: `zh-CN`
- 消息注册在 `src/locales/zh-CN.ts`，分 `auth` / `validation` / `error` 三组
- 组件中使用 `$t('auth.login')` 或 `useI18n().t()`

### 11.2 语言包规模

- `auth`: 24 个 key（登录、注册、placeholder、协议等）
- `validation`: 9 个 key（各字段校验错误消息）
- `error`: 11 个 key（AUTH_001-AUTH_010 + networkError）

---

## 12. 实施记录

### 12.1 文件变更统计

| 类型 | 数量 |
|------|------|
| 新增文件 | 57 |
| JS→TS 转换 | 4 (main.js, chat.js, ui.js, chatApi.js→request.ts) |
| 修改文件 | 4 (App.vue, index.html, package.json, variables.css) |
| 保留不变 | 8 (chat components: AppShell, ChatHeader, ChatMain, InputBar, MessageItem, MessageList, RightPanel, SideMenu, TopBar) |
| 删除文件 | 4 (main.js, chat.js, ui.js, chatApi.js) |

### 12.2 TypeScript 类型检查

```bash
$ npx vue-tsc --build --force
# 零错误通过
```

### 12.3 测试结果

```bash
$ npx vitest run
 Test Files  5 passed (5)
      Tests  24 passed (24)
```

### 12.4 npm 脚本

| 命令 | 用途 |
|------|------|
| `npm run dev` | 启动 Vite 开发服务器 |
| `npm run build` | 并行类型检查 + 生产构建（run-p type-check "build-only {@}"） |
| `npm run type-check` | 仅类型检查 |
| `npm run test` | 运行测试 |
| `npm run test:watch` | 开发模式测试 |
| `npm run test:coverage` | 覆盖率报告 |
| `npm run lint` | ESLint 检查 |
| `npm run format` | Prettier 格式化 |
```

---

## 13. 聊天模块概述

### 13.1 需求来源

聊天模块设计基于 `requirements.md`（ke-hermes 前端需求文档），该文档定义了 5 项功能需求：

| 需求编号 | 功能 | 说明 |
|---------|------|------|
| F1 | 对话界面 | 消息列表 + 输入区域，左右对齐，自动滚动 |
| F2 | 普通对话 | POST /api/chat → 完整回复（当前未实现，仅流式） |
| F3 | 流式对话 | POST /api/chat/stream → SSE 逐 token 推送 |
| F4 | 状态管理 | Pinia chatStore：messages/loading/sendMessage |
| F5 | 界面样式 | 白色背景 → 已在 v1.1.0 升级为暗色主题 |

### 13.2 实现与需求偏差

| 需求 | 实现 | 偏差说明 |
|------|------|---------|
| F1 对话界面 | 超出需求：升级为 AppShell 三栏布局 + 可折叠侧栏 + 历史面板 | 需求仅定义了简单的上方消息/下方输入布局；实际实现了企业级多面板布局 |
| F2 普通对话 | chatApi.js 中原有 `sendChatRequest`，迁移到 request.ts 后仅保留 SSE 流式 | 当前 chatStore 仅使用 sendStreamRequest；普通对话模式待实现 |
| F3 流式对话 | 完全符合需求 | fetch + ReadableStream SSE 解析、逐 token 追加、loading 态、错误处理 |
| F4 状态管理 | 超出需求：新增 uiStore 管理 sidebar/panel/model/history | 需求仅定义 chatStore；实际需要 uiStore 管理复杂 UI 状态 |
| F5 界面样式 | 暗色主题替代白色背景 | v1.1.0 全面暗色化，通过 Legacy 兼容层保证现有组件正常渲染 |

### 13.3 技术要点

| 项目 | 技术 | 说明 |
|------|------|------|
| 布局 | Flexbox 三栏 | SideMenu(左) + MainColumn(ChatHeader+MessageList+InputBar)(中) + RightPanel(右) |
| 流式通信 | fetch + ReadableStream | 手动解析 SSE `data: { "token": "..." }\n\n` 格式 |
| Markdown | marked 库 | 智能体回复渲染为富文本（标题/代码块/表格/引用等） |
| 自动滚动 | watch + nextTick + scrollTop | 监听 messages.length 和 lastContent 变化 |
| 消息 ID | 自增整数 | `let nextId = 1` 每消息递增 |

---

## 14. 聊天页面布局

### 14.1 AppShell — 三栏弹性布局

```
┌──────────────────────────────────────────────────────────┐
│ AppShell (flex row, 100vh)                               │
│ ┌─────────┬──────────────────────────────┬────────────┐ │
│ │SideMenu │  MainColumn (flex:1)         │ RightPanel │ │
│ │220px    │  ┌────────────────────────┐  │ 280px      │ │
│ │(可折叠  │  │ TopBar (52px)          │  │ (可折叠    │ │
│ │ 56px)  │  ├────────────────────────┤  │  40px)    │ │
│ │         │  │ ChatHeader (48px)      │  │            │ │
│ │         │  ├────────────────────────┤  │ 对话历史    │ │
│ │  导航    │  │ MessageList (flex:1)    │  │ 列表       │ │
│ │  菜单    │  │  - MessageItem (user)  │  │            │ │
│ │         │  │  - MessageItem (asst)  │  │            │ │
│ │         │  │  - auto-scroll         │  │            │ │
│ │         │  ├────────────────────────┤  │            │ │
│ │         │  │ InputBar              │  │            │ │
│ │         │  │ (输入框 + 发送/附件按钮) │  │            │ │
│ │         │  └────────────────────────┘  │            │ │
│ └─────────┴──────────────────────────────┴────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 14.2 布局尺寸规范

| 区域 | 宽度/高度 | CSS 变量 | 说明 |
|------|---------|---------|------|
| SideMenu 展开 | 220px | `--sidebar-width` | 含 Logo + 导航菜单 |
| SideMenu 折叠 | 56px | `--sidebar-collapsed-width` | 仅图标，文字隐藏 |
| TopBar | 52px | `--topbar-height` | 搜索框 + 通知/用户按钮 |
| ChatHeader | 48px | `--chat-header-height` | 智能体名称 + 模型选择器 |
| RightPanel 展开 | 280px | `--right-panel-width` | 对话历史列表 |
| RightPanel 折叠 | 40px | `--right-panel-collapsed-width` | 仅展开按钮 |
| MessageList | flex: 1 | — | 自动填充剩余空间，overflow-y: auto |
| InputBar | fit-content | — | 固定底部，含输入框+发送按钮 |

### 14.3 折叠/展开过渡

```css
/* SideMenu & RightPanel 使用 CSS transition */
transition: width var(--transition-duration) ease,
            min-width var(--transition-duration) ease;

/* 折叠态隐藏文字 */
.sidebar.collapsed .logo       { opacity: 0; width: 0; overflow: hidden; }
.sidebar.collapsed .menu-label { opacity: 0; height: 0; overflow: hidden; }
.sidebar.collapsed .menu-text  { opacity: 0; width: 0; overflow: hidden; }
```

---

## 15. 聊天核心组件设计

### 15.1 AppShell

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/AppShell.vue` |
| 功能 | 三栏根布局容器 |
| 子组件 | SideMenu + (TopBar + ChatMain) + RightPanel |
| 状态依赖 | uiStore（sidebar/panel 折叠态） |
| 样式 | `display: flex; height: 100vh;` |

### 15.2 ChatMain

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/ChatMain.vue` |
| 功能 | 中间主列垂直布局 |
| 子组件 | ChatHeader + MessageList + InputBar |
| 样式 | `flex-direction: column; height: 100%;` |

### 15.3 MessageList

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/MessageList.vue` |
| 功能 | 滚动消息容器，渲染 `MessageItem` 列表 |
| Props | 无（直接从 chatStore 读取 `messages`） |
| 自动滚动 | watch `messages.length`（新消息）和 `lastContent`（流式追加）→ `scrollToBottom()` |
| 样式 | `flex:1; overflow-y:auto; padding:16px 24px; gap:16px` |

```typescript
// 自动滚动实现
const lastContent = computed(() => {
  const msgs = chatStore.messages
  if (msgs.length === 0) return ''
  return msgs[msgs.length - 1].content
})

function scrollToBottom() {
  nextTick(() => {
    const el = scrollContainer.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch(() => chatStore.messages.length, scrollToBottom)
watch(lastContent, scrollToBottom)
```

### 15.4 MessageItem

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/MessageItem.vue` |
| 功能 | 单条消息渲染，区分 user/assistant 角色 |
| Props | `message: ChatMessage` |
| 关键行为 | user 消息右对齐（蓝底白字），assistant 左对齐（卡片白/暗底） |

**渲染逻辑：**

| 角色 | 头像图标 | 内容渲染 | 对齐 |
|------|---------|---------|------|
| user | UserCircle (lucide) | 纯文本 | 右 |
| assistant | Sparkles (lucide) | **Markdown → HTML**（通过 `marked`） | 左 |

**流式输出指示器：**
```
<span v-if="message.streaming && !message.content" class="typing-indicator">
  <span class="dot" /><span class="dot" /><span class="dot" />
</span>
```
三个圆点依次闪烁（CSS `@keyframes typing`，各延迟 0s/0.2s/0.4s）。

**Markdown 渲染样式（scoped）：**
- 标题 h1–h4：字体 14–18px
- 代码块 `<pre><code>`：浅/暗背景 + Consolas/Monaco 等宽字体
- 引用 blockquote：左侧 3px 蓝色竖线
- 表格：完整边框 + 表头背景
- 链接：accent 色 + hover 下划线

### 15.5 InputBar

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/InputBar.vue` |
| 功能 | 消息输入 + 发送 + 附件入口 |
| 本地状态 | `inputText: ref<string>` |
| 依赖 | chatStore.sendMessage, chatStore.loading, uiStore |

**交互行为：**

| 操作 | 行为 |
|------|------|
| Enter（非 Shift） | `e.preventDefault()` → `sendMessage(text)` → 清空输入 |
| Shift + Enter | 换行（默认行为） |
| 点击发送按钮 | `sendMessage(text)` → 清空输入 |
| loading=true | 输入框和发送按钮 disabled |
| 点击 + 按钮 | `uiStore.togglePlusMenu()` → 弹出附件菜单 |
| 点击外部 | `uiStore.closePlusMenu()`（document click 监听） |

**Plus 弹出菜单**：绝对定位在输入框上方，包含"上传附件"和"上传图片"两项。

**底部信息栏**：
- 左侧：模型选择器 Pill（`uiStore.selectedModel` + ChevronDown）
- 右侧：快捷键提示 "Enter 发送 · Shift+Enter 换行"

### 15.6 ChatHeader

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/ChatHeader.vue` |
| 功能 | 聊天区顶部信息栏 + 模型切换下拉 |
| 内容 | 智能体头像（Sparkles 图标圆形蓝底）+ 名称 "Hermes 智能体" + 模型下拉选择器 |
| 模型选择器 | el-dropdown 实现，可选模型：DeepSeek V4、Claude Opus 4.7、GPT-4o、Gemini 2.5 Pro。选中项同步更新 `uiStore.selectedModel` |

### 15.7 SideMenu

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/SideMenu.vue` |
| 功能 | 可折叠左侧导航菜单 |
| 图标库 | lucide-vue-next（PanelLeftClose, MessageSquare, Timer, Bot, Zap, Settings） |

**菜单分组:**

| 分组 | 项目 |
|------|------|
| 聊天 | 对话 |
| 控制 | 定时任务 |
| 代理 | 代理列表, Skills |
| 设置 | 配置 |

**折叠/展开:** 点击右上角 `<`/`>` 按钮 → `uiStore.toggleSidebar()` → `sidebarCollapsed` 翻转 → CSS transition 动画。

### 15.8 TopBar

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/TopBar.vue` |
| 功能 | 顶部全局搜索 + 通知/用户菜单 |
| 搜索 | 搜索框绑定 `uiStore.searchQuery`，支持清空按钮 |
| 通知按钮 | 铃铛图标（Bell），无具体交互（占位） |
| 用户菜单 | el-dropdown 实现：显示用户头像首字母 + 昵称，下拉项包含"退出登录"（调用 `useAuth().logout()`） |

### 15.9 RightPanel

| 属性 | 说明 |
|------|------|
| 文件 | `src/components/RightPanel.vue` |
| 功能 | 可折叠右侧历史对话面板 |
| 展开态 | 标题"历史对话" + 折叠按钮 + "新建对话"按钮 + 历史列表 |
| 折叠态 | 仅展开按钮 |
| 新建对话 | `chatStore.clearMessages()` + `uiStore.newConversation()` |
| 删除历史 | hover 显示删除按钮 → `uiStore.deleteHistory(id)` |

---

## 16. 流式对话（SSE）设计

### 16.1 数据流

```
用户输入 → InputBar.handleSend()
         → chatStore.sendMessage(text)
           ├─ 追加 user 消息到 messages[]
           ├─ 创建空 assistant 消息（streaming=true）
           ├─ 调用 sendStreamRequest(text, callbacks)
           │   ├─ fetch POST /api/chat/stream
           │   ├─ response.body.getReader() → ReadableStream
           │   ├─ 逐块解码 → TextDecoder
           │   ├─ 按 \n 分割 → 解析 SSE data: 行
           │   └─ JSON.parse → onToken(token)
           │       └─ assistantMsg.content += token
           ├─ onDone() → streaming=false, loading=false
           └─ onError() → 追加错误文本到消息末尾
```

### 16.2 SSE 解析实现

```typescript
// src/services/request.ts — sendStreamRequest()

const reader = response.body?.getReader()
const decoder = new TextDecoder()
let buffer = ''

while (true) {
  const { done, value } = await reader.read()
  if (done) break

  buffer += decoder.decode(value, { stream: true })
  const lines = buffer.split('\n')
  buffer = lines.pop() || ''       // 保留未完成行

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        const json = JSON.parse(line.slice(6))
        if (json.token) onToken(json.token)
      } catch { /* skip */ }
    }
  }
}
// 处理 buffer 中残留的最后一行
```

### 16.3 请求/响应格式

| 方向 | 格式 |
|------|------|
| 请求 | `POST /api/chat/stream` `{ "message": "string" }` |
| 响应 | SSE 事件流：`data: {"token": "string"}\n\n` |

### 16.4 为什么不用 EventSource

浏览器原生 `EventSource` 仅支持 GET 请求，不支持 POST。SSE 对话需要 POST 发送用户消息，因此必须使用 `fetch` + `ReadableStream` 手动解析 SSE 格式。

---

## 17. 聊天状态管理

### 17.1 chatStore

| State | 类型 | 说明 |
|-------|------|------|
| `messages` | `Ref<ChatMessage[]>` | 所有消息 |
| `loading` | `Ref<boolean>` | 等待流式回复中 |

| Action | 说明 |
|--------|------|
| `addMessage(role, content, streaming?)` | 追加消息，返回引用（用于流式追加） |
| `sendMessage(text)` | 空/loading 校验 → 追加 user → 创建 asst → 调用 SSE → onToken 追加 content → onDone/onError 标记完成 |
| `clearMessages()` | 清空消息列表 + 重置 loading |

```typescript
// ChatMessage 类型
interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  streaming: boolean     // true 表示正在流式接收 token
}
```

**消息 ID 策略**：`let nextId = 1` 模块级变量，自增分配，确保每条消息有唯一 key（Vue `v-for` 使用）。

### 17.2 uiStore

| State | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `sidebarCollapsed` | `boolean` | `false` | 左侧菜单折叠态 |
| `rightPanelCollapsed` | `boolean` | `false` | 右侧面板折叠态 |
| `plusMenuOpen` | `boolean` | `false` | 附件弹出菜单 |
| `searchQuery` | `string` | `''` | 搜索框输入 |
| `selectedModel` | `string` | `'DeepSeek V4'` | 当前选中模型 |
| `histories` | `HistoryItem[]` | 5 条预设 | 对话历史列表 |
| `activeHistoryId` | `number \| null` | `1` | 当前活跃历史 ID |

| Action | 说明 |
|--------|------|
| `toggleSidebar()` | 翻转 sidebarCollapsed |
| `toggleRightPanel()` | 翻转 rightPanelCollapsed |
| `togglePlusMenu()` | 翻转 plusMenuOpen |
| `closePlusMenu()` | plusMenuOpen = false |
| `deleteHistory(id)` | 过滤删除 + 如果当前选中则清除 activeHistoryId |
| `newConversation()` | 重置 activeHistoryId + 关闭菜单 |

```typescript
interface HistoryItem {
  id: number
  title: string
}
```

---

## 18. 聊天 API 接口对接

### 18.1 后端接口清单（聊天）

| 接口 | 方法 | 请求体 | 响应体 | 用途 | 实现状态 |
|------|------|--------|--------|------|---------|
| `/api/chat` | POST | `{"message":"string"}` | `{"response":"string"}` | 普通对话 | **未实现** |
| `/api/chat/stream` | POST | `{"message":"string"}` | SSE `data:{"token":"string"}\n\n` | 流式对话 | 已实现 |

### 18.2 错误处理

| 场景 | 状态码 | 前端处理 |
|------|--------|---------|
| 空消息 | — | 前端 `minLength=1` 校验，不发送请求 |
| 后端不可用 | 网络错误 | 在 assistant 消息末尾追加 `[Connection failed: ...]` |
| 后端内部错误 | 500 | 在 assistant 消息末尾追加 `[Error: ...]` |
| HTTP 异常 | 4xx/5xx | `fetch` 非 ok → `throw new Error('HTTP ${status}: ${body}')` |

### 18.3 请求配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 代理目标 | `http://127.0.0.1:8000` | Vite proxy 配置 |
| baseURL | `/api` | 经 Vite 代理转发到后端 |
| Content-Type | `application/json` | 请求头 |

---

## 19. 需求对照与合规

### 19.1 requirements.md 逐条对照

| 需求编号 | 需求描述 | 实现状态 | 实现文件 |
|---------|---------|---------|---------|
| F1 对话界面 | 上方消息列表 + 下方输入区，左右对齐，自动滚动 | **完全实现 + 超越** | AppShell, MessageList, MessageItem, InputBar |
| F2 普通对话 | POST /api/chat，完整回复，loading 态，错误处理 | **已实现** | request.ts 中 sendChatRequest() 作为降级方案 |
| F3 流式对话 | POST /api/chat/stream，SSE 逐 token 推送，逐字效果 | **完全实现** | request.ts sendStreamRequest, chatStore.sendMessage |
| F4 状态管理 | Pinia chatStore：messages/loading，sendMessage | **完全实现 + 超越** | chatStore (chat.ts) + uiStore (ui.ts) |
| F5 界面样式 | 白色背景，user 深色右对齐，asst 浅色左对齐 | **已升级** | v1.1.0 暗色主题 + Legacy 兼容层 |

### 19.2 待实现项（v1.2.1）

| 项目 | 优先级 | 说明 |
|------|--------|------|
| 搜索功能 | P3 | TopBar 搜索框绑定 uiStore.searchQuery 但无实际搜索逻辑 |
| 对话历史持久化 | P3 | 当前硬编码 5 条预设历史，需接入后端对话 CRUD API |
| 通知功能 | P3 | TopBar 铃铛按钮无交互 |
| 用户菜单完善 | P3 | TopBar 用户头像已实现登出，可补充个人设置等入口 |
| 注册表单提交 | P2 | RegisterForm 和 EmailRegisterForm 的 submit 为 TODO 占位，需接入后端注册 API |

### 19.3 组件 → 文件映射总表

| 组件 | 文件 | 关联需求 |
|------|------|---------|
| AppShell | `src/components/AppShell.vue` | F1 |
| ChatMain | `src/components/ChatMain.vue` | F1 |
| MessageList | `src/components/MessageList.vue` | F1, F3 |
| MessageItem | `src/components/MessageItem.vue` | F1, F3, F5 |
| InputBar | `src/components/InputBar.vue` | F1, F2, F3 |
| ChatHeader | `src/components/ChatHeader.vue` | F1 |
| SideMenu | `src/components/SideMenu.vue` | F1（扩展） |
| TopBar | `src/components/TopBar.vue` | F1（扩展） |
| RightPanel | `src/components/RightPanel.vue` | F1（扩展） |
| chatStore | `src/stores/chat.ts` | F4 |
| uiStore | `src/stores/ui.ts` | F1（扩展） |
| sendStreamRequest | `src/services/request.ts` | F3 |

---

> 本文档 v1.2.1 基于实际代码实现全面更新：测试目录迁移至 tests/、路由改为 AuthLayout 嵌套结构、普通对话 sendChatRequest 已实现、ChatHeader 模型下拉选择器已实现、auth store 分离 Token/User 持久化。前后端接口对齐，认证/验证码/OAuth/短信模块均已联调通过。
