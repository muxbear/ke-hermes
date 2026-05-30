# ke-hermes 前端需求说明书

## 1. 项目概述

ke-hermes 前端是通用智能体的 Web 交互界面，采用 Vue3 + Pinia 技术栈，通过调用后端 `/api/chat` 和 `/api/chat/stream` 接口实现对话功能，支持普通回复和流式 token 输出两种模式。

## 2. 技术栈

| 组件       | 技术            | 用途              |
| -------- | ------------- | --------------- |
| 框架       | Vue 3         | UI 渲染与组件化       |
| 状态管理    | Pinia         | 对话历史、加载状态等全局状态 |
| 构建       | Vite          | 开发服务器与生产构建      |
| HTTP 请求  | axios         | 调用后端普通对话接口      |
| 流式请求    | fetch + ReadableStream | 解析 SSE 流式响应     |
| 样式       | CSS           | 界面布局与样式         |

## 3. 功能需求

### F1: 对话界面

提供主对话页面，用户可输入消息并查看智能体回复。

**具体要求：**

- 页面布局：上方消息列表区域，下方输入区域
- 消息列表展示用户消息和智能体回复，区分左右对齐
- 输入区域包含文本输入框和发送按钮
- 发送后清空输入框，消息立即追加到列表
- 消息列表自动滚动到最新消息

### F2: 普通对话

调用后端 `POST /api/chat` 接口发送消息，获取完整回复。

**具体要求：**

- 请求体：`{ "message": "string" }`
- 响应体：`{ "response": "string" }`
- 发送请求后显示加载状态（输入框禁用、发送按钮禁用）
- 收到响应后将智能体回复追加到消息列表
- 请求失败时显示错误提示

### F3: 流式对话

调用后端 `POST /api/chat/stream` 接口发送消息，通过 SSE 接收逐 token 推送的流式回复。

**具体要求：**

- 请求体：`{ "message": "string" }`
- 响应格式：SSE 事件流，每条 `data: {"token": "string"}\n\n`
- 发送请求后立即在消息列表中创建一条空的智能体回复
- 每个 token 到达后追加到该回复文本中，实现逐字输出效果
- 流式完成后标记该回复为已完成状态
- 流式输出过程中输入框和发送按钮禁用
- 流式过程中发生错误时，在当前回复末尾追加错误提示

**SSE 解析方式：** 使用 `fetch` 发送 POST 请求，通过 `response.body.getReader()` 读取 `ReadableStream`，逐块解析 SSE 格式数据。不能使用浏览器原生 `EventSource`，因为它仅支持 GET 请求。

### F4: 对话状态管理

使用 Pinia store 管理对话相关状态。

**具体要求：**

- 定义 `chatStore`，包含以下状态：
  - `messages` — 消息列表，每条消息包含 `role`（`user` / `assistant`）、`content`（文本）、`streaming`（是否正在流式输出）
  - `loading` — 是否正在等待回复
- 提供以下 action：
  - `sendMessage(message)` — 发送用户消息，追加到 `messages`，调用流式接口获取回复
  - `appendToken(token)` — 流式输出时追加 token 到当前回复
  - `finishStreaming()` — 流式输出完成，标记 `streaming` 为 false
- 消息持久化：当前阶段不持久化，页面刷新后清空；后续可扩展 localStorage 存储

### F5: 界面样式

**具体要求：**

- 整体风格简洁，白色背景
- 用户消息靠右对齐，深色背景浅色文字
- 智能体回复靠左对齐，浅色背景深色文字
- 输入框固定在页面底部，上方消息列表可滚动
- 流式输出时智能体回复区域显示打字效果
- 加载状态时发送按钮显示禁用样式

## 4. 接口对接

### 4.1 后端接口

| 接口                    | 方法   | 请求体                       | 响应体                  | 用途   |
| --------------------- | ---- | ------------------------- | -------------------- | ---- |
| `/api/chat`           | POST | `{ "message": "string" }` | `{ "response": "string" }` | 普通对话 |
| `/api/chat/stream`    | POST | `{ "message": "string" }` | SSE 流 `data: {"token": "string"}\n\n` | 流式对话 |

### 4.2 错误处理

| 场景           | 状态码 | 处理方式              |
| ------------ | --- | ----------------- |
| 空消息         | 422 | 前端 `min_length=1` 校验，不发送请求 |
| 后端不可用      | 网络错误 | 在消息列表中显示连接失败提示    |
| 后端内部错误    | 500 | 在消息列表中显示服务错误提示    |

### 4.3 请求配置

- 后端地址：`http://127.0.0.1:8000`
- 开发环境通过 Vite `proxy` 配置代理，避免跨域问题
- axios 实例的 `baseURL` 设为 `/api`（通过代理转发到后端）

## 5. 状态设计

### Pinia Store — `chatStore`

```typescript
interface Message {
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean    // true 表示正在流式接收
}

interface ChatState {
  messages: Message[]
  loading: boolean
}
```

**Actions：**

| Action             | 说明                            |
| ------------------ | ----------------------------- |
| `sendMessage(msg)` | 追加用户消息，创建流式回复占位，发起 SSE 请求 |
| `appendToken(t)`   | 向最后一条 assistant 消息追加 token  |
| `finishStreaming()`| 标记流式完成，设置 loading=false    |
| `setError(err)`    | 在最后一条 assistant 消息追加错误文本   |

## 6. 目录结构

```
frontend/
├── src/
│   ├── App.vue                # 应用根组件
│   ├── main.js                # Vue 应用入口
│   ├── stores/
│   │   └── chat.js            # Pinia chatStore
│   ├── components/
│   │   ├── ChatView.vue       # 对话页面主组件
│   │   ├── MessageList.vue    # 消息列表组件
│   │   ├── MessageItem.vue    # 单条消息组件
│   │   └── InputBar.vue       # 输入区域组件
│   ├── services/
│   │   └── chatApi.js         # 后端 API 调用封装
│   └── assets/
│       └── styles/
│           └── main.css       # 全局样式
├── public/
│   └── favicon.ico
├── tests/
├── docs/
│   ├── requirements.md        # 本文件
│   └── design.md              # 详细设计说明书
├── index.html                 # HTML 入口
├── vite.config.js             # Vite 配置（含 proxy）
└── package.json               # 依赖配置
```

## 7. 环境与配置

| 配置项          | 说明                | 开发环境值                    |
| ------------ | ----------------- | ----------------------- |
| Vite proxy   | 代理 `/api` 到后端     | `http://127.0.0.1:8000` |
| axios baseURL | API 请求基础路径        | `/api`                  |

## 8. 依赖清单

| 包名        | 用途       |
| --------- | -------- |
| vue       | Vue 3 核心 |
| pinia     | 状态管理     |
| axios     | HTTP 请求  |
| vite      | 构建工具     |
| @vitejs/plugin-vue | Vite Vue 插件 |