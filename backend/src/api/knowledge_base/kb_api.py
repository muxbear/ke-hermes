"""知识库 API 路由——CRUD + 概览统计。"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id, get_db
from api.knowledge_base.schemas import (
    IndexConfigSchema,
    KBCreateRequest,
    KBListResponse,
    KBResponse,
    KBStatsResponse,
    KBUpdateRequest,
)
from api.knowledge_base.service import (
    create_kb,
    delete_kb,
    get_indexing_activity,
    get_kb,
    get_kb_stats,
    list_kbs,
    reindex_kb,
    update_kb,
)

router = APIRouter(prefix="/api/knowledge-bases", tags=["知识库"])


def _get_vector_store(request: Request):
    """从 app state 获取向量数据库实例。"""
    return getattr(request.app.state, "vector_store", None)


@router.get("", response_model=dict)
async def list_knowledge_bases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """获取知识库列表（分页 + 模糊搜索）。"""
    result = await list_kbs(db, user_id, page=page, page_size=page_size, search=search)
    return {
        "code": 0,
        "data": result.model_dump(),
        "message": "ok",
    }


@router.get("/stats", response_model=dict)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """获取知识库统计信息。"""
    result = await get_kb_stats(db, user_id)
    return {"code": 0, "data": result.model_dump(), "message": "ok"}


@router.get("/available-models", response_model=dict)
async def get_available_models(
    model_type: str = "llm",
    provider_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
):
    """获取可用于知识库的模型列表，可按 provider 筛选。

    model_type: llm（实体/关系抽取）或 embedding（向量化）
    provider_id: 指定则只返回该提供商下的模型
    """
    from sqlalchemy import select
    from db.models.ai_model import AIModel

    conditions = [
        AIModel.type == model_type,
        AIModel.status == "active",
    ]
    if provider_id:
        conditions.append(AIModel.provider_id == provider_id)

    stmt = select(AIModel).where(*conditions)
    rows = (await db.execute(stmt)).scalars().all()

    models = [
        {
            "id": m.id,
            "name": m.name,
            "display_name": m.display_name,
            "type": m.type,
            "provider_id": m.provider_id,
        }
        for m in rows
    ]
    return {"code": 0, "data": models, "message": "ok"}


@router.get("/available-providers", response_model=dict)
async def get_available_providers(
    model_type: str = Query(default="llm"),
    db: AsyncSession = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
):
    """获取拥有指定类型模型的提供商列表。

    model_type: llm（实体/关系抽取）或 embedding（向量化）
    返回的每个 provider 带有一个简化的 models 列表。
    """
    from sqlalchemy import select
    from db.models.ai_model import AIModel
    from db.models.provider import Provider

    # 找出有该类活跃模型的 provider_id
    sub_stmt = select(AIModel.provider_id).where(
        AIModel.type == model_type,
        AIModel.status == "active",
    ).distinct()
    provider_ids = (await db.execute(sub_stmt)).scalars().all()

    if not provider_ids:
        return {"code": 0, "data": [], "message": "ok"}

    # 查出这些 provider
    prov_stmt = select(Provider).where(Provider.id.in_(provider_ids))
    providers = (await db.execute(prov_stmt)).scalars().all()

    # 查出这些 provider 下所有该类活跃模型
    model_stmt = select(AIModel).where(
        AIModel.provider_id.in_(provider_ids),
        AIModel.type == model_type,
        AIModel.status == "active",
    )
    models = (await db.execute(model_stmt)).scalars().all()

    # 按 provider_id 分组
    models_by_provider: dict[str, list[dict]] = {}
    for m in models:
        models_by_provider.setdefault(m.provider_id, []).append({
            "id": m.id,
            "name": m.name,
            "display_name": m.display_name,
            "type": m.type,
        })

    result = [
        {
            "id": p.id,
            "name": p.name,
            "logo": p.logo,
            "models": models_by_provider.get(p.id, []),
        }
        for p in providers
    ]
    return {"code": 0, "data": result, "message": "ok"}


@router.post("", response_model=dict, status_code=201)
async def create_knowledge_base(
    body: KBCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """创建知识库。"""
    vector_store = _get_vector_store(request)
    result = await create_kb(db, user_id, body, vector_store)
    await db.commit()
    return {"code": 0, "data": result.model_dump(), "message": "ok"}


@router.get("/{kb_id}", response_model=dict)
async def get_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """获取知识库详情。"""
    result = await get_kb(db, kb_id, user_id)
    return {"code": 0, "data": result.model_dump(), "message": "ok"}


@router.put("/{kb_id}", response_model=dict)
async def update_knowledge_base(
    kb_id: str,
    body: KBUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """更新知识库。"""
    result = await update_kb(db, kb_id, user_id, body)
    await db.commit()
    return {"code": 0, "data": result.model_dump(), "message": "ok"}


@router.delete("/{kb_id}", response_model=dict)
async def delete_knowledge_base(
    kb_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """删除知识库。"""
    vector_store = _get_vector_store(request)
    await delete_kb(db, kb_id, user_id, vector_store)
    await db.commit()
    return {"code": 0, "data": None, "message": "ok"}


@router.get("/{kb_id}/indexing-activity", response_model=dict)
async def get_index_activity(
    kb_id: str,
    limit: int = Query(default=5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """获取最近索引活动。"""
    result = await get_indexing_activity(db, kb_id, user_id, limit)
    return {"code": 0, "data": result, "message": "ok"}


@router.post("/{kb_id}/reindex", response_model=dict)
async def reindex_knowledge_base(
    kb_id: str,
    request: Request,
    body: IndexConfigSchema,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """保存索引配置并重新索引知识库中的所有文档。"""
    vector_store = _get_vector_store(request)

    from api.knowledge_base.doc_service import IndexingScheduler
    scheduler = IndexingScheduler.instance()

    result = await reindex_kb(
        db, kb_id, user_id,
        config=body,
        vector_store=vector_store,
        scheduler=scheduler,
    )
    await db.commit()
    return {"code": 0, "data": result, "message": "ok"}
