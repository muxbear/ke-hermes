"""知识库检索 API 路由——向量 / BM25 / 混合检索."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id, get_db
from api.knowledge_base.schemas import SearchRequest, SearchResponse
from api.knowledge_base.service import _get_kb_or_404

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-bases", tags=["知识库-检索"])


@router.post("/{kb_id}/search", response_model=dict)
async def search_knowledge_base(
    kb_id: str,
    req_body: SearchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """在知识库中检索内容。

    支持三种检索模式:
    - hybrid: 混合检索（向量 + BM25 融合，alpha 控制权重）
    - vector: 纯向量语义检索
    - bm25: 纯关键词检索
    """
    await _get_kb_or_404(db, kb_id, user_id)

    orchestrator = request.app.state.search_orchestrator
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="检索服务未就绪")

    try:
        result: SearchResponse = await orchestrator.search(db, kb_id, req_body)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception:
        logger.exception("Unhandled search error for kb=%s", kb_id)
        raise HTTPException(status_code=500, detail="检索服务内部错误") from None

    return {"code": 0, "data": result.model_dump(), "message": "ok"}
