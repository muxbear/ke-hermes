# ke-hermes 后端详细设计说明书

## 1. 项目概述

ke-hermes 是一个通用智能体服务，基于 deepagents 框架构建智能体，通过 FastAPI + uvicorn 提供 HTTP API，供前端调用。

## 2. 技术栈

| 组件       | 技术/框架         | 版本要求       | 用途               |
| -------- | -------------- | ---------- | ---------------- |
| Web 框架   | FastAPI        | >=0.100.0  | HTTP API 路由与请求处理 |
| ASGI 服务器 | uvicorn        | >=0.20.0   | 服务运行与部署          |
| 智能体框架    | deepagents     | >=0.6.1    | 智能体图构建           |
| LLM/向量调用 | langchain-openai | >=1.2.0    | DeepSeek/DashScope 模型调用 |
| 配置管理    | pydantic-settings | >=2.0.0    | 环境变量配置类          |
| 环境加载    | python-dotenv  | >=1.0.1    | .env 文件加载        |
| 图执行引擎   | langgraph      | >=1.0.0    | 智能体图状态机运行        |
| Python   | CPython        | >=3.11,<4.0 | 运行环境              |

## 3. 目录结构

```
backend/
├── src/
│   ├── server.py                # 服务入口（FastAPI + uvicorn）
│   ├── agent/
│   │   ├── __init__.py          # 导出 graph
│   │   ├── config/
│   │   │   ├── __init__.py      # 导出 settings 实例
│   │   │   └── config.py        # Settings 配置类定义
│   │   ├── models/
│   │   │   ├── __init__.py      # 导出 llm, embeddings
│   │   │   ├── llm.py           # ChatOpenAI 实例（DeepSeek）
│   │   │   └── em.py            # OpenAIEmbeddings 实例（DashScope）
│   │   ├── tools/
│   │   │   └── __init__.py      # 工具列表导出（预留）
│   │   ├── utils/
│   │   │   └── __init__.py      # 辅助方法导出（预留）
│   │   └── graph.py             # deepagents 智能体图定义
│   └── api/
│       ├── __init__.py           # 导出 router
│       └── agent/
│           ├── __init__.py       # 导出 router
│           └── agent_api.py      # 智能体 API 路由与数据模型
├── tests/
│   ├── conftest.py               # 测试公共 fixtures
│   ├── unit_tests/
│   │   ├── test_config.py       # 配置模块测试
│   │   ├── test_models.py       # 模型实例测试
│   │   └── test_agent.py        # 智能体导出测试
│   └── integration_tests/
│       ├── test_server.py        # 服务启动测试
│       └── test_agent_api.py     # API 接口测试
├── docs/
│   ├── requirements.md           # 需求文档
│   ├── test_plan.md              # 测试规划文档
│   └── design.md                 # 本文件
├── .env                          # 环境变量配置（不入库）
├── .env.example                  # 环境变量示例
└── pyproject.toml                # 项目元数据与依赖
```

## 4. 模块详细设计

### 4.1 服务入口 — `server.py`

**职责：** 创建 FastAPI 应用实例，加载环境变量，注册 API 路由。

**关键设计决策：** `load_dotenv()` 必须在所有业务模块导入之前调用。原因是导入链 `server → api → agent → graph → models.llm → ChatOpenAI(...)` 在模块级创建 LLM 实例，需要从 `.env` 读取 `DEEPSEEK_API_KEY`。若 `load_dotenv()` 在导入之后执行，`ChatOpenAI` 初始化时环境变量为空，会报 `Missing credentials` 错误。

```python
# server.py
from dotenv import load_dotenv

load_dotenv()                     # 必须在业务导入之前

from fastapi import FastAPI
from api import router

app = FastAPI(title="ke-hermes", description="通用智能体服务")
app.include_router(router)
```

**启动命令：**

```bash
cd backend
uvicorn src.server:app --host 127.0.0.1 --port 8000
```

项目通过 `uv pip install -e .` 以可编辑模式安装到虚拟环境，`pyproject.toml` 中 `[tool.setuptools.packages.find] where = ["src"]` 确保所有 `src/` 下的包自动可导入，无需手动设置 `PYTHONPATH`。

### 4.2 配置模块 — `agent/config`

**职责：** 集中管理所有环境变量配置，供其他模块引用。

#### `config.py` — Settings 类

使用 `pydantic_settings.BaseSettings` 定义配置类，自动从环境变量读取值。所有字段提供默认值，仅 `DEEPSEEK_API_KEY` 和 `DASHSCOPE_API_KEY` 为空字符串（需用户在 `.env` 中填写）。

```python
class Settings(BaseSettings):
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_EMBEDDING: str = "text-embedding-v4"
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    HOST: str = "127.0.0.1"
    PORT: int = 8000
```

**设计说明：** `DEEPSEEK_BASE_URL` 使用 DeepSeek 官方 API 地址，`langchain-openai` 的 `ChatOpenAI` 通过 OpenAI 兼容协议调用 DeepSeek。同理，DashScope 的向量模型也通过 OpenAI Embeddings 兼容协议调用，`base_url` 为 DashScope 兼容模式地址。

