"""切片管理 API 路由——查询/更新/删除切片。"""

from fastapi import APIRouter, Request

from api.knowledge_base.chunk_service import (
    batch_operation,
    delete_chunk,
    get_chunk_detail,
    list_chunks,
    update_chunk,
)
from api.knowledge_base.schemas import BatchChunkRequest, ChunkUpdateRequest

router = APIRouter(prefix="/api/knowledge-bases", tags=["知识库-切片"])


def _get_vector_store(request: Request):
    return getattr(request.app.state, "vector_store", None)


def _get_embedding_model(request: Request):
    return getattr(request.app.state, "embedding_model", None)


@router.get("/{kb_id}/documents/{doc_id}/chunks")
async def api_list_chunks(
    kb_id: str,
    doc_id: str,
    request: Request,
    search: str | None = None,
):
    """列出文档所有切片。"""
    vs = _get_vector_store(request)
    if vs is None:
        return {"code": 500, "data": [], "message": "向量库未初始化"}
    chunks = await list_chunks(vs, kb_id, doc_id, search)
    return {"code": 0, "data": [c.model_dump() for c in chunks], "message": "ok"}


@router.get("/{kb_id}/documents/{doc_id}/chunks/{chunk_id}")
async def api_get_chunk_detail(
    kb_id: str,
    doc_id: str,
    chunk_id: str,
    request: Request,
):
    """获取切片详情（含上下文）。"""
    vs = _get_vector_store(request)
    if vs is None:
        return {"code": 500, "data": None, "message": "向量库未初始化"}
    try:
        detail = await get_chunk_detail(vs, kb_id, doc_id, chunk_id)
        return {"code": 0, "data": detail.model_dump(), "message": "ok"}
    except ValueError as e:
        return {"code": 404, "data": None, "message": str(e)}


@router.put("/{kb_id}/documents/{doc_id}/chunks/{chunk_id}")
async def api_update_chunk(
    kb_id: str,
    doc_id: str,
    chunk_id: str,
    body: ChunkUpdateRequest,
    request: Request,
):
    """更新切片内容（重新向量化）。"""
    vs = _get_vector_store(request)
    emb = _get_embedding_model(request)
    if vs is None:
        return {"code": 500, "data": None, "message": "向量库未初始化"}
    if emb is None:
        return {"code": 500, "data": None, "message": "Embedding 模型未初始化"}
    chunk = await update_chunk(vs, emb, kb_id, chunk_id, body.content)
    return {"code": 0, "data": chunk.model_dump(), "message": "ok"}


@router.delete("/{kb_id}/documents/{doc_id}/chunks/{chunk_id}")
async def api_delete_chunk(
    kb_id: str,
    doc_id: str,
    chunk_id: str,
    request: Request,
):
    """删除单个切片。"""
    vs = _get_vector_store(request)
    if vs is None:
        return {"code": 500, "data": None, "message": "向量库未初始化"}
    await delete_chunk(vs, kb_id, chunk_id)
    return {"code": 0, "data": None, "message": "ok"}


@router.post("/{kb_id}/documents/{doc_id}/chunks/batch")
async def api_batch_chunk_operation(
    kb_id: str,
    doc_id: str,
    body: BatchChunkRequest,
    request: Request,
):
    """批量操作：保存或删除切片。"""
    vs = _get_vector_store(request)
    emb = _get_embedding_model(request)
    if vs is None:
        return {"code": 500, "data": None, "message": "向量库未初始化"}
    if emb is None and body.action == "save_all":
        return {"code": 500, "data": None, "message": "Embedding 模型未初始化"}
    result = await batch_operation(vs, emb, kb_id, body)
    return {"code": 0, "data": result, "message": "ok"}
