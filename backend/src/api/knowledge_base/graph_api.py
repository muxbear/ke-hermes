"""知识图谱 API 路由——实体/关系查询 & 重建。"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id, get_db
from api.knowledge_base.graph_service import (
    get_entity_detail,
    get_graph_data,
    rebuild_graph_for_kb,
)
from api.knowledge_base.service import _get_kb_or_404

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
    """重新抽取知识图谱——遍历所有已索引文档，重建实体和关系。"""
    kb = await _get_kb_or_404(db, kb_id, user_id)
    entities_count, relations_count = await rebuild_graph_for_kb(db, kb.config, kb_id)
    await db.commit()
    return {
        "code": 0,
        "data": {
            "entities": entities_count,
            "relations": relations_count,
        },
        "message": "ok",
    }
