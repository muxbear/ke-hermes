# Ke-Hermes 事件流优化规划

## 背景

DeepAgents 官方文档推荐使用 `stream_events(version="v3")` API 进行事件流处理，该 API 提供类型化的投影（projections）如 `stream.messages`、`stream.subagents`、`stream.tool_calls` 等，替代了手动解析 v2 原始事件的模式。

当前后端 `agent_api.py` 使用 `astream_events(version="v2")`，通过解析底层事件类型（`on_chat_model_stream`、`on_chain_start`、`on_tool_start` 等）并自维护 `chain_names` 栈来组装 SSE 数据帧。这种方式存在以下不足：

- **无法感知子智能体层级**：使用栈跟踪 agent 嵌套，对 DeepAgents 的 subagent 概念无感知
- **无工具输出流式传输**：只能等待工具执行完成后一次性返回完整输出
- **内部事件过滤负担**：需手动过滤 LangGraph/Runnable/Channel 等内部链事件
- **缺少推理内容支持**：无法区分推理 token 和文本 token
- **错误处理粒度粗**：子智能体级别的错误无法单独捕获和上报

## 现状分析

### 当前架构

```
frontend (SSE fetch) → POST /api/chat/stream → StreamingResponse
                                                      ↑
                                          event_generator()
                                              ↑
                                  graph.astream_events(version="v2")
                                              ↑
                                    create_deep_agent() graph
```

### 当前 SSE 数据帧类型

| 帧类型 | 触发条件 | 关键字段 |
|--------|---------|---------|
| `{"token": "..."}` | `on_chat_model_stream` | 文本 token |
| `{"trace": {"type": "agent_start", "name": "..."}}` | `on_chain_start` | agent 名称 |
| `{"trace": {"type": "agent_end", "name": "..."}}` | `on_chain_end` | agent 名称 |
| `{"trace": {"type": "tool_start", "name": "...", "agent": "...", "input": "..."}}` | `on_tool_start` | 工具名、父 agent、输入 |
| `{"trace": {"type": "tool_end", "name": "...", "agent": "...", "output": "..."}}` | `on_tool_end` | 工具名、父 agent、输出 |
| `{"error": "..."}` | 异常 | 错误消息 |
| `{"thread_id": "..."}` | 流结束 | 对话线程 ID |

### 前端消费方式

前端通过 `ReadableStream` 消费 SSE，每个 `data:` 行解析后分别调用 `onToken`、`onTrace`、`onThreadId`、`onError` 回调。`TracePanel.vue` 组件根据 trace 事件展示 agent/tool 生命周期。

## 优化目标

1. 从 v2 原始事件 API 迁移到 v3 投影 API
2. 支持子智能体层级感知的事件流
3. 支持工具输出的流式增量传输
4. 支持推理内容（reasoning）的区分和传输
5. 保持前端 SSE 协议兼容（渐进式升级，不破坏现有前端）
6. 提升错误处理的细粒度

## 优化方案

### 第一阶段：v2 → v3 API 升级（兼容模式）

保持现有 SSE 数据帧格式不变，但将底层实现从 v2 事件解析切换到 v3 投影 API。这是风险最低的升级路径。

**修改文件**：`backend/src/api/agent/agent_api.py`

**改动要点**：

1. 将 `version="v2"` 改为 `version="v3"`（line 107）
2. 使用 `stream.messages` 替代手动解析 `on_chat_model_stream`：
   ```python
   async for message in stream.messages:
       async for delta in message.text:
           yield sse_frame({"token": delta})
   ```
3. 使用 `stream.tool_calls` 替代 `on_tool_start`/`on_tool_end`：
   ```python
   async for call in stream.tool_calls:
       yield sse_frame({"trace": {"type": "tool_start", "name": call.tool_name, ...}})
       for delta in call.output_deltas:
           yield sse_frame({"token": delta})  # 工具输出流式返回
       yield sse_frame({"trace": {"type": "tool_end", "name": call.tool_name, ...}})
   ```
4. 移除 `chain_names` 栈——v3 不再需要手动跟踪嵌套关系

**优势**：
- 无需手动过滤内部事件（LangGraph/Runnable/Channel）
- 类型化投影提供更好的 IDE 支持
- 代码量减少约 30%

**兼容性**：完全兼容，SSE 帧格式不变

### 第二阶段：子智能体层级感知

引入子智能体（subagent）事件类型，让前端能区分主智能体和子智能体的事件，支持更丰富的 UI 展示。

