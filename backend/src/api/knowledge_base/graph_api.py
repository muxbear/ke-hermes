"""知识图谱 API 路由——实体/关系查询 & 重建。"""

import logging
import os

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id, get_db
from api.knowledge_base.graph_service import (
    GraphExtractionService,
    get_entity_detail,
    get_graph_data,
)
from api.knowledge_base.service import _get_kb_or_404
from core.rag.loaders import create_default_loader_registry
from core.rag.splitters import create_chunk_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-bases", tags=["知识库-图谱"])


@router.get("/{kb_id}/graph", response_model=dict)
async def get_graph(
    kb_id: str,
    entity_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """获取知识图谱数据（实体 + 关系）。"""
    await _get_kb_or_404(db, kb_id, user_id)
    result = await get_graph_data(db, kb_id, entity_type)
    return {"code": 0, "data": result, "message": "ok"}


@router.get("/{kb_id}/graph/entities/{entity_id}", response_model=dict)
async def get_entity(
    kb_id: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """获取实体详情。"""
    result = await get_entity_detail(db, kb_id, entity_id)
    if result is None:
        return {"code": 404, "data": None, "message": "实体不存在"}
    return {"code": 0, "data": result, "message": "ok"}


@router.post("/{kb_id}/graph/re-extract", response_model=dict)
async def re_extract_graph(
    kb_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """重新抽取知识图谱——遍历所有已索引文档，重建实体和关系。

    先清除该 KB 下的旧实体和关系，再对所有文档逐个重新抽取。
    """
    kb = await _get_kb_or_404(db, kb_id, user_id)

    # 清除旧数据
    await db.execute(
        text("DELETE FROM knowledge_base_relations WHERE kb_id = :kb_id"), {"kb_id": kb_id}
    )
    await db.execute(
        text("DELETE FROM knowledge_base_entities WHERE kb_id = :kb_id"), {"kb_id": kb_id}
    )
    await db.commit()

    # 获取所有已索引文档
    from db.models.knowledge_base_document import KnowledgeBaseDocument
    doc_rows = (await db.execute(
        select(KnowledgeBaseDocument).where(
            KnowledgeBaseDocument.kb_id == kb_id,
            KnowledgeBaseDocument.status == "indexed",
        )
    )).scalars().all()

    if not doc_rows:
        return {"code": 0, "data": {"entities": 0, "relations": 0}, "message": "没有已索引的文档"}

    # 加载文档内容并抽取
    loader_registry = create_default_loader_registry()
    chunk_registry = create_chunk_registry(kb.config)
    extractor = GraphExtractionService()

    total_entities = 0
    total_relations = 0

    for doc in doc_rows:
        if not doc.storage_path or not os.path.exists(doc.storage_path):
            logger.warning("File not found for re-extract: %s", doc.storage_path)
            continue

        try:
            documents = loader_registry.load(doc.storage_path, doc.type)
            chunks = chunk_registry.split("recursive", documents)
            entities, relations = await extractor.extract_entities_and_relations(
                kb_id, doc.id, chunks,
            )
            total_entities += len(entities)
            total_relations += len(relations)
        except Exception as e:
            logger.error("Re-extract failed for doc=%s: %s", doc.id, e)
            continue

    # 更新 KB 计数
    result = await get_graph_data(db, kb_id)
    kb.entities_count = len(result["entities"])
    kb.relations_count = len(result["relations"])

    return {
        "code": 0,
        "data": {
            "entities": total_entities,
            "relations": total_relations,
            "docs_processed": len(doc_rows),
        },
        "message": "ok",
    }
