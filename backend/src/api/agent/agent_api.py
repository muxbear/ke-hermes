import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.utils.uuid import uuid7
from openai import BadRequestError
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent import get_graph
from agent.context.context import Context
from api.conversation.conversation_api import create_conversation
from api.deps import get_current_user_id
from db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    user_id: str | None = 'user_123' # TODO
    thread_id: str | None = None
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    thread_id: str
    response: str


class StreamToken(BaseModel):
    token: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    is_new = not req.thread_id
    thread_id = req.thread_id or str(uuid7())
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    context = Context(
        server_info="ke_hermes_server",
        user_id=user_id,
        org_id="default-org",  # TODO: 从 JWT claims 或 User 表读取真实 org_id
    )

    try:
        result = await get_graph().ainvoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
            context=context
        )
    except BadRequestError as e:
        logger.warning("Model returned BadRequestError: %s", e)
        return ChatResponse(
            response="抱歉，您的请求被模型安全审核拦截，请尝试换一种表述方式。",
            thread_id=thread_id,
        )
    except Exception:
        logger.exception("Agent encountered an unhandled error")
        return ChatResponse(
            response="抱歉，服务处理您的请求时发生了错误，请稍后重试。",
            thread_id=thread_id,
        )

    # 新对话自动创建记录
    if is_new:
        await create_conversation(db, user_id, thread_id, req.message)

    final_message = result["messages"][-1]
    return ChatResponse(
        response=final_message.content,
        thread_id=thread_id
    )


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)):
    is_new = not req.thread_id
    thread_id = req.thread_id or str(uuid7())
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    context = Context(
        server_info="ke_hermes_server",
        user_id=user_id,
        org_id="default-org",  # TODO: 从 JWT claims 或 User 表读取真实 org_id
    )

    async def event_generator():
        queue: asyncio.Queue[dict | None] = asyncio.Queue()

        async def consume_all() -> None:
            try:
                stream = await get_graph().astream_events(
                    {"messages": [HumanMessage(content=req.message)]},
                    config=config,
                    context=context,
                    version="v3",
                )

                async def consume_messages() -> None:
                    async for message in stream.messages:
                        async for delta in message.reasoning:
                            await queue.put({"reasoning": delta})
                        async for delta in message.text:
                            await queue.put({"token": delta})

                async def consume_tool_calls() -> None:
                    async for call in stream.tool_calls:
                        input_str = json.dumps(call.input, ensure_ascii=False, default=str)
                        await queue.put({
                            "trace": {
                                "type": "tool_start",
                                "name": call.tool_name,
                                "agent": "main",
                                "input": input_str,
                            }
                        })
                        async for delta in call.output_deltas:
                            await queue.put({"token": str(delta)})
                        output_str = str(call.output) if call.output is not None else ""
                        error_str = str(call.error) if call.error is not None else ""
                        await queue.put({
                            "trace": {
                                "type": "tool_end",
                                "name": call.tool_name,
                                "agent": "main",
                                "output": error_str or output_str,
                            }
                        })

                async def consume_subagents() -> None:
                    async for subagent in stream.subagents:
                        await queue.put({
                            "trace": {
                                "type": "subagent_start",
                                "name": subagent.name,
                            }
                        })
                        try:
                            async for message in subagent.messages:
                                async for delta in message.reasoning:
                                    await queue.put({"reasoning": delta})
                                async for delta in message.text:
                                    await queue.put({"token": delta})
                        except Exception as e:
                            subagent_error = getattr(subagent, "error", None) or str(e)
                            subagent_status = getattr(subagent, "status", "failed")
                            logger.warning(
                                "Subagent '%s' failed — status=%s, error=%s",
                                subagent.name, subagent_status, subagent_error,
                            )
                            await queue.put({
                                "trace": {
                                    "type": "subagent_end",
                                    "name": subagent.name,
                                    "status": subagent_status,
                                    "error": subagent_error,
                                }
                            })
                            continue
                        await queue.put({
                            "trace": {
                                "type": "subagent_end",
                                "name": subagent.name,
                                "status": subagent.status,
                            }
                        })

                results = await asyncio.gather(
                    consume_messages(), consume_tool_calls(), consume_subagents(),
                    return_exceptions=True,
                )
                for result in results:
                    if isinstance(result, BadRequestError):
                        raise result
                    if isinstance(result, BaseException):
                        logger.warning("Stream consumer aborted: %s", result)
            except BadRequestError as e:
                logger.warning("Model returned BadRequestError in stream: %s", e)
                await queue.put({"error": "抱歉，您的请求被模型安全审核拦截，请尝试换一种表述方式。"})
            except Exception:
                logger.exception("Agent stream encountered an unhandled error")
                await queue.put({"error": "抱歉，服务处理您的请求时发生了错误，请稍后重试。"})
            finally:
                await queue.put(None)

        consumer = asyncio.create_task(consume_all())

        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=0.5)
                except TimeoutError:
                    if await request.is_disconnected():
                        logger.info("Client disconnected, cancelling agent stream")
                        consumer.cancel()
                        break
                    continue
                if item is None:
                    break
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            logger.info("Stream generator cancelled, cleaning up consumer")
            consumer.cancel()
            raise

        await consumer

        yield f"data: {json.dumps({'thread_id': thread_id})}\n\n"

        if is_new:
            try:
                await create_conversation(db, user_id, thread_id, req.message)
            except Exception:
                logger.exception("Failed to create conversation record")

    return StreamingResponse(event_generator(), media_type="text/event-stream")