#### `__init__.py` — 配置实例导出

```python
from agent.config.config import Settings
settings = Settings()
```

模块级创建 `Settings()` 实例，此时 `.env` 已由 `server.py` 的 `load_dotenv()` 加载，环境变量已就绪。

### 4.3 模型模块 — `agent/models`

**职责：** 创建 LLM 和向量模型实例，供 `graph.py` 和后续 RAG 场景使用。

#### `llm.py` — 大语言模型实例

```python
from langchain_openai import ChatOpenAI
from agent.config import settings

llm = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,          # "deepseek-v4-pro"
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,    # "https://api.deepseek.com/v1"
)
```

**设计说明：** DeepSeek 提供 OpenAI 兼容 API，`langchain-openai.ChatOpenAI` 通过设置 `base_url` 即可调用 DeepSeek 模型，无需专用 SDK。

#### `em.py` — 向量模型实例

```python
from langchain_openai import OpenAIEmbeddings
from agent.config import settings

embeddings = OpenAIEmbeddings(
    model=settings.DASHSCOPE_EMBEDDING,           # "text-embedding-v4"
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.DASHSCOPE_BASE_URL,         # DashScope 兼容模式地址
)
```

**设计说明：** DashScope（阿里云）同样提供 OpenAI Embeddings 兼容协议，通过 `base_url` 指向兼容模式端点即可调用。

#### `__init__.py` — 模型导出

```python
from agent.models.llm import llm
from agent.models.em import embeddings
```

### 4.4 智能体图 — `agent/graph.py`

**职责：** 使用 deepagents 框架定义智能体图。

```python
from deepagents import create_deep_agent
from agent.models.llm import llm

graph = create_deep_agent(
    model=llm,
    system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求提供准确、有用的回答。",
)
```

**设计说明：** `create_deep_agent()` 是 deepagents 框架的主入口函数，返回 `CompiledStateGraph` 类型。传入 `model` 参数为已初始化的 `ChatOpenAI` 实例（而非模型字符串），确保使用 DeepSeek 配置。deepagents 自动组装以下中间件栈：

- `TodoListMiddleware` — 任务列表管理
- `SkillsMiddleware` — 技能注册
- `FilesystemMiddleware` — 文件读写
- `SummarizationMiddleware` — 长对话摘要压缩
- `PatchToolCallsMiddleware` — 工具调用修补
- `AnthropicPromptCachingMiddleware` — 提示缓存（即使使用 DeepSeek 也生效）
- 内置工具：`write_todos`、`ls`、`read_file`、`write_file`、`edit_file`、`glob`、`grep`

`system_prompt` 传入中文提示，定义智能体的角色和行为准则。

### 4.5 智能体导出 — `agent/__init__.py`

```python
from agent.graph import graph
__all__ = ["graph"]
```

### 4.6 API 模块 — `api/agent/agent_api.py`

**职责：** 将智能体 `graph` 暴露为 HTTP REST API 接口。

#### 数据模型

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)    # 禁止空字符串

class ChatResponse(BaseModel):
    response: str

class StreamToken(BaseModel):
    token: str
```

**设计说明：** `message` 字段使用 `Field(min_length=1)` 约束，空字符串请求会返回 422 校验错误。三个模型直接定义在 `agent_api.py` 中，而非独立 `schemas.py` 文件，保持简洁。

#### `/api/chat` — 对话接口

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=req.message)]}
    )
    final_message = result["messages"][-1]
    return ChatResponse(response=final_message.content)
```

**调用流程：**

1. 接收 `ChatRequest`，提取 `message`
2. 包装为 `HumanMessage`，传入 `graph.ainvoke()`
3. deepagents 执行智能体图，调用 DeepSeek LLM 生成回复
4. 从返回结果中取最后一条消息（`AIMessage`），提取 `content`
5. 包装为 `ChatResponse` 返回

#### `/api/chat/stream` — 流式对话接口

```python
@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_generator():
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=req.message)]},
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].text
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**调用流程：**

1. 接收 `ChatRequest`，提取 `message`
2. 包装为 `HumanMessage`，传入 `graph.astream_events(version="v2")`
3. 逐事件迭代，筛选 `on_chat_model_stream` 类型事件
4. 提取每个 token，以 SSE 格式 `data: {"token": "..."}\n\n` 逐条推送
5. 使用 `StreamingResponse(media_type="text/event-stream")` 返回流式响应

**设计说明：** `astream_events` 是 LangGraph 提供的异步流式事件接口，`version="v2"` 确保事件格式稳定。仅过滤 `on_chat_model_stream` 事件，跳过工具调用等中间事件，前端只接收 LLM 生成的 token 流。

#### 路由注册链

```
agent_api.py → router (APIRouter, prefix="/api")
    ↓
api/agent/__init__.py → 导出 router
    ↓
api/__init__.py → 导出 router
    ↓
