from agent import get_checkpointer
from api.deps import get_current_user_id
from db import get_db
from db.models import Conversation
from fastapi import APIRouter, Depends, HTTPException

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel


router = APIRouter(prefix="/api", tags=["conversations"])

# ---- 辅助函数 ----
def _message_to_dict(msg) -> dict:
    """
    这段代码是一个‌适配器函数（Adapter Function）‌，其主要目的是将 ‌LangChain‌ 框架中复杂的消息对象（如 HumanMessage, AIMessage 等）
    转换为一种通用的、轻量级的字典格式 {"role": ..., "content": ...}
    """
    type_map = {
        SystemMessage: "system",
        HumanMessage: "user",
        AIMessage: "assistant",
        ToolMessage: "tool"
    }
    role = "unknow"
    for msg_type, name in type_map.items():
        if isinstance(msg, msg_type):
            role = name
            break
    # 过滤掉 tool 消息(前端不展示)
    content = getattr(msg, "content", "")
    return {"role": role, "content": str(content) if content else ""}

async def create_conversation(
    db: AsyncSession,
    user_id: str,
    thread_id: str,
    title: str
):
    """创建对话记录. 供 chat 端点在新对话时调用"""
    import uuid

    conv = Conversation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        thread_id=thread_id,
        title=title[:30] if len(title) > 30 else title,
    )

    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


# ---- Response schemas ----
class ConversationItem(BaseModel):
    thread_id: str
    title: str
    updated_at: str

class MessageItem(BaseModel):
    role: str
    content: str    

class ConversationDetail(BaseModel):
    thread_id: str
    title: str
    messages: list[MessageItem]

class RenameRequest(BaseModel):
    title: str

# ---- 端点 ----

@router.get("/conversations")
async def list_conversations(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的对话列表, 按更新时间倒序"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    return {
        "code": 0,
        "data": [
            {
                "thread_id": c.thread_id,
                "title": c.title,
                "updated_at": c.updated_at.isoformat() if c.updated_at else "",
            }
            for c in conversations
        ],
    }

@router.get("/conversations/{thread_id}")
async def conversations(
    user_id: str = Depends(get_current_user_id),
    thread_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """获取某个对话的消息列表"""
    # 1. 查询 Conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.thread_id == thread_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denies")

    # 2. 从 graph state 获取消息（DeltaChannel 需 aget_state 重建）
    config = {"configurable": {"thread_id": thread_id}}
    from agent import get_graph
    state = await get_graph().aget_state(config)
    raw_messages: list = state.values.get("messages", []) if (state and state.values) else []
    messages = [_message_to_dict(m) for m in raw_messages]

    return {
        "code": 0,
        "data": {
            "thread_id": thread_id,
            "title": conv.title,
            "messages": messages,
        },
    }


@router.patch("/conversations/{thread_id}")
async def rename_conversations(
    thread_id: str,
    req: RenameRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """重命名对话"""
    # 1. 查询 Conversation 确认归属
    result = await db.execute(
        select(Conversation).where(Conversation.thread_id == thread_id)
    )

    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    conv.title = req.title[:255]
    await db.commit()

    return {
        "code": 0,
        "data": {
            "thread_id": thread_id,
            "title": conv.title
        }
    }

@router.delete("/conversations/{thread_id}")
async def delete_conversation(
    thread_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除对话记录(DB 记录 + LangGraph checkpoints)."""
    # 1. 查 Conversation 确认归属
    result = await db.execute(
        select(Conversation).where(Conversation.thread_id == thread_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    # 2. 先删除 checkpoints (避免删除了 DB 但 checkpoint 残留)
    try:
        checkpointer = get_checkpointer()
        await checkpointer.adelete_thread(thread_id)
    except Exception:
        # checkpoint 可能不存在(新对话还没消息), 忽略错误
        pass

    # 3. 删除 DB 记录
    await db.delete(conv)
    await db.commit()

    return {
        "code": 0,
        "data": None
    }