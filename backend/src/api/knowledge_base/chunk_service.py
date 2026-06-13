"""切片业务逻辑——查询/更新/删除文档切片。"""

import logging

from api.knowledge_base.schemas import (
    BatchChunkRequest,
    ChunkDetailResponse,
    ChunkResponse,
)
from core.rag.vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


def _build_chunk_response(raw: dict, fallback_index: int = 0) -> ChunkResponse:
    """将 Milvus 原始记录转为前端 ChunkResponse。"""
    text = raw.get("chunk_text", "")
    meta = raw.get("metadata_", {}) or {}
    return ChunkResponse(
        id=raw.get("id", ""),
        index=raw.get("chunk_index", fallback_index),
        content=text,
        token_count=max(1, len(text) // 2),
        char_count=len(text),
        page_ref=meta.get("page", meta.get("page_ref", "")),
        section=meta.get("section", meta.get("h1", meta.get("h2", ""))),
        entities=meta.get("entities", []),
    )


async def list_chunks(
    vector_store: BaseVectorStore,
    kb_id: str,
    doc_id: str,
    search: str | None = None,
) -> list[ChunkResponse]:
    """列出文档所有切片，支持本地搜索过滤。"""
    raws = await vector_store.get_chunks_by_doc_id(kb_id, doc_id)
    chunks = [_build_chunk_response(r) for r in raws]

    if search:
        q = search.lower()
        chunks = [
            c for c in chunks
            if q in c.content.lower() or q in c.section.lower()
        ]

    return chunks


async def get_chunk_detail(
    vector_store: BaseVectorStore,
    kb_id: str,
    doc_id: str,
    chunk_id: str,
) -> ChunkDetailResponse:
    """获取切片详情 + 上下文（前一/后一切片）。"""
    all_raws = await vector_store.get_chunks_by_doc_id(kb_id, doc_id)

    target: dict | None = None
    prev_raw: dict | None = None
    next_raw: dict | None = None

    for i, r in enumerate(all_raws):
        if r.get("id") == chunk_id:
            target = r
            if i > 0:
                prev_raw = all_raws[i - 1]
            if i < len(all_raws) - 1:
                next_raw = all_raws[i + 1]
            break

    if target is None:
        raise ValueError(f"Chunk not found: {chunk_id}")

    return ChunkDetailResponse(
        chunk=_build_chunk_response(target),
        prev_chunk=_build_chunk_response(prev_raw) if prev_raw else None,
        next_chunk=_build_chunk_response(next_raw) if next_raw else None,
    )


async def update_chunk(
    vector_store: BaseVectorStore,
    embedding_model,
    kb_id: str,
    chunk_id: str,
    content: str,
) -> ChunkResponse:
    """更新切片内容 → 重新向量化 → 更新 Milvus。"""
    new_embedding = (await embedding_model.aembed_documents([content]))[0]
    await vector_store.update_chunk(kb_id, chunk_id, content, new_embedding)
    return ChunkResponse(
        id=chunk_id,
        index=0,
        content=content,
        token_count=max(1, len(content) // 2),
        char_count=len(content),
    )


async def delete_chunk(
    vector_store: BaseVectorStore,
    kb_id: str,
    chunk_id: str,
) -> None:
    """删除单个切片。"""
    await vector_store.delete_chunk_by_id(kb_id, chunk_id)


async def batch_operation(
    vector_store: BaseVectorStore,
    embedding_model,
    kb_id: str,
    req: BatchChunkRequest,
) -> dict:
    """批量操作：保存所有编辑 或 批量删除。"""
    if req.action == "save_all":
        saved = 0
        for ch in req.chunks:
            chunk_id = ch.get("id", "")
            content = ch.get("content", "")
            if chunk_id and content:
                await update_chunk(
                    vector_store, embedding_model, kb_id, chunk_id, content,
                )
                saved += 1
        return {"saved": saved, "deleted": 0}

    if req.action == "delete":
        deleted = 0
        for chunk_id in req.chunk_ids:
            if chunk_id:
                await delete_chunk(vector_store, kb_id, chunk_id)
                deleted += 1
        return {"saved": 0, "deleted": deleted}

    raise ValueError(f"Unknown batch action: {req.action}")