server.py → app.include_router(router)
```

## 5. 环境变量设计

所有配置通过 `.env` 文件管理，`python-dotenv` 在应用启动时加载。

| 变量名               | 类型   | 默认值                                            | 说明              |
| ----------------- | ---- | ---------------------------------------------- | --------------- |
| `DEEPSEEK_API_KEY`  | str | `""`                                           | DeepSeek API 密钥（必填） |
| `DEEPSEEK_MODEL`    | str | `"deepseek-v4-pro"`                            | LLM 模型名称        |
| `DEEPSEEK_BASE_URL` | str | `"https://api.deepseek.com/v1"`                | DeepSeek API 地址 |
| `DASHSCOPE_API_KEY`  | str | `""`                                           | DashScope API 密钥 |
| `DASHSCOPE_EMBEDDING` | str | `"text-embedding-v4"`                          | 向量模型名称          |
| `DASHSCOPE_BASE_URL` | str | `"https://dashscope.aliyuncs.com/compatible-mode/v1"` | DashScope API 地址 |
| `HOST`            | str | `"127.0.0.1"`                                  | 服务监听地址          |
| `PORT`            | int | `8000`                                          | 服务监听端口          |

## 6. 关键设计决策

### 6.1 load_dotenv 调用时序

`load_dotenv()` 在 `server.py` 最顶部调用，位于所有业务模块导入之前。原因：Python 导入语句在模块级立即执行，导入链触发 `ChatOpenAI` 和 `OpenAIEmbeddings` 实例创建，这两个实例在初始化时需要读取 `DEEPSEEK_API_KEY` 和 `DASHSCOPE_API_KEY`。若 `load_dotenv()` 在导入之后执行，实例创建时环境变量为空，会报认证错误。

### 6.2 模型实例模块级创建

LLM 和 Embeddings 实例在模块级（而非函数内）创建，所有请求共享同一实例。`ChatOpenAI` 和 `OpenAIEmbeddings` 内部管理连接池和客户端对象，模块级创建避免重复初始化开销。

### 6.3 OpenAI 兼容协议调用 DeepSeek/DashScope

DeepSeek 和 DashScope 均提供 OpenAI API 兼容接口，`langchain-openai` 的 `ChatOpenAI` 和 `OpenAIEmbeddings` 通过设置 `base_url` 参数即可调用这些服务，无需引入各自专用 SDK，降低了依赖复杂度。

### 6.4 SSE 流式响应格式

流式接口使用 SSE（Server-Sent Events）协议，每条事件格式为 `data: {"token": "..."}\n\n`，符合 SSE 标准规范。前端可通过 `EventSource` 或 `fetch` + `ReadableStream` 解析。

### 6.5 可编辑模式安装

项目通过 `uv pip install -e .` 以可编辑模式安装到虚拟环境，`pyproject.toml` 中 `[tool.setuptools.packages.find] where = ["src"]` 确保包发现路径指向 `src/`。安装后 `src/` 下所有模块自动可导入，运行 `uvicorn src.server:app` 无需手动设置 `PYTHONPATH=src`。

## 7. 数据流

### 7.1 普通对话请求

```
前端 POST /api/chat {"message": "用户输入"}
    ↓
agent_api.py → ChatRequest 校验
    ↓
graph.ainvoke({"messages": [HumanMessage(content="用户输入")]})
    ↓
deepagents 执行智能体图 → ChatOpenAI(DeepSeek) 生成回复
    ↓
取 result["messages"][-1].content → AIMessage
    ↓
ChatResponse {"response": "智能体回复"}
    ↓
前端接收 JSON 响应
```

### 7.2 流式对话请求

```
前端 POST /api/chat/stream {"message": "用户输入"}
    ↓
agent_api.py → ChatRequest 校验
    ↓
graph.astream_events({"messages": [HumanMessage(...)]}, version="v2")
    ↓
deepagents 逐事件执行 → on_chat_model_stream 事件
    ↓
提取 token → SSE: data: {"token": "..."}\n\n
    ↓
StreamingResponse(media_type="text/event-stream") 逐条推送
    ↓
前端通过 SSE 解析 token 流
```

### 7.3 模块依赖关系

```
server.py
  ├── load_dotenv()        ← 加载 .env
  └── api.router
        └── agent_api.router
              └── agent.graph
                    ├── agent.models.llm  ← ChatOpenAI(DeepSeek)
                    │     └── agent.config.settings
                    └── agent.models.em   ← OpenAIEmbeddings(DashScope)
                          └── agent.config.settings
```

所有模块最终依赖 `agent.config.settings`，配置变更只需修改 `.env` 文件，无需改动代码。

## 8. 启动与部署

### 8.1 开发环境启动

```bash
cd backend
uvicorn src.server:app --host 127.0.0.1 --port 8000
```

### 8.2 前置条件

1. Python >= 3.11
2. 虚拟环境已创建并安装依赖（`uv pip install -e .`）
3. `.env` 文件已配置 `DEEPSEEK_API_KEY`

### 8.3 API 文档

服务启动后访问 `http://127.0.0.1:8000/docs`，FastAPI 自动生成交互式 Swagger UI 文档。