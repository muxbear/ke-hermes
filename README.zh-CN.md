<p align="center">
  <h1 align="center">⚡ Ke Hermes</h1>
  <p align="center"><strong>通用智能体服务平台</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python">
  <img src="https://img.shields.io/badge/vue-3.5-brightgreen" alt="Vue">
  <img src="https://img.shields.io/badge/fastapi-0.100+-teal" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

[English](README.md)

## 项目简介

Ke Hermes 是一个通用智能体 Web 应用，采用前后端分离架构。基于 DeepAgents (LangGraph) 和 DeepSeek 大语言模型，提供智能对话交互界面，支持实时流式响应、用户认证和第三方 OAuth 登录。

## 功能特性

- **AI 对话** — 基于 DeepSeek LLM 的实时 SSE 流式对话，支持非流式降级方案
- **用户认证** — JWT 登录态管理，bcrypt 密码哈希，RSA-2048 加密传输密码
- **注册** — 手机短信注册和邮箱注册
- **第三方登录** — GitHub、Google、微信 OAuth 登录
- **验证码** — 滑块验证码
- **速率限制** — 可配置的登录失败锁定和短信日发送上限
- **国际化** — 基于 vue-i18n 的多语言支持

## 系统架构

```
┌─────────────────────────────────────────┐
│              前端 (Vue 3)                │
│    Element Plus + Pinia + Vue Router     │
│    localhost:5173                        │
└──────────────┬──────────────────────────┘
               │ /api (Vite 代理)
┌──────────────▼──────────────────────────┐
│            后端 (FastAPI)                │
│    LangGraph + DeepSeek + SQLAlchemy     │
│    localhost:8000                        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      LLM: DeepSeek (deepseek-v4-pro)     │
│      向量: DashScope                     │
│      存储: SQLite / PostgreSQL           │
│      缓存: Redis (可选)                  │
└─────────────────────────────────────────┘
```

## 项目结构

```
ke-hermes/
├── frontend/          # Vue 3 + Vite + Element Plus 前端
│   ├── src/
│   │   ├── views/     # 页面组件
│   │   ├── components/# 可复用组件
│   │   ├── composables/# 组合式函数
│   │   ├── stores/    # Pinia 状态管理
│   │   ├── services/  # API 层 (Axios + SSE)
│   │   ├── router/    # Vue Router 配置
│   │   ├── types/     # TypeScript 类型
│   │   └── locales/   # i18n 语言文件
│   └── tests/
├── backend/           # Python FastAPI + LangGraph 后端
│   ├── src/
│   │   ├── server.py  # 应用入口
│   │   ├── api/       # 路由模块 (auth/chat/captcha/oauth/sms)
│   │   ├── agent/     # LangGraph 智能体 (graph/config/models/tools)
│   │   ├── core/      # 核心模块 (security/store/response)
│   │   └── db/        # 数据库引擎与 ORM 模型
│   └── tests/
└── docs/              # 项目文档
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- uv (Python 包管理器)

### 后端

```bash
cd backend
cp .env.example .env     # 编辑 .env 填入 API 密钥
uv sync                  # 安装依赖
uv run uvicorn server:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173` — 开发服务器自动将 `/api` 请求代理到后端。

## 环境变量

| 变量名 | 说明 | 是否必填 |
|---|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 是 |
| `DEEPSEEK_MODEL` | 模型名称 (默认: `deepseek-v4-pro`) | 否 |
| `DEEPSEEK_BASE_URL` | API 基地址 | 否 |
| `DATABASE_URL` | 数据库连接 (SQLite: `sqlite+aiosqlite:///ke-hermes.db`) | 否 |
| `REDIS_URL` | Redis 连接 (不可用时自动降级为内存存储) | 否 |
| `JWT_SECRET_KEY` | JWT 签名密钥 (留空则自动生成) | 否 |

## 常用命令

| 目录 | 命令 | 说明 |
|---|---|---|
| backend | `uv run pytest` | 运行测试 |
| backend | `uv run ruff check .` | 代码检查 |
| backend | `uv run ruff format .` | 代码格式化 |
| frontend | `npm run dev` | 启动开发服务器 |
| frontend | `npm run build` | 生产构建 |
| frontend | `npm run test` | 运行测试 |
| frontend | `npm run lint` | 代码检查 |

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端框架 | Vue 3 + TypeScript |
| UI 组件库 | Element Plus |
| 状态管理 | Pinia |
| 构建工具 | Vite 5 |
| 后端框架 | FastAPI |
| 智能体框架 | DeepAgents / LangGraph |
| 大语言模型 | DeepSeek (deepseek-v4-pro) |
| 向量模型 | DashScope (text-embedding-v4) |
| 数据库 | SQLAlchemy async + SQLite / PostgreSQL |
| 缓存 | Redis (支持内存降级) |
| 认证 | JWT (HS256) + bcrypt + RSA-2048 |
| 测试 | pytest + vitest |

## 开源协议

[MIT](LICENSE)
