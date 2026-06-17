"""知识库检索工具——供 Agent 在对话中搜索已索引的知识库内容。"""

import asyncio
from typing import Any


def kb_search(
    query: str,
    kb_id: str = "",
    kb_name: str = "",
    mode: str = "hybrid",
    top_k: int = 5,
) -> dict[str, Any]:
    """搜索知识库中的内容，支持混合检索、向量检索和 BM25 关键词检索。

    调用前请先用 list_knowledge_bases 获取可用的知识库列表，再传入正确的 kb_id。
    如果不知道 kb_id，可以传入 kb_name 按名称匹配。

    Args:
        query: 搜索查询，使用关键词而非完整句子。
        kb_id: 知识库 ID（优先使用）。不知道时传空字符串，通过 kb_name 匹配。
        kb_name: 知识库名称（模糊匹配）。仅 kb_id 为空时生效。
        mode: 检索模式，"hybrid"（RRF 混合，推荐）、"vector"（语义）、"bm25"（关键词）。
        top_k: 返回结果数量，默认 5。

    Returns:
        {"total": int, "results": [{"doc": str, "content": str, "score": float, ...}]}
        如果 kb_id 无效，返回 {"error": str, "available_kbs": [...]}
    """
    return asyncio.run(_kb_search_async(query, kb_id, kb_name, mode, top_k))


async def _kb_search_async(
    query: str, kb_id: str, kb_name: str, mode: str, top_k: int
) -> dict[str, Any]:
    from api.knowledge_base.schemas import SearchRequest
    from api.knowledge_base.search_service import get_search_orchestrator
    from db.engine import async_session
    from sqlalchemy import select
    from db.models.knowledge_base import KnowledgeBase

    orch = get_search_orchestrator()
    if orch is None:
        return {"error": "搜索服务未就绪，请稍后重试", "total": 0, "results": []}

    if not query.strip():
        return {"total": 0, "results": []}

    # 解析 kb_id：支持 UUID、名称模糊匹配、自动发现
    resolved_id = kb_id.strip()
    if not resolved_id:
        async with async_session() as db:
            if kb_name.strip():
                # 按名称模糊匹配
                rows = (
                    await db.execute(
                        select(KnowledgeBase).where(
                            KnowledgeBase.name.contains(kb_name.strip())
                        )
                    )
                ).scalars().all()
            else:
                # 自动取第一个 ready 状态的 KB
                rows = (
                    await db.execute(
                        select(KnowledgeBase).where(
                            KnowledgeBase.status == "ready"
                        ).limit(1)
                    )
                ).scalars().all()

            if not rows:
                # 返回可用 KB 列表帮助 LLM 下次调用
                all_rows = (
                    await db.execute(
                        select(KnowledgeBase).where(
                            KnowledgeBase.status == "ready"
                        )
                    )
                ).scalars().all()
                available = [
                    {"kb_id": r.id, "name": r.name, "docs": r.docs_count or 0}
                    for r in all_rows
                ]
                return {
                    "error": (
                        f"未找到匹配的知识库'{kb_name}'。"
                        if kb_name.strip()
                        else "未指定知识库且没有可用的 ready 状态知识库。"
                    ),
                    "available_kbs": available,
                    "total": 0,
                    "results": [],
                    "hint": "请先调用 list_knowledge_bases 查看可用知识库，然后用正确的 kb_id 重新调用 kb_search。",
                }

            resolved_id = rows[0].id

    # 验证 kb_id 对应的 Milvus/Chroma Collection 是否存在
    req = SearchRequest(query=query.strip(), mode=mode, top_k=top_k)

    async with async_session() as db:
        try:
            resp = await orch.search(db, resolved_id, req)
        except RuntimeError as e:
            # Collection 不存在等错误 → 返回可用 KB 列表
            all_rows = (
                await db.execute(
                    select(KnowledgeBase).where(
                        KnowledgeBase.status == "ready"
                    )
                )
            ).scalars().all()
            available = [
                {"kb_id": r.id, "name": r.name, "docs": r.docs_count or 0}
                for r in all_rows
            ]
            return {
                "error": f"检索失败（kb_id={resolved_id}）：{e}",
                "available_kbs": available,
                "total": 0,
                "results": [],
                "hint": "该知识库可能不存在或未完成索引，请使用 list_knowledge_bases 确认可用的知识库。",
            }

        return {
            "total": resp.total,
            "results": [
                {
                    "doc": r.doc_name,
                    "content": r.content,
                    "score": r.score,
                    "vec_score": r.vec_score,
                    "bm25_score": r.bm25_score,
                }
                for r in resp.results
            ],
        }


def list_knowledge_bases() -> dict[str, Any]:
    """列出当前系统中所有可用的知识库及其 ID。

    Returns:
        {"total": int, "knowledge_bases": [{"kb_id": str, "name": str, "docs": int, "chunks": int}]}
    """
    return asyncio.run(_list_kb_async())


async def _list_kb_async() -> dict[str, Any]:
    from db.engine import async_session
    from sqlalchemy import select
    from db.models.knowledge_base import KnowledgeBase

    async with async_session() as db:
        rows = (
            await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.status == "ready")
            )
        ).scalars().all()

    return {
        "total": len(rows),
        "knowledge_bases": [
            {
                "kb_id": r.id,
                "name": r.name,
                "docs": r.docs_count or 0,
                "chunks": r.chunks_count or 0,
            }
            for r in rows
        ],
    }


__all__ = ["kb_search", "list_knowledge_bases"]