**修改文件**：
- `backend/src/api/agent/agent_api.py`
- `frontend/src/types/chat.ts`
- `frontend/src/stores/chat.ts`
- `frontend/src/components/TracePanel.vue`

**新增 SSE 数据帧类型**：

```json
{"trace": {"type": "subagent_start", "name": "research-agent", "path": ["task_1"]}}
{"trace": {"type": "subagent_end", "name": "research-agent", "status": "completed"}}
```

**后端改动**（agent_api.py）：

使用 `stream.subagents` 投影，对每个子智能体：
- 发送 `subagent_start` 事件（含 name、path）
- 子智能体的消息通过 `subagent.messages` 消费，token 帧附带 `source` 字段区分来源
- 子智能体的工具调用通过 `subagent.tool_calls` 消费，带 `subagent` 标识
- 发送 `subagent_end` 事件（含 name、status）

**前端改动**：

1. `chat.ts` 类型定义：新增 `subagent_start`、`subagent_end` TraceEventType
2. `TracePanel.vue`：新增子智能体生命周期展示（类似 agent_start/end，但用不同颜色/图标）
3. 子智能体内的工具调用可折叠在子智能体面板下

### 第三阶段：工具输出流式传输 & 推理内容支持

**工具输出流式传输**：

当前工具输出在 `tool_end` 时一次性返回。v3 的 `call.output_deltas` 支持流式返回工具输出：

```json
{"trace": {"type": "tool_output_delta", "name": "search", "delta": "..."}}
```

**推理内容支持**：

当前 DeepSeek 配置中 `thinking` 被禁用。如需支持推理内容，可：

1. 修改 `backend/src/agent/models/llm.py` 中的 `extra_body` 启用 thinking
2. 在 SSE 中新增 `{"reasoning": "..."}` 帧
3. 前端新增推理内容展示（折叠区域，灰色文字）

### 第四阶段：连接管理与取消

当前缺少客户端断开时的处理。

**修改文件**：`backend/src/api/agent/agent_api.py`

**新增**：
1. 检测 `asyncio.CancelledError` / Starlette 的 `request.is_disconnected`
2. 客户端断开时取消 agent 运行（通过 LangGraph 的 cancel 机制）
3. 可选：实现 HTTP/2 server-sent events 或 WebSocket 升级

### 第五阶段：自定义投影（按需）

如果后续需要特定领域的流式事件（如检索进度、记忆加载状态等），可通过自定义 `StreamTransformer` 实现：

```python
from langgraph.streaming import StreamTransformer

class RetrievalProgressTransformer(StreamTransformer):
    # 实现自定义事件投影
    pass

stream = agent.astream_events(
    input, version="v3",
    transformers=[RetrievalProgressTransformer],
)
```

这也可以在 `AgentMiddleware` 中注册 Transformer，通过 `agent_builder.py` 的 `create_deep_agent()` 的 `middleware` 参数注入。

## 实施优先级

| 阶段 | 内容 | 影响范围 | 优先级 |
|------|------|---------|--------|
| 一 | v2 → v3 API 升级 | 仅后端 | **高**（立即） |
| 二 | 子智能体层级感知 | 后端 + 前端 | **高**（立即） |
| 三 | 工具输出流式 + 推理 | 后端 + 前端 | 中 |
| 四 | 连接管理 | 仅后端 | 中 |
| 五 | 自定义投影 | 仅后端 | 低（按需） |

## 实施建议

1. **渐进式升级**：先完成第一阶段（v2→v3），保持 SSE 协议不变，部署验证后再进行第二阶段。
2. **前后端协议**：新增 SSE 帧字段时，前端应忽略未知字段，确保前后端可独立部署。
3. **向后兼容**：旧版 SSE 帧格式在第二阶段可以保留，新增帧通过 `trace.type` 的动态值自然扩展。
4. **测试验证**：每个阶段完成后运行 `tests/integration_tests/test_agent_api.py` 验证。

## 关键文件清单

| 文件 | 职责 | 阶段 |
|------|------|------|
| `backend/src/api/agent/agent_api.py` | SSE 流生成器（核心改动） | 1-4 |
| `backend/src/agent/models/llm.py` | LLM 模型配置（reasoning 开关） | 3 |
| `backend/src/agent/builders/agent_builder.py` | 中间件/Transformer 注入 | 5 |
| `frontend/src/services/request.ts` | SSE 解析器 | 2-3 |
| `frontend/src/types/chat.ts` | 类型定义 | 2-3 |
| `frontend/src/stores/chat.ts` | 事件回调 | 2-3 |
| `frontend/src/components/TracePanel.vue` | Trace 渲染 | 2-3 |
