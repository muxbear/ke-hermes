"""Ke-Hermes 知识库检索 MCP Server。

基于 MCP 协议暴露知识库检索能力，任何兼容 MCP 的客户端均可连接。
复用 SearchOrchestrator 单例，需在 backend/ 上下文中启动。
"""

import asyncio
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent / "src"))

mcp = FastMCP("ke-hermes-kb-search")


@mcp.tool()
async def search_knowledge_base(
    kb_id: str,
    query: str,
    mode: str = "hybrid",
    top_k: int = 5,
) -> dict:
    """在 Ke-Hermes 知识库中检索知识。

    支持三种检索模式：
    - hybrid: RRF 混合检索（向量 + BM25 融合，推荐默认使用）
    - vector: 纯向量语义检索（适合概念性问题）
    - bm25:   纯关键词检索（适合精确术语匹配）

    Args:
        kb_id: 知识库唯一标识。
        query: 搜索查询关键词。
        mode: 检索模式，默认 hybrid。
        top_k: 返回结果数量，默认 5。

    Returns:
        {"total": int, "results": [{"doc": str, "content": str, "score": float, ...}]}
    """
    from api.knowledge_base.schemas import SearchRequest
    from api.knowledge_base.search_service import get_search_orchestrator
    from db.engine import async_session

    orch = get_search_orchestrator()
    if orch is None:
        return {"error": "搜索服务未就绪，请确认后端已启动", "total": 0, "results": []}

    if not query.strip():
        return {"total": 0, "results": []}

    req = SearchRequest(query=query.strip(), mode=mode, top_k=top_k)

    async with async_session() as db:
        resp = await orch.search(db, kb_id, req)
        return {
            "total": resp.total,
            "results": [r.model_dump() for r in resp.results],
        }


def main():
    """启动 MCP Server。需先通过 server.py 启动后端完成初始化。"""
    # 检查单例是否已注入
    from api.knowledge_base.search_service import get_search_orchestrator

    orch = get_search_orchestrator()
    if orch is None:
        print(
            "警告: SearchOrchestrator 尚未初始化。"
            "请先启动后端 server.py，或在当前进程中调用 _init_knowledge_base()。"
        )
        print("继续启动 MCP Server，但工具调用时将返回错误。")

    mcp.run()


if __name__ == "__main__":
    main()
