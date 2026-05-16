# 后端测试规划文档

## 测试概览

基于需求文档 F1-F3 功能需求，按模块划分测试范围，采用 pytest + httpx 进行单元测试和接口测试。

| 测试类别 | 覆盖需求 | 目录 |
| -------- | -------- | ---- |
| 单元测试 | F2.1 配置、F2.2 模型、F2 智能体导出 | `tests/unit_tests/` |
| 接口测试 | F1 服务启动、F3 API 接口 | `tests/integration_tests/` |

## 单元测试

### T1: 配置模块 — `test_config.py`

对应需求 F2.1，测试 `agent/config/config.py`。

| 测试项 | 说明 | 结果 |
| ------ | ---- | ---- |
| T1.1 默认值测试 | 未设置环境变量时，`DEEPSEEK_MODEL` 默认为 `deepseek-v4-pro`，`DASHSCOPE_EMBEDDING` 默认为 `text-embedding-v4`，`HOST` 默认 `127.0.0.1`，`PORT` 默认 `8000` | PASSED |
| T1.2 环境变量注入 | 通过 `monkeypatch.setenv` 设置 `DEEPSEEK_API_KEY`、`DASHSCOPE_API_KEY` 等，验证 Settings 实例读取正确 | PASSED |
| T1.3 Base URL 默认值 | 使用 `monkeypatch.delenv` 清除环境变量后，验证 `DEEPSEEK_BASE_URL` 和 `DASHSCOPE_BASE_URL` 有正确的默认值 | PASSED |

### T2: 模型模块 — `test_models.py`

对应需求 F2.2，测试 `agent/models/llm.py` 和 `agent/models/em.py`。

| 测试项 | 说明 | 结果 |
| ------ | ---- | ---- |
| T2.1 LLM 实例创建 | 验证 `llm` 是 `ChatOpenAI` 类型，且 `model_name` 与配置一致 | PASSED |
| T2.2 Embeddings 实例创建 | 验证 `embeddings` 是 `OpenAIEmbeddings` 类型 | PASSED |
| T2.3 模型导出 | 验证 `agent.models.__init__.py` 正确导出 `llm` 和 `embeddings` | PASSED |

### T3: 智能体模块 — `test_agent.py`

对应需求 F2，测试 `agent/graph.py` 和 `agent/__init__.py`。

| 测试项 | 说明 | 结果 |
| ------ | ---- | ---- |
| T3.1 graph 类型 | 验证 `graph` 是 `CompiledStateGraph` 类型 | PASSED |
| T3.2 模块导出 | 验证 `from agent import graph` 可以正确导入 | PASSED |

## 接口测试

### T4: 服务启动 — `test_server.py`

对应需求 F1，测试 `server.py`。

| 测试项 | 说明 | 结果 |
| ------ | ---- | ---- |
| T4.1 FastAPI 实例 | 验证 `app` 是 `FastAPI` 类型，title 为 `ke-hermes` | PASSED |
| T4.2 路由注册 | 验证 `/api/chat` 和 `/api/chat/stream` 路由已注册到 app | PASSED |
| T4.3 .env 加载 | 验证 `load_dotenv` 可正常调用 | PASSED |

### T5: 智能体接口 — `test_agent_api.py`

对应需求 F3，测试 `api/agent/agent_api.py`。

| 测试项 | 说明 | 结果 |
| ------ | ---- | ---- |
| T5.1 /api/chat 正常请求 | 使用 httpx AsyncClient 发送 `POST /api/chat`，请求体 `{ "message": "hello" }`，验证返回 `ChatResponse` 格式 | PASSED |
| T5.2 /api/chat 请求校验 | 发送空 `message` 字段，验证返回 422 校验错误 | PASSED |
| T5.3 /api/chat 缺少字段 | 发送无 `message` 字段的请求体，验证返回 422 | PASSED |
| T5.4 /api/chat/stream SSE | 发送 `POST /api/chat/stream`，验证响应 `content-type` 为 `text/event-stream` | PASSED |
| T5.5 /api/chat/stream 请求校验 | 发送空 `message`，验证返回 422 | PASSED |

## 测试工具与依赖

| 工具 | 用途 |
| ---- | ---- |
| pytest | 测试框架 |
| pytest-asyncio | 异步测试支持 |
| httpx | FastAPI 接口测试（ASGITransport + AsyncClient） |
| monkeypatch | 环境变量注入/隔离 |
| python-dotenv | 测试前加载 `.env` 环境变量 |

## 测试目录结构

```
backend/tests/
├── conftest.py              # 公共 fixtures（load_dotenv、app 实例、AsyncClient）
├── unit_tests/
│   ├── __init__.py
│   ├── test_config.py       # T1: 配置模块测试（3项）
│   ├── test_models.py       # T2: 模型模块测试（3项）
│   └── test_agent.py        # T3: 智能体模块测试（2项）
└── integration_tests/
    ├── __init__.py
    ├── test_server.py       # T4: 服务启动测试（3项）
    └── test_agent_api.py    # T5: 智能体接口测试（5项）
```

## 运行方式

```bash
cd backend
PYTHONPATH=src .venv/Scripts/python -m pytest tests/ -v
```

API Key 配置在 `backend/.env` 文件中，`conftest.py` 在导入模块前调用 `load_dotenv()` 加载环境变量。

## 注意事项

- 单元测试不依赖外部 API（仅验证实例属性和类型）
- 接口测试中 `/api/chat` 和 `/api/chat/stream` 调用智能体涉及真实 LLM 调用，需在 `.env` 中配置真实 `DEEPSEEK_API_KEY`
- 无真实 API Key 时，LLM 相关接口测试会被 `@pytest.mark.skipif` 跳过，其余测试正常运行
- SSE 流式接口测试验证响应格式（content-type），不验证 LLM 返回内容的具体语义
- `ChatRequest.message` 字段设有 `min_length=1` 约束，空字符串请求返回 422
- `conftest.py` 必须在导入 `server` 模块前调用 `load_dotenv()`，否则模块级创建的 `ChatOpenAI` 实例会因找不到 API Key 而报错

## 测试执行结果

```
16 passed in 5.88s
```

| 类别 | 通过 | 总计 |
| ---- | ---- | ---- |
| 单元测试 | 8 | 8 |
| 接口测试 | 8 | 8 |