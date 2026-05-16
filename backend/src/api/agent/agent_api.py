import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from agent import graph

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    response: str


class StreamToken(BaseModel):
    token: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=req.message)]}
    )
    final_message = result["messages"][-1]
    return ChatResponse(response=final_message.content)


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