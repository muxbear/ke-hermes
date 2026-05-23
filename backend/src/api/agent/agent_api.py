import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langchain_core.utils.uuid import uuid7
from pydantic import BaseModel, Field

from agent.context.context import Context
from agent import get_graph

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
async def chat(req: ChatRequest):
    thread_id = req.thread_id or str(uuid7())
    config = {"configurable": {"thread_id": thread_id}}
    context = Context(user_id=req.user_id)

    result = await get_graph().ainvoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config,
        context=context
    )

    final_message = result["messages"][-1]
    return ChatResponse(
        response=final_message.content, 
        thread_id=thread_id
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    thread_id = req.thread_id or str(uuid7())
    config = {"configurable": {"thread_id": thread_id}}
    context = Context(user_id=req.user_id)
    print(f"上下文 Context: {context}")

    async def event_generator():
        async for event in get_graph().astream_events(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
            context=context,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].text
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"

        yield f"data: {json.dumps({'thread_id': thread_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")