# Ke-Hermes 详细设计说明书 — 登录模块（桌面版）v1.0.0

| 版本    | 日期         | 作者  | 变更说明               |
| ----- | ---------- | --- | ------------------ |
| 1.0.0 | 2026-05-18 | -   | 登录模块详细设计初版，基于需求说明书 v1.1.0 |


---

## 目录

1. [概述](#1-概述)
2. [项目架构](#2-项目架构)
3. [路由设计](#3-路由设计)
4. [组件设计](#4-组件设计)
5. [状态管理设计](#5-状态管理设计)
6. [类型定义](#6-类型定义)
7. [API 服务层设计](#7-api-服务层设计)
8. [样式系统设计](#8-样式系统设计)
9. [安全设计](#9-安全设计)
10. [测试设计](#10-测试设计)
11. [国际化设计](#11-国际化设计)
12. [性能优化设计](#12-性能优化设计)
13. [附录](#13-附录)

---

## 1. 概述

### 1.1 文档目的

本文档为 Ke-Hermes 登录模块（桌面版）的详细设计说明书，基于《Ke-Hermes 需求说明书-登录模块（桌面版）-1.1.0》编写。文档定义了登录模块的技术架构、组件结构、数据流、接口契约和实现规范，供前端开发人员编码实现。

### 1.2 技术选型

| 类别       | 选型                   | 版本     |
| -------- | -------------------- | ------ |
| 框架       | Vue 3                | ^3.5   |
| 类型系统     | TypeScript           | ^5.5   |
| 路由       | Vue Router           | ^4.4   |
| 状态管理     | Pinia                | ^2.2   |
| 构建工具     | Vite                 | ^5.4   |
| 测试框架     | Vitest               | ^2.1   |
| 单元测试工具   | @vue/test-utils      | ^2.4   |
| 组件测试环境   | jsdom                | ^24.0  |
| UI 组件库   | Element Plus         | ^2.8   |
| HTTP 客户端 | Axios                | ^1.7   |
| CSS 方案   | SCSS + CSS Variables | -      |
| 加密       | JSEncrypt            | ^3.3   |
| 国际化      | vue-i18n             | ^9.14  |
| 代码格式化   | Prettier             | ^3.3   |
| 代码检查    | ESLint               | ^9.0   |
| 图标       | lucide-vue-next      | ^0.400 |

### 1.3 适用范围

- PC Web 端登录页面、注册页面
- OAuth 回调处理页面
- 路由守卫、Token 刷新、权限校验等通用逻辑

### 1.4 相关文档

- [Ke-Hermes 需求说明书-登录模块（桌面版）-1.1.0](./Ke%20Hermes%20需求说明书-登录模块（桌面版）-1.1.0.md)

---

## 2. 项目架构

### 2.1 create-vue 脚手架初始化

项目使用 Vue 官方 `create-vue` 脚手架初始化，初始化时启用以下特性：

```bash
npm create vue@latest ke-hermes-frontend -- \
  --typescript \
  --jsx \
  --router \
  --pinia \
  --vitest \
  --e2e none \
  --eslint \
  --prettier
```

### 2.2 目录结构

```
frontend/
├── .vscode/
│   └── extensions.json            # VS Code 推荐插件
├── index.html                     # 入口 HTML（lang="zh-CN"）
├── package.json                   # 依赖与脚本
├── tsconfig.json                  # TypeScript 项目配置
├── tsconfig.app.json              # 应用代码 TS 配置
├── tsconfig.node.json             # 构建工具 TS 配置
├── tsconfig.vitest.json           # 测试 TS 配置
├── vite.config.ts                 # Vite 构建配置
├── vitest.config.ts               # Vitest 测试配置
├── env.d.ts                       # 环境变量类型声明
├── eslint.config.ts               # ESLint 扁平配置
├── .prettierrc.json               # Prettier 格式化配置
├── .env                           # 默认环境变量
├── .env.development               # 开发环境变量
├── .env.production                # 生产环境变量
│
├── public/
│   └── favicon.ico                # 网站图标
│
├── src/
│   ├── main.ts                    # 应用入口：createApp + 插件注册
│   ├── App.vue                    # 根组件（仅 <RouterView />）
│   │
│   ├── router/
│   │   └── index.ts               # Vue Router 配置 + 路由守卫
│   │
│   ├── stores/
│   │   ├── auth.ts                # 认证状态管理（Token、用户信息、登录状态）
│   │   └── captcha.ts             # 验证码状态管理（图形验证码、短信倒计时）
│   │
│   ├── types/
│   │   ├── auth.ts                # 认证相关类型（登录表单、注册表单、Token）
│   │   ├── api.ts                 # API 通用类型（请求/响应包装、分页、错误码）
│   │   ├── captcha.ts             # 验证码类型（图形验证码、短信验证码）
│   │   └── components.ts          # 组件 Props/Emits/Slots 类型
│   │
│   ├── services/
│   │   ├── request.ts             # Axios 实例封装（拦截器、Token 刷新、错误处理）
│   │   ├── authApi.ts             # 认证 API（登录、注册、退出、Token 刷新）
│   │   ├── captchaApi.ts          # 验证码 API（获取图形验证码、发送短信）
│   │   └── oauthApi.ts            # 第三方登录 API（OAuth 跳转、回调）
│   │
│   ├── composables/
│   │   ├── useAuth.ts             # 认证组合式函数（登录逻辑封装）
│   │   ├── usePasswordEncrypt.ts  # 密码 RSA 加密组合式函数
│   │   ├── useCountdown.ts        # 倒计时组合式函数
│   │   ├── useCaptcha.ts          # 图形验证码组合式函数
│   │   └── useAgreement.ts        # 用户协议组合式函数
│   │
│   ├── components/
│   │   ├── auth/
│   │   │   ├── AuthLayout.vue     # 认证页布局（左品牌区 + 右表单区）
│   │   │   ├── BrandPanel.vue     # 左侧品牌展示面板
│   │   │   ├── LoginCard.vue      # 登录卡片容器
│   │   │   ├── LoginTabs.vue      # 登录方式切换标签（账号/手机号）
│   │   │   ├── AccountLoginForm.vue    # 账号密码登录表单
│   │   │   ├── PhoneLoginForm.vue      # 手机短信验证码登录表单
│   │   │   ├── RegisterForm.vue        # 注册表单
│   │   │   ├── EmailRegisterForm.vue   # 邮箱注册表单
│   │   │   ├── AgreementCheckbox.vue   # 用户协议勾选框
│   │   │   ├── OAuthPanel.vue          # 第三方登录图标面板
│   │   │   ├── RegisterLink.vue        # 注册入口链接
│   │   │   └── FeatureGrid.vue         # 品牌区特性网格
│   │   ├── common/
│   │   │   ├── PasswordInput.vue       # 密码输入框（含显示/隐藏切换）
│   │   │   ├── CountdownButton.vue     # 倒计时发送按钮
│   │   │   └── FormError.vue           # 表单错误提示
│   │   └── captcha/
│   │       ├── CaptchaModal.vue        # 验证码弹窗容器
│   │       ├── SlidePuzzle.vue         # 滑动拼图验证码
│   │       └── ImageCaptcha.vue        # 图形验证码（降级方案）
│   │
│   ├── views/
│   │   ├── LoginView.vue          # 登录页面视图
│   │   ├── RegisterView.vue       # 注册页面视图
│   │   ├── EmailRegisterView.vue  # 邮箱注册页面视图
│   │   └── OAuthCallbackView.vue  # OAuth 回调处理视图
│   │
│   ├── assets/
│   │   ├── styles/
│   │   │   ├── variables.css      # CSS 自定义属性（设计 Token）
│   │   │   ├── reset.css          # 全局重置样式
│   │   │   ├── fonts.css          # 字体定义（Inter、Noto Sans SC）
│   │   │   └── mixins.scss        # SCSS Mixins（响应式断点、暗色主题）
│   │   ├── images/
│   │   │   └── logo.svg           # Ke-Hermes Logo SVG
│   │   └── icons/                 # 自定义图标资源
│   │
│   └── locales/
│       ├── index.ts               # vue-i18n 配置入口
│       └── zh-CN.ts               # 简体中文语言包
│
└── src/__tests__/
    ├── setup.ts                   # 测试全局配置（Mock、插件注册）
    ├── components/                # 组件单元测试
    ├── stores/                    # Pinia Store 单元测试
    ├── services/                  # API 服务 Mock 测试
    └── composables/               # 组合式函数单元测试
```

### 2.3 模块分层

```
┌─────────────────────────────────────────────────────────┐
│  Views 层（页面视图）                                       │
│  LoginView / RegisterView / OAuthCallbackView           │
├─────────────────────────────────────────────────────────┤
│  Components 层（业务组件）                                  │
│  AuthLayout / LoginCard / AccountLoginForm /            │
│  CaptchaModal / OAuthPanel / ...                        │
├─────────────────────────────────────────────────────────┤
│  Composables 层（逻辑复用）                                 │
│  useAuth / useCaptcha / useCountdown / ...              │
├─────────────────────────────────────────────────────────┤
│  Stores 层（全局状态）                                      │
│  authStore / captchaStore                               │
├─────────────────────────────────────────────────────────┤
│  Services 层（API 通信）                                   │
│  authApi / captchaApi / oauthApi / request              │
├─────────────────────────────────────────────────────────┤
│  Types 层（类型定义）                                       │
│  auth.ts / api.ts / captcha.ts / components.ts          │
└─────────────────────────────────────────────────────────┘
```

依赖方向：上层依赖下层，下层不感知上层。Services 层和 Stores 层为并列关系，通过 Composables 层协调调用。

---

## 3. 路由设计

### 3.1 路由表

```typescript
// src/router/index.ts

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    component: () => import('@/components/auth/AuthLayout.vue'),
    children: [
      {
        path: '',
        name: 'login',
        component: () => import('@/views/LoginView.vue'),
        meta: { title: '登录', guest: true },
      },
    ],
  },
  {
    path: '/register',
    component: () => import('@/components/auth/AuthLayout.vue'),
    children: [
      {
        path: '',
        name: 'register',
        component: () => import('@/views/RegisterView.vue'),
        meta: { title: '注册', guest: true },
      },
      {
        path: 'email',
        name: 'register-email',
        component: () => import('@/views/EmailRegisterView.vue'),
        meta: { title: '邮箱注册', guest: true },
      },
    ],
  },
  {
    path: '/oauth/callback',
    name: 'oauth-callback',
    component: () => import('@/views/OAuthCallbackView.vue'),
    meta: { title: '第三方登录', guest: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
]
```

### 3.2 路由守卫

```typescript
// 全局前置守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 需要认证的页面 → 未登录则重定向至 /login
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  // 仅允许未登录用户访问的页面 → 已登录则重定向至首页
  if (to.meta.guest && authStore.isAuthenticated) {
    return next({ name: 'home' })
  }

  next()
})
```

### 3.3 路由 Meta 类型扩展

```typescript
// src/types/router.d.ts
import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    guest?: boolean
  }
}
```

### 3.4 登录成功回跳

登录成功后，读取 URL query 参数 `redirect`，跳转到目标页面；若无该参数则跳转 `/`：

```typescript
// 在登录成功回调中
const redirect = route.query.redirect as string | undefined
router.push(redirect || '/')
```

---

## 4. 组件设计

### 4.1 组件树

```
App.vue
└── <RouterView />
    ├── AuthLayout.vue                         [认证页根布局]
    │   ├── BrandPanel.vue                     [左侧品牌区 — 40%宽度]
    │   │   ├── <Logo />                       [Logo 96×96]
    │   │   ├── <h1> Ke-Hermes </h1>           [系统名称 36px]
    │   │   ├── <p> 自我进化，越用越强 </p>        [定位文案 20px]
    │   │   ├── FeatureGrid.vue                [2×4 特性网格]
    │   │   │   └── FeatureItem.vue ×8         [单特性行: 图标 + 标题 + 描述]
    │   │   └── <footer> 版权信息 </footer>      [底部版权]
    │   └── <RouterView />                     [右侧表单区 — 60%宽度]
    │       ├── LoginView.vue                  [登录页]
    │       │   └── LoginCard.vue              [登录卡片容器 — 520px]
    │       │       ├── LoginTabs.vue          [账号登录 / 手机登录]
    │       │       ├── AccountLoginForm.vue    [账号密码表单]
    │       │       │   ├── <el-input />        [账号输入框]
    │       │       │   ├── PasswordInput.vue   [密码输入框]
    │       │       │   └── <RememberMe+Forgot> [记住我 + 忘记密码]
    │       │       ├── PhoneLoginForm.vue      [手机号表单]
    │       │       │   ├── <el-input />        [手机号输入框]
    │       │       │   └── CountdownButton.vue [获取验证码 + 倒计时]
    │       │       ├── AgreementCheckbox.vue  [协议勾选区]
    │       │       ├── <el-button />           [登录按钮 52px]
    │       │       ├── OAuthPanel.vue         [第三方登录面板]
    │       │       │   └── OAuthIcon.vue ×5   [52×52 圆形图标按钮]
    │       │       └── RegisterLink.vue        [注册入口链接]
    │       │
    │       └── RegisterView.vue / EmailRegisterView.vue  [注册页]
    │
    └── CaptchaModal.vue                       [验证码弹窗 — Teleport 到 body]
        ├── SlidePuzzle.vue                    [滑动拼图验证码]
        └── ImageCaptcha.vue                   [图形验证码 — 降级]
```

### 4.2 核心组件规格

#### 4.2.1 AuthLayout

| 属性     | 说明                        |
| ------ | ------------------------- |
| 功能     | 认证页面根布局，提供左右分栏的插槽结构       |
| Props  | 无                         |
| 左侧内容  | `<BrandPanel />`           |
| 右侧内容  | `<RouterView />` 嵌套路由出口    |
| 响应式断点 | >=1024px: 4:6, 768-1023: 32:68, <768: 隐藏左侧 |

```vue
<!-- AuthLayout.vue 结构 -->
<template>
  <div class="auth-layout">
    <aside class="auth-layout__brand">
      <BrandPanel />
    </aside>
    <main class="auth-layout__form">
      <RouterView />
    </main>
  </div>
</template>
```

#### 4.2.2 AccountLoginForm

| 属性         | 说明                         |
| ---------- | -------------------------- |
| 功能         | 账号密码登录表单                   |
| 内部状态       | `form: { account, password, rememberMe }` |
| 校验规则       | 账号 2-64 字符；密码 6-12 字符至少字母+数字 |
| 交互         | 输入框聚焦边框变主蓝色；Enter 键触发登录    |
| 错误展示       | 输入框下方红色文字（el-input error 插槽）  |
| 密码加密       | 提交前通过 `usePasswordEncrypt` 加密 |

```typescript
// 表单数据接口
interface AccountLoginFormData {
  account: string
  password: string
  rememberMe: boolean
}

// 组件 Emits
interface AccountLoginFormEmits {
  (e: 'submit', payload: AccountLoginFormData): void
  (e: 'forgot-password'): void
}
```

#### 4.2.3 PhoneLoginForm

| 属性       | 说明                                 |
| -------- | ---------------------------------- |
| 功能       | 手机短信验证码登录表单                        |
| 内部状态     | `form: { phone, smsCode }`, `countdown: number` |
| 短信发送流程   | 输入手机号 → 点击「获取验证码」→ 弹出 `CaptchaModal` → 校验通过 → 发送短信 |
| 倒计时      | 60 秒，通过 `useCountdown` 管理             |
| 手机号掩码    | 输入时自动插入空格分隔（如 `138 0000 0000`）        |

#### 4.2.4 CaptchaModal

| 属性      | 说明                               |
| ------- | -------------------------------- |
| 功能      | 验证码弹窗，作为所有图形验证码流程的宿主             |
| Props   | `modelValue: boolean` (v-model)   |
| 子组件    | `SlidePuzzle` (优先) / `ImageCaptcha` (降级) |
| Teleport | 渲染到 `document.body`              |
| 背景遮罩    | `rgba(0,0,0,0.6)`，半透明深色遮罩        |

```typescript
interface CaptchaModalProps {
  modelValue: boolean          // 控制显示/隐藏
  type: 'slide' | 'image'     // 验证码类型
}

interface CaptchaModalEmits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', payload: CaptchaResult): void
  (e: 'fail'): void
}
```

#### 4.2.5 SlidePuzzle

| 属性          | 说明                  |
| ----------- | ------------------- |
| 功能          | 滑动拼图验证码组件           |
| 交互          | 鼠标拖拽滑块完成拼图，采集滑动轨迹   |
| 校验          | 轨迹上报后端校验，返回成功/失败    |
| 失败处理        | 自动刷新拼图，提示用户重试       |
| 内部状态        | `status: 'idle' | 'dragging' | 'verifying' | 'success' | 'fail'` |

#### 4.2.6 AgreementCheckbox

| 属性      | 说明                          |
| ------- | --------------------------- |
| 功能      | 协议勾选区（checkbox + 协议链接）       |
| 内部状态    | `checked: boolean`           |
| 协议弹窗    | 点击协议名弹出全文 Modal，含「同意」「不同意」按钮 |
| 未勾选拦截提示 | 红色边框闪烁 + 文字高亮，2 秒后恢复       |

#### 4.2.7 OAuthPanel

| 属性   | 说明                        |
| ---- | ------------------------- |
| 功能   | 第三方登录图标面板                 |
| 平台列表 | 微信、支付宝、飞书、钉钉、企业微信（按此顺序排列） |
| 图标规格 | 52×52px 圆形，纯色品牌底色 + 白色文字   |
| 交互   | 点击弹出二维码扫码弹窗（统一 Modal）     |
| hover | 图标上浮 2px + 阴影加深            |

#### 4.2.8 FeatureGrid

| 属性       | 说明                        |
| -------- | ------------------------- |
| 功能       | 品牌区 2×4 特性网格              |
| 数据       | `features: FeatureItem[]`  |
| 布局       | 2 列 × 4 行，水平排列（图标左 + 文字右） |
| 图标规格     | 40×40px，lucide icons      |
| 标题       | 18px / 700                |
| 描述       | 15px                      |
| 行间距      | 24px                      |
| 列间距      | 32px                      |
| 图标文字间距   | 14px                      |

```typescript
interface FeatureItem {
  icon: string          // lucide 图标名称
  title: string         // 标题
  description: string   // 描述
}
```

#### 4.2.9 PasswordInput

| 属性          | 说明                    |
| ----------- | --------------------- |
| 功能          | 密码输入框，含显示/隐藏密码切换按钮    |
| Props       | `modelValue: string`  |
| 切换按钮        | 右侧眼睛图标（Eye / EyeOff）  |
| 禁止粘贴（可配置）   | 通过环境变量 `VITE_ALLOW_PASTE_PASSWORD` 控制 |

---

## 5. 状态管理设计

### 5.1 authStore

```typescript
// src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo, AuthTokens } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // ---- State ----
  const tokens = ref<AuthTokens | null>(null)
  const user = ref<UserInfo | null>(null)
  const loginLoading = ref(false)
  const loginError = ref<string | null>(null)
  const agreedProtocolVersion = ref<string | null>(null)

  // ---- Getters ----
  const isAuthenticated = computed(() => !!tokens.value?.accessToken)
  const accessToken = computed(() => tokens.value?.accessToken ?? '')
  const refreshToken = computed(() => tokens.value?.refreshToken ?? '')

  // ---- Actions ----
  async function loginWithPassword(payload: { account: string; password: string; rememberMe: boolean }): Promise<void>
  async function loginWithPhone(payload: { phone: string; smsCode: string }): Promise<void>
  async function logout(): Promise<void>
  async function refreshAccessToken(): Promise<string>
  function setTokens(t: AuthTokens): void
  function clearTokens(): void
  function agreeProtocol(version: string): void

  return { tokens, user, loginLoading, loginError, agreedProtocolVersion,
           isAuthenticated, accessToken, refreshToken,
           loginWithPassword, loginWithPhone, logout, refreshAccessToken,
           setTokens, clearTokens, agreeProtocol }
})
```

**Token 刷新逻辑（去重锁机制）：**

```typescript
let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    try {
      const res = await authApi.refreshToken(refreshToken.value)
      setTokens(res.data)
      return res.data.accessToken
    } catch {
      clearTokens()
      throw new Error('refresh-failed')
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}
```

**token 持久化策略：**

- `rememberMe = true`: localStorage 存储 token（7 天）
- `rememberMe = false`: sessionStorage 存储 token（关闭标签页即失效）
- `pinia-plugin-persistedstate` 同步 token 到对应存储

### 5.2 captchaStore

```typescript
// src/stores/captcha.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCaptchaStore = defineStore('captcha', () => {
  // ---- State ----
  const modalVisible = ref(false)
  const captchaType = ref<'slide' | 'image'>('slide')

  /** 待处理操作：验证码通过后需继续执行的意图 */
  const pendingAction = ref<PendingAction | null>(null)

  const smsCountdown = ref(0)          // 短信发送倒计时（秒）
  const smsErrorCount = ref(0)         // 短信验证码错误计数
  const dailySmsCount = ref(0)         // 当日已发送短信次数

  // ---- Getters ----
  const canSendSms = computed(() => smsCountdown.value === 0 && dailySmsCount.value < 5)

  // ---- Actions ----
  function showCaptcha(action: PendingAction): void
  function hideCaptcha(): void
  function onCaptchaSuccess(payload: CaptchaResult): void
  function startSmsCountdown(): void
  function resetSmsCount(): void

  return { modalVisible, captchaType, pendingAction, smsCountdown,
           smsErrorCount, dailySmsCount, canSendSms,
           showCaptcha, hideCaptcha, onCaptchaSuccess,
           startSmsCountdown, resetSmsCount }
})

interface PendingAction {
  type: 'send-sms' | 'login'
  payload?: unknown
}

interface CaptchaResult {
  ticket: string    // 验证通过票据
  randstr: string   // 随机字符串
}
```

### 5.3 Store 间通信

- `captchaStore` 通过 `pendingAction` 记录用户意图，验证通过后根据 `type` 调用对应的 `authStore` Action 或短信发送 API
- 登录/注册成功后 `authStore` 重置 `captchaStore` 状态
- 组件层不直接协调多 Store 间的复杂逻辑，统一由 Composables 层封装

---

## 6. 类型定义

### 6.1 认证类型

```typescript
// src/types/auth.ts

/** 认证 Token */
export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresIn: number           // Access Token 有效期（秒），默认 7200
}

/** 用户基本信息 */
export interface UserInfo {
  id: string
  nickname: string
  avatar: string              // 头像 URL
  phone: string
  email: string
  workspaceId: string
}

/** 账号密码登录请求 */
export interface AccountLoginRequest {
  account: string
  password: string             // RSA 加密后的密码
  captchaTicket?: string       // 失败 3 次后需要图形验证码票据
  captchaRandstr?: string
}

/** 手机号登录请求 */
export interface PhoneLoginRequest {
  phone: string
  smsCode: string
}

/** 注册请求 */
export interface RegisterRequest {
  phone: string
  smsCode: string
  nickname: string
  password: string             // RSA 加密后的密码
  agreedProtocolVersion: string
}

/** 邮箱注册请求 */
export interface EmailRegisterRequest {
  email: string
  emailCode: string
  nickname: string
  password: string             // RSA 加密后的密码
  agreedProtocolVersion: string
}

/** 登录/注册响应 */
export interface AuthResponse {
  tokens: AuthTokens
  user: UserInfo
  needProtocolAgreement?: string  // 需重新同意的协议版本号
}

/** 登录失败计数 */
export interface LoginFailInfo {
  failCount: number
  lockedUntil: number | null     // 锁定到期时间戳
}
```

### 6.2 API 通用类型

```typescript
// src/types/api.ts

/** 后端统一响应包装 */
export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
  requestId: string
  timestamp: number
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

/** 验证码发送请求 */
export interface SendSmsRequest {
  phone: string
  captchaTicket: string
  captchaRandstr: string
}
```

### 6.3 验证码类型

```typescript
// src/types/captcha.ts

export interface SlidePuzzleData {
  bgImage: string              // 背景图 Base64
  slideImage: string           // 滑块图 Base64
  y: number                    // 滑块 y 坐标
}

export interface SlideVerifyRequest {
  distance: number             // 滑块移动距离（px）
  track: number[]              // 轨迹数组（鼠标/触摸移动坐标序列）
  ticket?: string
}

export interface SlideVerifyResponse {
  success: boolean
  ticket?: string
  randstr?: string
}
```

### 6.4 组件类型

```typescript
// src/types/components.ts

export interface LoginTabItem {
  key: 'account' | 'phone'
  label: string
}

export interface FeatureItem {
  icon: string                 // lucide 图标名称
  title: string
  description: string
}

export interface OAuthProvider {
  name: string
  icon: string
  bgColor: string              // 品牌底色
  textColor: string            // 文字色（通常白色）
  shadowColor: string          // 投影阴影色
}
```

---

## 7. API 服务层设计

### 7.1 Axios 实例封装

```typescript
// src/services/request.ts

import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosError } from 'axios'
import { useAuthStore } from '@/stores/auth'
import type { ApiResponse } from '@/types/api'

const instance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：注入 Access Token
instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const authStore = useAuthStore()
  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`
  }
  return config
})

// 响应拦截器：统一错误处理 + Token 自动刷新
instance.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse
    if (data.code !== 0) {
      return Promise.reject(new ApiError(data.code, data.message))
    }
    return response
  },
  async (error: AxiosError<ApiResponse>) => {
    if (error.response?.status === 401) {
      // Token 过期，尝试刷新
      try {
        const authStore = useAuthStore()
        const newToken = await authStore.refreshAccessToken()
        error.config!.headers.Authorization = `Bearer ${newToken}`
        return instance.request(error.config!)
      } catch {
        // 刷新失败，跳转登录
        authStore.clearTokens()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export class ApiError extends Error {
  constructor(public code: string, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export default instance
```

### 7.2 认证 API

```typescript
// src/services/authApi.ts

import request from './request'
import type { ApiResponse } from '@/types/api'
import type {
  AccountLoginRequest, PhoneLoginRequest, RegisterRequest,
  EmailRegisterRequest, AuthResponse
} from '@/types/auth'

export const authApi = {
  /** 账号密码登录 */
  accountLogin: (data: AccountLoginRequest) =>
    request.post<ApiResponse<AuthResponse>>('/api/auth/login/account', data),

  /** 手机号登录 */
  phoneLogin: (data: PhoneLoginRequest) =>
    request.post<ApiResponse<AuthResponse>>('/api/auth/login/phone', data),

  /** 手机号注册 */
  register: (data: RegisterRequest) =>
    request.post<ApiResponse<AuthResponse>>('/api/auth/register/phone', data),

  /** 邮箱注册 */
  emailRegister: (data: EmailRegisterRequest) =>
    request.post<ApiResponse<AuthResponse>>('/api/auth/register/email', data),

  /** 退出登录 */
  logout: () =>
    request.post<ApiResponse<null>>('/api/auth/logout'),

  /** 刷新 Token */
  refreshToken: (refreshToken: string) =>
    request.post<ApiResponse<AuthResponse>>('/api/auth/refresh', { refreshToken }),

  /** 获取登录失败次数 */
  getFailCount: (account: string) =>
    request.get<ApiResponse<{ failCount: number }>>('/api/auth/fail-count', { params: { account } }),
}
```

### 7.3 验证码 API

```typescript
// src/services/captchaApi.ts

import request from './request'
import type { ApiResponse } from '@/types/api'
import type { SendSmsRequest } from '@/types/api'
import type { SlidePuzzleData, SlideVerifyRequest, SlideVerifyResponse } from '@/types/captcha'

export const captchaApi = {
  /** 获取滑动拼图数据 */
  getSlidePuzzle: () =>
    request.get<ApiResponse<SlidePuzzleData>>('/api/captcha/slide'),

  /** 校验滑动拼图 */
  verifySlide: (data: SlideVerifyRequest) =>
    request.post<ApiResponse<SlideVerifyResponse>>('/api/captcha/slide/verify', data),

  /** 发送短信验证码 */
  sendSms: (data: SendSmsRequest) =>
    request.post<ApiResponse<null>>('/api/sms/send', data),

  /** 获取图形验证码（降级方案） */
  getImageCaptcha: () =>
    request.get<ApiResponse<{ image: string; key: string }>>('/api/captcha/image'),

  /** 校验图形验证码 */
  verifyImageCaptcha: (data: { key: string; code: string }) =>
    request.post<ApiResponse<{ success: boolean }>>('/api/captcha/image/verify', data),
}
```

### 7.4 接口路由清单

| 接口路径                      | 方法   | 说明        | 关联需求章节 |
| ------------------------- | ---- | --------- | ------ |
| `/api/auth/login/account` | POST | 账号密码登录    | 2.2    |
| `/api/auth/login/phone`   | POST | 手机验证码登录   | 2.3    |
| `/api/auth/register/phone` | POST | 手机号注册     | 3.2    |
| `/api/auth/register/email` | POST | 邮箱注册      | 3.3    |
| `/api/auth/logout`        | POST | 退出登录      | 4.4    |
| `/api/auth/refresh`       | POST | 刷新 Token  | 4.4    |
| `/api/auth/fail-count`    | GET  | 获取登录失败计数  | 2.2.3  |
| `/api/captcha/slide`      | GET  | 获取滑动拼图数据  | 2.4    |
| `/api/captcha/slide/verify` | POST | 校验滑动拼图    | 2.4    |
| `/api/captcha/image`      | GET  | 获取图形验证码   | 2.4    |
| `/api/captcha/image/verify` | POST | 校验图形验证码   | 2.4    |
| `/api/sms/send`           | POST | 发送短信验证码   | 2.3.2  |

---

## 8. 样式系统设计

### 8.1 CSS 变量（设计 Token）

```css
/* src/assets/styles/variables.css */

:root {
  /* === 品牌色系 === */
  --color-bg-page: #060b1a;
  --color-bg-form-area: #090e1f;
  --color-bg-card: rgba(13, 19, 41, 0.9);
  --color-bg-input: #0f172e;
  --color-bg-brand-start: #050a1f;
  --color-bg-brand-mid: #0a173d;
  --color-bg-brand-end: #050d29;

  --color-border-card: rgba(38, 51, 89, 0.4);
  --color-border-input: #1f293d;

  --color-accent: #3b82f6;
  --color-accent-dark: #2563eb;
  --color-accent-gradient: linear-gradient(90deg, #3b82f6, #2563eb);

  /* === 文字色阶 === */
  --color-text-primary: #f2f5fa;
  --color-text-secondary: #8794ad;
  --color-text-label: #c7d1e0;
  --color-text-muted: #596680;
  --color-text-error: #f04545;

  /* === 圆角 === */
  --radius-input: 10px;
  --radius-card: 16px;
  --radius-button: 10px;
  --radius-checkbox: 6px;
  --radius-oauth-icon: 26px;
  --radius-logo: 20px;

  /* === 尺寸 === */
  --size-input-height: 52px;
  --size-button-height: 52px;
  --size-card-max-width: 520px;
  --size-card-padding: 40px;
  --size-card-gap: 24px;
  --size-checkbox: 20px;
  --size-oauth-icon: 52px;
  --size-oauth-gap: 20px;
  --size-logo: 96px;
  --size-brand-padding-v: 40px;
  --size-brand-padding-h: 30px;
  --size-brand-block-gap: 40px;
  --size-feature-icon: 40px;
  --size-feature-row-gap: 24px;
  --size-feature-col-gap: 32px;
  --size-feature-icon-text-gap: 14px;
  --size-login-tab-indicator: 36px 3px;

  /* === 字号/字重 === */
  --font-size-system-name: 36px;
  --font-size-tagline: 20px;
  --font-size-feature-title: 18px;
  --font-size-feature-desc: 15px;
  --font-size-button: 19px;
  --font-size-input: 16px;
  --font-size-login-tab: 18px;
  --font-size-remember-forgot: 15px;
  --font-size-agreement: 14px;
  --font-size-oauth-label: 15px;
  --font-size-register-link: 15px;
  --font-size-copyright: 12px;
  --font-size-oauth-text: 17px;

  --font-weight-bold: 700;
  --font-weight-semibold: 600;
  --font-weight-normal: 400;

  /* === 字体族 === */
  --font-family-base: 'Inter', 'Noto Sans SC', system-ui, -apple-system, sans-serif;

  /* === 阴影 === */
  --shadow-card: 0px 8px 32px rgba(0, 0, 0, 0.4);
  --shadow-button: 0px 4px 16px rgba(59, 130, 246, 0.3);
  --shadow-logo: 0px 4px 20px rgba(59, 130, 246, 0.25);

  /* === 过渡 === */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 400ms ease;

  /* === 遮罩 === */
  --color-overlay: rgba(0, 0, 0, 0.6);
  --color-modal-bg: rgba(15, 23, 46, 0.98);

  /* === 导肮 === */
  --color-oauth-wechat: #07c160;
  --color-oauth-alipay: #1777f9;
  --color-oauth-feishu: #3370fa;
  --color-oauth-dingtalk: #0089f9;
  --color-oauth-wework: rgba(7, 193, 96, 0.85);
}
```

### 8.2 SCSS Mixins

```scss
// src/assets/styles/mixins.scss

// 响应式断点
$breakpoint-lg: 1024px;
$breakpoint-md: 768px;

@mixin respond-lg {
  @media (min-width: $breakpoint-lg) {
    @content;
  }
}

@mixin respond-md {
  @media (min-width: $breakpoint-md) and (max-width: $breakpoint-lg - 1px) {
    @content;
  }
}

@mixin respond-sm {
  @media (max-width: $breakpoint-md - 1px) {
    @content;
  }
}

// 卡片毛玻璃效果
@mixin glass-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-card);
  backdrop-filter: blur(8px);
  box-shadow: var(--shadow-card);
}

// 聚焦输入框样式
@mixin input-focus {
  &:focus-within {
    border-color: var(--color-accent);
    box-shadow: 0px 0px 0px 2px rgba(59, 130, 246, 0.15);
  }
}
```

### 8.3 组件样式组织

每个 Vue 组件使用 `<style scoped lang="scss">` 定义样式，遵循以下规则：

- 使用 CSS 变量（`var(--xxx)`）引用设计 Token，避免硬编码颜色
- 使用 SCSS 嵌套语法（`.parent { .child { ... } }`），嵌套深度不超过 3 层
- 使用 BEM 类名约定：`.block__element--modifier`
- 动画使用 CSS `transition` 或 `@keyframes`

---

## 9. 安全设计

### 9.1 密码加密

```typescript
// src/composables/usePasswordEncrypt.ts

import { ref } from 'vue'
import JSEncrypt from 'jsencrypt'

/** 使用 RSA 公钥加密密码 */
export function usePasswordEncrypt() {
  const publicKey = ref('')  // 从后端接口获取

  async function fetchPublicKey(): Promise<void> {
    if (publicKey.value) return
    const res = await authApi.getPublicKey()
    publicKey.value = res.data.data.publicKey
  }

  function encrypt(password: string): string {
    const jsEncrypt = new JSEncrypt()
    jsEncrypt.setPublicKey(publicKey.value)
    return jsEncrypt.encrypt(password) as string
  }

  return { publicKey, fetchPublicKey, encrypt }
}
```

密码加密流程：

```
用户输入密码
     ↓
提交前调用 fetchPublicKey() 获取 RSA 公钥
     ↓
使用 JSEncrypt 加密密码明文
     ↓
将加密后的密文作为请求参数发送
```

### 9.2 Token 管理

| 存储位置            | 条件           | 说明        |
| --------------- | ------------ | --------- |
| `localStorage`  | rememberMe   | 7 天内免登录自动续期 |
| `sessionStorage` | !rememberMe  | 关闭标签页即失效  |

实现方式：

```typescript
// src/stores/auth.ts 中的 token 持久化
function persistTokens(t: AuthTokens, rememberMe: boolean) {
  const storage = rememberMe ? localStorage : sessionStorage
  storage.setItem('auth_tokens', JSON.stringify(t))
}

function loadTokens(): AuthTokens | null {
  const raw = localStorage.getItem('auth_tokens')
            || sessionStorage.getItem('auth_tokens')
  return raw ? JSON.parse(raw) : null
}
```

### 9.3 请求安全

- 全站 HTTPS
- 所有 API 请求携带 `Authorization: Bearer <accessToken>` 头
- API 请求添加 XSRF-TOKEN 头（从 Cookie 读取）
- 敏感信息（密码、验证码）不通过 URL 参数传递，一律使用 POST Body
- 前端不存储明文密码

### 9.4 前端安全头部

在 `index.html` 中通过 `<meta>` 标签设置：

```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' https://api.ke-hermes.com">
```

部署时在 Nginx 配置严格的 HTTP 安全头：

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 9.5 登录限流（前端侧）

- 登录失败 3 次后，自动弹出图形验证码
- 短信发送按钮 60 秒倒计时
- 防止重复提交：按钮点击后添加 `loading` 状态，接口返回前禁用

---

## 10. 测试设计

### 10.1 测试策略

| 测试类型   | 工具               | 范围                   | 覆盖率目标 |
| ------ | ---------------- | -------------------- | ----- |
| 单元测试   | Vitest           | Composables、Stores、工具函数 | >= 80% |
| 组件测试   | Vitest + @vue/test-utils + jsdom | UI 组件                | >= 70% |
| API Mock | Vitest + msw     | API 服务层              | 关键路径  |

### 10.2 测试环境配置

```typescript
// vitest.config.ts
import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(viteConfig, defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/composables/**', 'src/stores/**', 'src/components/**'],
    },
  },
}))
```

### 10.3 关键测试用例

#### 10.3.1 authStore 测试

```
• loginWithPassword 成功后 tokens 和 user 正确设置
• loginWithPassword 失败后 loginError 包含错误信息
• refreshAccessToken 并发调用仅发起一次请求（去重锁）
• refreshAccessToken 失败后清除 tokens
• logout 清空所有状态并调用后端接口
• rememberMe=true 时 token 存入 localStorage
• rememberMe=false 时 token 存入 sessionStorage
```

#### 10.3.2 AccountLoginForm 测试

```
• 表单渲染：账号输入框、密码输入框、记住我复选框、登录按钮
• account 为空时提交 → 显示校验错误
• password 少于 6 位时提交 → 显示校验错误
• 有效输入提交 → emit submit 事件携带表单数据
• 登录按钮 loading 状态下不可重复点击
• Enter 键触发登录
• "忘记密码"链接点击 → emit forgot-password
```

#### 10.3.3 CaptchaModal 测试

```
• modelValue=true 时弹窗显示
• modelValue=false 时弹窗关闭
• SlidePuzzle 校验成功 → emit success
• SlidePuzzle 校验失败 → 自动刷新
• 降级方案 ImageCaptcha 正常渲染
• ESC 键关闭弹窗
```

#### 10.3.4 useCountdown 测试

```
• 调用 start(60) 后 countdown.value = 60
• 每秒递减直到 0
• countdown > 0 时 canSend 为 false
• countdown = 0 时 canSend 为 true
• 组件卸载后定时器正确清理
```

#### 10.3.5 路由守卫测试

```
• 未登录访问 / → 重定向 /login
• 未登录访问 /login → 正常渲染
• 已登录访问 /login → 重定向 /
• /login?redirect=/workspace → 登录后跳转 /workspace
```

### 10.4 Commit 前检查

```json
// package.json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

配合 Husky + lint-staged 在 commit 前自动运行相关测试用例。

---

## 11. 国际化设计

### 11.1 vue-i18n 配置

```typescript
// src/locales/index.ts
import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'

const i18n = createI18n({
  legacy: false,              // 使用 Composition API 模式
  locale: 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: { 'zh-CN': zhCN },
})

export default i18n
```

### 11.2 语言包结构

```typescript
// src/locales/zh-CN.ts
export default {
  auth: {
    login: '登录',
    register: '注册',
    logout: '退出登录',
    accountLogin: '账号登录',
    phoneLogin: '手机登录',
    placeholderAccount: '请输入账号',
    placeholderPassword: '请输入密码',
    placeholderPhone: '请输入手机号',
    placeholderSmsCode: '请输入验证码',
    placeholderEmail: '请输入邮箱',
    placeholderNickname: '请输入昵称',
    placeholderConfirmPassword: '请再次输入密码',
    rememberMe: '记住我',
    forgotPassword: '忘记密码',
    getSmsCode: '获取验证码',
    resendSms: '重新发送',
    agreementPrefix: '我已阅读并同意',
    userAgreement: '用户服务协议',
    privacyPolicy: '隐私政策',
    thirdPartyLogin: '第三方账号登录',
    noAccount: '还没有账号？',
    goRegister: '立即注册',
    hasAccount: '已有账号？',
    goLogin: '立即登录',
    // ...
  },
  validation: {
    required: '此项为必填',
    accountLength: '账号长度 2-64 个字符',
    passwordRule: '密码 6-12 个字符，至少包含字母和数字',
    phoneFormat: '请输入正确的手机号',
    smsCodeLength: '验证码为 6 位数字',
    // ...
  },
  error: {
    AUTH_001: '账号或密码错误',
    AUTH_002: '账号已被锁定，请稍后再试',
    AUTH_003: '验证码错误',
    AUTH_004: '验证码已过期',
    AUTH_005: '该手机号未注册',
    // ...
  },
}
```

### 11.3 组件中使用

```vue
<template>
  <el-input :placeholder="$t('auth.placeholderAccount')" />
  <span>{{ $t('auth.noAccount') }} <a>{{ $t('auth.goRegister') }}</a></span>
</template>
```

一期仅实现 `zh-CN` 语言包，目录结构预留 `en-US.ts` 位置，为 1.2.0 英文版迭代提供扩展能力。

---

## 12. 性能优化设计

### 12.1 路由懒加载

所有页面视图组件使用动态导入：

```typescript
// 路由配置中的异步加载
component: () => import('@/views/LoginView.vue')
```

结合 Vite 自动代码分割，每个页面作为独立 chunk 按需加载。

### 12.2 首屏优化

| 优化项            | 说明                           | 目标         |
| -------------- | ---------------------------- | ---------- |
| 关键 CSS 内联      | 将 `variables.css` + `reset.css` 内联至 `index.html` | 减少阻塞渲染请求   |
| 字体优化           | 使用 `font-display: swap` + 字体子集 | 避免文字闪烁     |
| SVG Logo        | 内联至 HTML，不依赖网络请求             | 减少请求数      |
| Element Plus 按需 | unplugin-vue-components 自动引入 | 减小 JS Bundle |

### 12.3 接口优化

- 登录接口失败重试：最多 1 次（防止重复调用密码校验）
- 短信发送接口：乐观更新倒计时，不等待接口返回
- Token 刷新去重锁：防止并发 401 响应触发多次刷新请求

### 12.4 构建优化

```typescript
// vite.config.ts 构建配置
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'element-plus': ['element-plus'],
        'vue-vendor': ['vue', 'vue-router', 'pinia'],
        'auth-module': ['./src/views/LoginView.vue', './src/views/RegisterView.vue'],
      },
    },
  },
  target: 'es2020',
  cssCodeSplit: true,
  sourcemap: false,  // 生产环境不生成 sourcemap
}
```

---

## 13. 附录

### 13.1 页面状态枚举

```typescript
// 登录页面可能的状态
export enum PageStatus {
  IDLE = 'idle',             // 正常空闲
  LOADING = 'loading',       // 登录请求中
  SMS_SENDING = 'smsSending',   // 短信发送中
  SMS_COUNTDOWN = 'smsCountdown', // 短信倒计时
  ERROR = 'error',           // 显示错误信息
  LOCKED = 'locked',         // 账号锁定
  CAPTCHA_REQUIRED = 'captchaRequired', // 需要验证码
}
```

### 13.2 登录完整流程时序图

```
用户 → AccountLoginForm → useAuth → authStore → authApi → 后端
  │         │               │          │          │         │
  │  输入账号密码  │               │          │          │         │
  │────────→│               │          │          │         │
  │         │  submit()     │          │          │         │
  │         │──────────────→│          │          │         │
  │         │               │ 校验表单    │          │         │
  │         │               │ encrypt密码│          │         │
  │         │               │ login()   │          │         │
  │         │               │──────────→│          │         │
  │         │               │           │ POST /login        │
  │         │               │           │─────────→│         │
  │         │               │           │          │         │
  │         │   ←—— 错误 ——  │  ←—— 错误 ——│←————————│ 401/500 │
  │         │ 显示错误信息    │           │          │         │
  │         │               │           │          │         │
  │         │   ←—— 成功 ——  │  ←—— 成功 ——│←————————│ 200 OK  │
  │         │               │ setTokens  │          │         │
  │         │               │ persistTokens         │         │
  │         │               │ router.push(redirect) │         │
  │←────────│               │          │          │         │
  │ 跳转首页   │               │          │          │         │
```

### 13.3 短信验证码发送流程时序图

```
用户 → PhoneLoginForm → useCaptcha → captchaStore → captchaApi → 后端
  │         │              │            │             │          │
  │  输入手机号  │              │            │             │          │
  │  点击获取验证码│              │            │             │          │
  │────────→│              │            │             │          │
  │         │ sendSms()    │            │             │          │
  │         │─────────────→│            │             │          │
  │         │              │ showCaptcha│             │          │
  │         │              │───────────→│             │          │
  │         │              │ 等待用户完成滑块│           │          │
  │←── 弹窗 ──│              │            │             │          │
  │  完成拼图  │              │            │             │          │
  │────────→│              │            │             │          │
  │         │              │ onCaptchaSuccess         │          │
  │         │              │───────────→│             │          │
  │         │              │            │ POST /sms/send         │
  │         │              │            │────────────→│          │
  │         │              │            │             │          │
  │         │  startCountdown()        │             │          │
  │  显示60s倒计时         │            │             │          │
```

### 13.4 组件 Props/Emits 完整契约

**LoginCard.vue**

| Prop         | Type     | Default | 说明     |
| ------------ | -------- | ------- | ------ |
| `loading`    | boolean  | false   | 登录加载状态 |

| Emit  | Payload        | 说明      |
| ----- | -------------- | ------- |
| —     | —              | 纯容器组件   |

**LoginTabs.vue**

| Prop         | Type     | Default     | 说明      |
| ------------ | -------- | ----------- | ------- |
| `modelValue` | string   | `'account'` | 当前选中标签  |

| Emit                  | Payload           | 说明     |
| --------------------- | ----------------- | ------ |
| `update:modelValue`   | `'account' \| 'phone'` | 标签切换  |

**PasswordInput.vue**

| Prop            | Type    | Default | 说明       |
| --------------- | ------- | ------- | -------- |
| `modelValue`    | string  | ''      | 密码值      |
| `placeholder`   | string  | ''      | 占位符      |
| `disabled`      | boolean | false   | 禁用状态     |

| Emit                | Payload | 说明   |
| ------------------- | ------- | ---- |
| `update:modelValue` | string  | 值更新  |

**CountdownButton.vue**

| Prop          | Type    | Default | 说明      |
| ------------- | ------- | ------- | ------- |
| `countdown`   | number  | 0       | 剩余倒计时秒数 |
| `disabled`    | boolean | false   | 禁用状态    |

| Emit      | Payload | 说明     |
| --------- | ------- | ------ |
| `click`   | void    | 点击发送   |

**CaptchaModal.vue**

| Prop         | Type    | Default | 说明       |
| ------------ | ------- | ------- | -------- |
| `modelValue` | boolean | false   | 显示/隐藏    |
| `type`       | string  | 'slide' | 验证码类型    |

| Emit                  | Payload          | 说明       |
| --------------------- | ---------------- | -------- |
| `update:modelValue`   | boolean          | 更新显示状态   |
| `success`             | CaptchaResult    | 验证通过     |
| `fail`                | void             | 验证失败     |

**OAuthPanel.vue**

| Prop         | Type              | Default | 说明       |
| ------------ | ----------------- | ------- | -------- |
| `providers`  | OAuthProvider[]   | [...]   | 第三方平台列表  |

| Emit          | Payload          | 说明       |
| ------------- | ---------------- | -------- |
| `select`      | OAuthProvider    | 选中第三方平台  |

### 13.5 表单校验规则定义

```typescript
// 校验规则集中定义，供组件和 composables 共用
export const validationRules = {
  account: [
    { required: true, message: 'validation.required', trigger: 'blur' },
    { min: 2, max: 64, message: 'validation.accountLength', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'validation.required', trigger: 'blur' },
    { min: 6, max: 12, message: 'validation.passwordRule', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: 'validation.passwordRule', trigger: 'blur' },
  ],
  phone: [
    { required: true, message: 'validation.required', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: 'validation.phoneFormat', trigger: 'blur' },
  ],
  smsCode: [
    { required: true, message: 'validation.required', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: 'validation.smsCodeLength', trigger: 'blur' },
  ],
  email: [
    { required: true, message: 'validation.required', trigger: 'blur' },
    { type: 'email', message: 'validation.emailFormat', trigger: 'blur' },
  ],
  nickname: [
    { required: true, message: 'validation.required', trigger: 'blur' },
    { min: 2, max: 20, message: 'validation.nicknameLength', trigger: 'blur' },
  ],
  registerPassword: [
    { required: true, message: 'validation.required', trigger: 'blur' },
    { min: 8, max: 32, message: 'validation.registerPasswordRule', trigger: 'blur' },
    {
      validator: (_rule: unknown, value: string) => {
        const categories = [/[a-z]/, /[A-Z]/, /\d/, /[!@#$%^&*()_+\-=[\]{}|;':",./<>?`~]/]
        const count = categories.filter(r => r.test(value)).length
        return count >= 3
      },
      message: 'validation.registerPasswordRule',
      trigger: 'blur',
    },
  ],
}
```

### 13.6 npm 脚本清单

```json
{
  "scripts": {
    "dev": "vite",
    "build": "run-p type-check \"build-only {@}\" --",
    "preview": "vite preview",
    "build-only": "vite build",
    "type-check": "vue-tsc --build --force",
    "lint": "eslint . --ext .vue,.ts,.tsx --fix",
    "format": "prettier --write src/",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui"
  }
}
```

---

> 本文档由前端技术团队维护，随登录模块代码实现持续更新。实现过程中如需偏离本文档设计，需在 PR 中说明理由并同步更新此文档。
