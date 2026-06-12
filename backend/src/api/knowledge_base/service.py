"""知识库业务逻辑——CRUD + 统计。"""

import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.knowledge_base.schemas import (
    KBCreateRequest,
    KBListResponse,
    KBResponse,
    KBStatsResponse,
    KBUpdateRequest,
    IndexConfigSchema,
)
from core.rag.vector_store import BaseVectorStore
from db.models.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

STAGE_NAMES = ["排队", "解析", "切片", "向量化", "BM25 倒排", "实体抽取", "关系抽取", "入库"]


def _format_bytes(size_bytes: int) -> str:
    """将字节数格式化为人类可读字符串。"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    for unit in ["KB", "MB", "GB", "TB"]:
        size_bytes /= 1024
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
    return f"{size_bytes:.1f} PB"


def _kb_to_response(kb: KnowledgeBase) -> KBResponse:
    """ORM 模型 → 响应对象。"""
    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        status=kb.status,
        docs_count=kb.docs_count,
        chunks_count=kb.chunks_count,
        entities_count=kb.entities_count,
        relations_count=kb.relations_count,
        size_bytes=kb.size_bytes,
        size_display=_format_bytes(kb.size_bytes),
        tags=kb.tags,
        config=IndexConfigSchema(**kb.config) if kb.config else IndexConfigSchema(),
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


async def list_kbs(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 12,
    search: str | None = None,
) -> KBListResponse:
    """获取知识库列表（分页 + 模糊搜索）。"""
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    conditions = [KnowledgeBase.user_id == user_id]
    if search:
        pattern = f"%{search}%"
        conditions.append(
            text("knowledge_bases.name ILIKE :q OR knowledge_bases.description ILIKE :q")
        )

    # Total count
    total_stmt = select(func.count()).select_from(KnowledgeBase).where(*conditions)
    if search:
        total_stmt = total_stmt.params(q=pattern)
    total = (await db.execute(total_stmt)).scalar() or 0

    # Items
    stmt = (
        select(KnowledgeBase)
        .where(*conditions)
        .order_by(KnowledgeBase.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if search:
        stmt = stmt.params(q=pattern)
    rows = (await db.execute(stmt)).scalars().all()

    return KBListResponse(
        items=[_kb_to_response(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_kb_stats(db: AsyncSession, user_id: str) -> KBStatsResponse:
    """获取知识库统计信息。"""
    base = select(
        func.coalesce(func.sum(KnowledgeBase.docs_count), 0),
        func.coalesce(func.sum(KnowledgeBase.chunks_count), 0),
        func.coalesce(func.sum(KnowledgeBase.entities_count), 0),
        func.count(KnowledgeBase.id),
    ).where(KnowledgeBase.user_id == user_id)
    result = (await db.execute(base)).one()
    total_docs, total_chunks, total_entities, total_kbs = result

    indexing_count = (
        await db.execute(
            select(func.count())
            .select_from(KnowledgeBase)
            .where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.status == "indexing",
            )
        )
    ).scalar() or 0

    return KBStatsResponse(
        total_kbs=total_kbs,
        total_docs=total_docs,
        total_chunks=total_chunks,
        total_entities=total_entities,
        total_indexing=indexing_count,
    )


async def create_kb(
    db: AsyncSession,
    user_id: str,
    req: KBCreateRequest,
    vector_store: BaseVectorStore | None = None,
) -> KBResponse:
    """创建知识库。"""
    # Check name uniqueness
    existing = (
        await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.name == req.name,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"知识库 '{req.name}' 已存在")

    kb = KnowledgeBase(
        name=req.name,
        description=req.description,
        tags=req.tags,
        config=req.config.model_dump(),
        user_id=user_id,
        status="draft",
    )
    db.add(kb)
    await db.flush()

    # Create vector DB collection
    if vector_store:
        dim = req.config.embedding_dim
        try:
            await vector_store.create_collection(kb.id, dim)
        except Exception as e:
            logger.error("Failed to create vector collection for kb=%s: %s", kb.id, e)

    return _kb_to_response(kb)


async def get_kb(db: AsyncSession, kb_id: str, user_id: str) -> KBResponse:
    """获取知识库详情。"""
    kb = await _get_kb_or_404(db, kb_id, user_id)
    return _kb_to_response(kb)


async def update_kb(
    db: AsyncSession, kb_id: str, user_id: str, req: KBUpdateRequest,
) -> KBResponse:
    """更新知识库。"""
    kb = await _get_kb_or_404(db, kb_id, user_id)

    update_data = req.model_dump(exclude_none=True)
    if "config" in update_data and update_data["config"] is not None:
        update_data["config"] = update_data["config"].model_dump()

    for key, value in update_data.items():
        if value is not None:
            setattr(kb, key, value)

    kb.updated_at = datetime.utcnow()
    await db.flush()
    return _kb_to_response(kb)


async def delete_kb(
    db: AsyncSession,
    kb_id: str,
    user_id: str,
    vector_store: BaseVectorStore | None = None,
) -> None:
    """删除知识库——级联删除文档、实体、关系和向量数据。"""
    kb = await _get_kb_or_404(db, kb_id, user_id)

    # Delete vector DB collection
    if vector_store:
        try:
            await vector_store.delete_collection(kb_id)
        except Exception as e:
            logger.error("Failed to delete vector collection kb=%s: %s", kb_id, e)

    # Delete related records
    for table in ["knowledge_base_documents", "knowledge_base_entities", "knowledge_base_relations"]:
        await db.execute(text(f"DELETE FROM {table} WHERE kb_id = :kb_id"), {"kb_id": kb_id})

    await db.delete(kb)


async def get_indexing_activity(
    db: AsyncSession, kb_id: str, user_id: str, limit: int = 5,
) -> list:
    """获取最近索引活动。"""
    from db.models.knowledge_base_document import KnowledgeBaseDocument

    await _get_kb_or_404(db, kb_id, user_id)
    stmt = (
        select(KnowledgeBaseDocument)
        .where(KnowledgeBaseDocument.kb_id == kb_id)
        .order_by(KnowledgeBaseDocument.uploaded_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": r.id, "name": r.name, "status": r.status,
            "progress": r.progress, "uploaded_at": r.uploaded_at.isoformat(),
        }
        for r in rows
    ]


def compute_stages(status: str, progress: int) -> list[dict]:
    """根据文档状态和进度计算 8 阶段状态。"""
    status_order = [
        "queued", "parsing", "chunking", "embedding", "bm25", "extracting", "indexed",
    ]
    stages = []
    current_idx = status_order.index(status) if status in status_order else -1

    for i, name in enumerate(STAGE_NAMES):
        if i < current_idx:
            stages.append({"name": name, "status": "done", "pct": 100})
        elif i == current_idx:
            pct = max(0, progress) if progress >= 0 else 0
            stages.append({"name": name, "status": "running" if pct < 100 else "done", "pct": pct})
        else:
            stages.append({"name": name, "status": "pending", "pct": 0})

    if status == "failed":
        # Mark the current stage as failed
        failed_idx = min(current_idx, len(stages) - 1) if current_idx >= 0 else 0
        stages[failed_idx]["status"] = "failed"

    return stages


async def _get_kb_or_404(db: AsyncSession, kb_id: str, user_id: str) -> KnowledgeBase:
    """获取知识库或抛出 404。"""
    kb = (
        await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb
