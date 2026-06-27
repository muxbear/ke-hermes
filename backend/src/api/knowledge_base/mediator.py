"""知识库中介者——协调多组件间的文档/知识库删除操作。

将散落在 delete_kb() 和 delete_document() 中的多组件清理逻辑集中管理。
"""

from __future__ import annotations

import logging
import os
import shutil

from core.rag.vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


class KnowledgeBaseMediator:
    """封装知识库操作中涉及的多组件协调逻辑。

    使用方式:
        mediator = KnowledgeBaseMediator(vector_store)
        await mediator.on_document_deleted(kb_id, doc_id, storage_path)
        await mediator.on_knowledge_base_deleted(kb_id)
    """

    def __init__(self, vector_store: BaseVectorStore | None = None) -> None:
        self._vector_store = vector_store

    async def on_document_deleted(
        self, kb_id: str, doc_id: str, storage_path: str,
    ) -> None:
        """文档删除后的级联清理——向量库 + 文件系统。"""
        errors: list[str] = []

        # 向量库清理
        if self._vector_store:
            try:
                await self._vector_store.delete_by_doc_id(kb_id, doc_id)
            except Exception as e:
                errors.append(f"向量库: {e}")
                logger.error("删除文档向量数据失败 kb=%s doc=%s: %s", kb_id, doc_id, e)

        # 文件系统清理
        storage_dir = os.path.dirname(storage_path)
        if os.path.isdir(storage_dir):
            try:
                shutil.rmtree(storage_dir, ignore_errors=True)
            except Exception as e:
                errors.append(f"文件系统: {e}")

        if errors:
            logger.warning("文档 %s 部分清理失败: %s", doc_id, "; ".join(errors))

    async def on_knowledge_base_deleted(self, kb_id: str) -> None:
        """知识库删除后的级联清理——向量库中删除整个 collection。"""
        if not self._vector_store:
            return
        try:
            await self._vector_store.delete_collection(kb_id)
        except Exception as e:
            logger.error("删除知识库 %s 向量数据失败: %s", kb_id, e)
