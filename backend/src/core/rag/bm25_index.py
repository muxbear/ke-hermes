"""BM25 倒排索引——委托给向量数据库实现。"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.documents import Document

if TYPE_CHECKING:
    from core.rag.vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


class BM25Indexer:
    """BM25 倒排索引管理。

    对 Milvus Collection 调用 BM25 函数索引，对 Chroma 使用内置全文检索。
    """

    def __init__(self, vector_store: "BaseVectorStore"):
        self._store = vector_store

    async def index(self, kb_id: str, documents: list[Document]) -> None:
        """为文档建立 BM25 索引（委托给向量数据库）。"""
        logger.info("BM25 index: kb=%s docs=%d", kb_id, len(documents))
        # BM25 索引在向量数据库 add_documents 时自动建立
        # Milvus: BM25 Function 自动从 chunk_text 生成稀疏向量
        # Chroma: 内置全文检索引擎

    async def search(self, kb_id: str, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """BM25 全文检索。"""
        return await self._store.bm25_search(kb_id, query, top_k)
