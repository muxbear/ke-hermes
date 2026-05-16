# 后端需求文档

## 项目概述

ke-hermes 后端是一个通用智能体服务，基于 deepagents 框架构建智能体，并通过 FastAPI + uvicorn 提供 HTTP API 接口，供前端调用。

## 功能需求

### F1: uvicorn 服务

提供一个基于 uvicorn 的 ASGI 服务，用于发布后端所有接口。

**具体要求：**

- 入口文件：`backend/src/server.py`
- 使用 FastAPI 创建应用实例
- 使用 uvicorn 启动服务，默认端口 8000
- 支持通过 `.env` 配置端口和 host
- 启动命令：`uvicorn src.server:app --host 127.0.0.1 --port 8000`

### F2: 智能体实现

在 `backend/src/agent/graph.py` 中使用 deepagents 框架实现一个通用智能体。

**具体要求：**

- 使用 deepagents 框架定义智能体图（Agent Graph）
- 智能体具备对话能力，接收用户输入并返回响应
- 通过 `langchain-openai` 兼容接口调用 DeepSeek 模型作为智能体的 LLM 后端
- 智能体图通过 `backend/src/agent/__init__.py` 导出，模块名保持为 `graph`
- LLM 配置（模型名、API Key 等）通过环境变量注入，不硬编码

#### F2.1: 配置定义包 — `agent/config`

集中管理智能体相关配置，从 `.env` 文件读取并导出配置实例。

- `agent/config/__init__.py` — 导出配置实例
- `agent/config/config.py` — 使用 Pydantic `BaseSettings` 定义配置类，从环境变量读取以下字段：
  - `DEEPSEEK_API_KEY` — DeepSeek API 密钥
  - `DEEPSEEK_MODEL` — 默认模型名（默认值 `deepseek-v4-pro`）
  - `DEEPSEEK_BASE_URL` — API 基地址（可选，用于兼容第三方 OpenAI 接口）
  - `DASHSCOPE_API_KEY` — DashScope API 密钥
  - `DASHSCOPE_EMBEDDING` — 向量模型名（默认值 `text-embedding-v4`）
  - `DASHSCOPE_BASE_URL` — DashScope API 基地址（可选）
- 通过 `python-dotenv` 在应用启动时加载 `.env` 文件

#### F2.2: 模型定义包 — `agent/models`

定义智能体使用的 LLM 和向量模型实例。

- `agent/models/__init__.py` — 导出模型实例
- `agent/models/llm.py` — 定义大语言模型实例，使用 `langchain-openai` 的 `ChatOpenAI`：
  - 从 `agent/config` 读取 `DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL`
  - 导出 `llm` 实例供 `graph.py` 使用
- `agent/models/em.py` — 定义向量模型（Embedding Model）实例，使用 `langchain-openai` 的 `OpenAIEmbeddings`：
  - 从 `agent/config` 读取 `DASHSCOPE_API_KEY`、`DASHSCOPE_EMBEDDING`、`DASHSCOPE_BASE_URL`
  - 导出 `embeddings` 实例供后续 RAG 或检索场景使用

#### F2.3: 大模型工具包 — `agent/tools`

定义可被智能体调用的工具（Tool），扩展智能体能力边界。

- `agent/tools/__init__.py` — 导出工具列表
- 当前阶段为预留目录，后续可添加如搜索、计算、文件读取等工具
- 工具使用 LangChain `@tool` 装饰器定义，返回 `list[BaseTool]` 供 graph 注册

#### F2.4: 工具方法包 — `agent/utils`

存放智能体模块内部通用的辅助函数和类。

- `agent/utils/__init__.py` — 导出公共辅助方法
- 当前阶段为预留目录，后续可添加如日志格式化、消息转换等辅助逻辑

### F3: 智能体 API 接口

在 `backend/src/api/agent/` 目录下为智能体发布 REST API 接口。

**具体要求：**

- 服务模块：`backend/src/api/agent/agent_api.py`
- 提供以下接口：

| 方法   | 路径                 | 说明     | 请求体                       | 响应体                                      |
| ---- | ------------------ | ------ | ------------------------- | ---------------------------------------- |
| POST | `/api/chat`        | 发送对话消息 | `{ "message": "string" }` | `{ "response": "string" }`               |
| POST | `/api/chat/stream` | 流式对话   | `{ "message": "string" }` | SSE 事件流，每条 `data: { "token": "string" }` |

- 将路由注册到 FastAPI 应用实例中
- 请求与响应使用 Pydantic 模型定义

#### F3.1: 智能体服务 — `api/agent/agent_api.py`

将智能体 `graph` 暴露为 HTTP 服务。

- 创建 `APIRouter` 实例，prefix 为 `/api`
- `/api/chat`：调用 `graph.invoke()` 执行智能体，返回完整响应
- `/api/chat/stream`：调用 `graph.stream()` 执行智能体，通过 SSE（Server-Sent Events）逐 token 返回流式响应
- 流式接口使用 FastAPI 的 `StreamingResponse`，`media_type="text/event-stream"`
- Pydantic 数据模型直接在 `agent_api.py` 中定义：
  - `ChatRequest` — 请求模型，字段 `message: str`
  - `ChatResponse` — 响应模型，字段 `response: str`
  - `StreamToken` — 流式 token 模型，字段 `token: str`

#### F3.2: API 包导出 — `api/agent/__init__.py`

- 导出 `router` 实例，供 `server.py` 注册到 FastAPI 应用

## 环境变量

| 变量名               | 说明            | 示例值                              | 是否必填 |
| ----------------- | ------------- | -------------------------------- | ---- |
| `DEEPSEEK_API_KEY`  | DeepSeek API 密钥 | `sk-xxx...`                    | 必填   |
| `DEEPSEEK_MODEL`    | LLM 模型名称     | `deepseek-v4-pro`              | 可选   |
| `DEEPSEEK_BASE_URL` | API 基地址       | `https://api.deepseek.com/v1`  | 可选   |
| `DASHSCOPE_API_KEY`  | DashScope API 密钥 | `sk-xxx...`                    | 可选   |
| `DASHSCOPE_EMBEDDING` | 向量模型名称     | `text-embedding-v4`            | 可选   |
| `DASHSCOPE_BASE_URL` | DashScope API 基地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 可选   |
| `HOST`            | 服务监听地址        | `127.0.0.1`                 | 可选   |
| `PORT`            | 服务监听端口        | `8000`                      | 可选   |

## 技术栈

| 组件       | 技术               |
| -------- | ---------------- |
| Web 框架   | FastAPI          |
| ASGI 服务器 | uvicorn          |
| 智能体框架    | deepagents       |
| LLM 调用   | langchain-openai |
| 环境配置     | python-dotenv    |

## 目录结构

```
backend/
├── src/
│   ├── server.py          # uvicorn 服务入口
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── config.py  # 获取 .env 中的配置
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── em.py        # 文本向量模型 text-embedding-v4
│   │   │   └── llm.py       # 定义大语言模型, deepseek-v4-pro, qwen3.6-plus 等
│   │   ├── tools/
│   │   │   └── __init__.py
│   │   ├── utils/
│   │   │   └── __init__.py
│   │   └── graph.py         # 使用 deepagents 定义的智能体
│   └── api/
│       ├── __init__.py
│       └── agent/
│           ├── __init__.py
│           └── agent_api.py  # 智能体提供的服务
├── tests/
├── docs/
├── .env                     # 环境变量配置（不入库）
├── .env.example             # 环境变量示例
└── pyproject.toml           # 项目依赖配置
```