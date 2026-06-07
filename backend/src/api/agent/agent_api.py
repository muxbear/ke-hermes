import json

from api.conversation.conversation_api import create_conversation
from api.deps import get_current_user_id
from db import get_db
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import StreamingResponse

from langchain_core.messages import HumanMessage
from langchain_core.utils.uuid import uuid7
from pydantic import BaseModel, Field

from agent.context.context import Context
from agent import get_graph
from sqlalchemy.ext.asyncio import AsyncSession

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
    config = {"configurable": {"thread_id": thread_id}}
    context = Context(server_info="ke_hermes_server", user_id=user_id) # 用 JWT 提取的 user_id 替换 req.user_id 

    result = await get_graph().ainvoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config,
        context=context
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
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)):
    is_new = not req.thread_id
    thread_id = req.thread_id or str(uuid7())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    context = Context(server_info="ke_hermes_server", user_id=user_id)

    async def event_generator():
        chain_names: list[str] = []

        async for event in get_graph().astream_events(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
            context=context,
            version="v2",
        ):
            kind = event["event"]
            name = event.get("name", "")

            if kind == "on_chat_model_stream":
                token = event["data"]["chunk"].text
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"

            elif kind == "on_chain_start":
                if name and not name.startswith(("LangGraph", "Runnable", "Channel")):
                    chain_names.append(name)
                    yield f"data: {json.dumps({'trace': {'type': 'agent_start', 'name': name}})}\n\n"

            elif kind == "on_chain_end":
                if chain_names and name == chain_names[-1]:
                    chain_names.pop()
                    yield f"data: {json.dumps({'trace': {'type': 'agent_end', 'name': name}})}\n\n"

            elif kind == "on_tool_start":
                parent_agent = chain_names[-1] if chain_names else "main"
                tool_input = event["data"].get("input", {})
                input_str = json.dumps(tool_input, ensure_ascii=False, default=str)
                yield f"data: {json.dumps({'trace': {'type': 'tool_start', 'name': name, 'agent': parent_agent, 'input': input_str}})}\n\n"

            elif kind == "on_tool_end":
                parent_agent = chain_names[-1] if chain_names else "main"
                tool_output = event["data"].get("output", "")
                output_str = str(tool_output) if tool_output is not None else ""
                yield f"data: {json.dumps({'trace': {'type': 'tool_end', 'name': name, 'agent': parent_agent, 'output': output_str}})}\n\n"

        yield f"data: {json.dumps({'thread_id': thread_id})}\n\n"

        if is_new:
            await create_conversation(db, user_id, thread_id, req.message)

    return StreamingResponse(event_generator(), media_type="text/event-stream")