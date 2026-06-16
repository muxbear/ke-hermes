"""文档管理 API 路由——上传/列表/详情/删除/重试。"""

from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id, get_db
from api.knowledge_base.doc_service import (
    delete_document,
    get_document,
    list_documents,
    retry_document,
    upload_documents,
)

router = APIRouter(prefix="/api/knowledge-bases", tags=["知识库-文档"])


def _get_scheduler(request: Request):
    return getattr(request.app.state, "scheduler", None)


def _get_vector_store(request: Request):
    return getattr(request.app.state, "vector_store", None)


@router.post("/{kb_id}/documents/upload", response_model=dict)
async def upload_docs(
    kb_id: str,
    request: Request,
    files: list[UploadFile] = File(..., max_count=20),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """向指定知识库批量上传文档（最多 20 个），落盘、写库，并异步触发索引流水线。"""
    if not files:
        return {"code": 400, "data": None, "message": "请选择文件"}

    scheduler = _get_scheduler(request)
    result = await upload_documents(db, kb_id, user_id, files, scheduler)
    await db.commit()
    return {
        "code": 0,
        "data": [r.model_dump(mode="json") for r in result],
        "message": "ok",
    }


@router.get("/{kb_id}/documents", response_model=dict)
async def list_docs(
    kb_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """获取文档列表。"""
    result = await list_documents(db, kb_id, user_id, page, page_size, search, status)
    return {"code": 0, "data": result, "message": "ok"}


@router.get("/{kb_id}/documents/{doc_id}", response_model=dict)
async def get_doc(
    kb_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """获取文档详情（含索引流水线状态）。"""
    result = await get_document(db, kb_id, doc_id, user_id)
    return {"code": 0, "data": result.model_dump(mode="json"), "message": "ok"}


@router.delete("/{kb_id}/documents/{doc_id}", response_model=dict)
async def delete_doc(
    kb_id: str,
    doc_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """删除文档。"""
    vector_store = _get_vector_store(request)
    await delete_document(db, kb_id, doc_id, user_id, vector_store)
    await db.commit()
    return {"code": 0, "data": None, "message": "ok"}


@router.post("/{kb_id}/documents/{doc_id}/retry", response_model=dict)
async def retry_doc(
    kb_id: str,
    doc_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """重试失败文档。"""
    scheduler = _get_scheduler(request)
    result = await retry_document(db, kb_id, doc_id, user_id, scheduler)
    await db.commit()
    return {"code": 0, "data": result.model_dump(mode="json"), "message": "ok"}
