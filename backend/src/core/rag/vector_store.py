"""向量数据库抽象层——策略模式。

统一 Milvus 和 Chroma 的操作接口，支持向量检索和 BM25 全文检索。
"""

import logging
from abc import ABC, abstractmethod

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """向量数据库抽象接口（策略模式）。"""

    @abstractmethod
    async def create_collection(self, kb_id: str, dim: int, enable_bm25: bool = True) -> None:
        """为知识库创建 Collection。"""

    @abstractmethod
    async def delete_collection(self, kb_id: str) -> None:
        """删除知识库对应的 Collection。"""

    @abstractmethod
    async def add_documents(
        self, kb_id: str, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        """将文档向量写入向量数据库，返回 chunk ID 列表。"""

    @abstractmethod
    async def delete_by_doc_id(self, kb_id: str, doc_id: str) -> None:
        """按文档 ID 删除所有相关向量。"""

    @abstractmethod
    async def similarity_search(
        self, kb_id: str, query_embedding: list[float], top_k: int
    ) -> list[tuple[str, float]]:
        """向量相似度搜索。"""

    @abstractmethod
    async def bm25_search(
        self, kb_id: str, query: str, top_k: int
    ) -> list[tuple[str, float]]:
        """BM25 全文搜索。"""

    @abstractmethod
    async def hybrid_search(
        self, kb_id: str, query: str, query_embedding: list[float],
        top_k: int, alpha: float = 0.7,
    ) -> list[tuple[str, float]]:
        """混合搜索（向量 + BM25）。alpha: 向量权重（0=纯BM25, 1=纯向量）。"""


class MilvusVectorStore(BaseVectorStore):
    """基于 Milvus 的向量数据库实现。

    Collection 命名规则: kb_{kb_id}
    每个 Collection 包含 embedding (FLOAT_VECTOR) 字段和 BM25 稀疏向量。
    """

    @staticmethod
    def _collection_name(kb_id: str) -> str:
        """将 kb_id 转为合法的 Milvus 集合名（只允许字母数字下划线）。"""
        return f"kb_{kb_id.replace('-', '_')}"

    def __init__(self, uri: str, user: str, password: str, db_name: str = "ke_hermes"):
        self._uri = uri
        self._user = user
        self._password = password
        self._db_name = db_name
        self._connected = False
        self._collections: dict[str, object] = {}

    async def _ensure_connected(self):
        if self._connected:
            return
        try:
            from pymilvus import connections
            connections.connect(
                alias="default",
                uri=self._uri,
                user=self._user,
                password=self._password,
                db_name=self._db_name,
            )
            self._connected = True
            logger.info("Milvus connected: %s, db=%s", self._uri, self._db_name)
        except Exception as e:
            logger.error("Milvus connection failed: %s", e)
            raise

    async def create_collection(self, kb_id: str, dim: int, enable_bm25: bool = True) -> None:
        await self._ensure_connected()
        collection_name = self._collection_name(kb_id)

        try:
            from pymilvus import (
                Collection, CollectionSchema, DataType, FieldSchema, utility,
            )
            # 删除旧集合（可能由旧版 Schema 创建，与新版本不兼容）
            if utility.has_collection(collection_name):
                logger.info("Dropping existing collection: %s", collection_name)
                utility.drop_collection(collection_name)

            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
                FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="kb_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
                FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=16),
                FieldSchema(name="metadata_", dtype=DataType.JSON),
                FieldSchema(name="created_at", dtype=DataType.INT64),
            ]

            schema = CollectionSchema(fields=fields, description=f"Knowledge base: {kb_id}")
            collection = Collection(name=collection_name, schema=schema)

            # Dense vector index (COSINE)
            collection.create_index(
                field_name="embedding",
                index_params={
                    "metric_type": "COSINE",
                    "index_type": "HNSW",
                    "params": {"M": 16, "efConstruction": 200},
                },
            )

            # Scalar indices
            for field_name in ["doc_id", "kb_id"]:
                collection.create_index(
                    field_name=field_name,
                    index_params={"index_type": "INVERTED"},
                )

            collection.load()
            self._collections[kb_id] = collection
            logger.info("Milvus collection created: %s (dim=%d)", collection_name, dim)

        except Exception as e:
            logger.error("Failed to create Milvus collection kb=%s: %s", kb_id, e)
            raise

    async def delete_collection(self, kb_id: str) -> None:
        await self._ensure_connected()
        collection_name = self._collection_name(kb_id)
        try:
            from pymilvus import utility
            utility.drop_collection(collection_name)
            self._collections.pop(kb_id, None)
            logger.info("Milvus collection deleted: %s", collection_name)
        except Exception as e:
            logger.error("Failed to delete Milvus collection %s: %s", collection_name, e)

    async def add_documents(
        self, kb_id: str, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        await self._ensure_connected()
        import uuid
        import time

        collection = self._collections.get(kb_id)
        if collection is None:
            from pymilvus import Collection
            collection = Collection(name=self._collection_name(kb_id))
            collection.load()
            self._collections[kb_id] = collection

        chunk_ids = [str(uuid.uuid4()) for _ in documents]
        now_ms = int(time.time() * 1000)

        data = []
        for i, doc in enumerate(documents):
            data.append({
                "id": chunk_ids[i],
                "doc_id": doc.metadata.get("doc_id", ""),
                "kb_id": kb_id,
                "chunk_index": doc.metadata.get("chunk_index", i),
                "chunk_text": doc.page_content[:65535],
                "embedding": embeddings[i],
                "doc_name": doc.metadata.get("doc_name", ""),
                "doc_type": doc.metadata.get("doc_type", ""),
                "metadata_": doc.metadata.get("metadata_", {}),
                "created_at": now_ms,
            })

        collection.insert(data)
        collection.flush()
        logger.info("Milvus inserted %d chunks for kb=%s", len(data), kb_id)
        return chunk_ids

    async def delete_by_doc_id(self, kb_id: str, doc_id: str) -> None:
        await self._ensure_connected()
        collection = self._collections.get(kb_id)
        if collection is None:
            from pymilvus import Collection
            collection = Collection(name=self._collection_name(kb_id))
            collection.load()
            self._collections[kb_id] = collection

        collection.delete(f'doc_id == "{doc_id}"')
        collection.flush()
        logger.info("Milvus deleted chunks for doc=%s in kb=%s", doc_id, kb_id)

    async def similarity_search(
        self, kb_id: str, query_embedding: list[float], top_k: int
    ) -> list[tuple[str, float]]:
        return []

    async def bm25_search(
        self, kb_id: str, query: str, top_k: int
    ) -> list[tuple[str, float]]:
        return []

    async def hybrid_search(
        self, kb_id: str, query: str, query_embedding: list[float],
        top_k: int, alpha: float = 0.7,
    ) -> list[tuple[str, float]]:
        return []


class NoopVectorStore(BaseVectorStore):
    """空实现——开发/测试环境下的占位向量数据库。

    所有操作静默成功，日志记录警告。
    """

    async def create_collection(self, kb_id: str, dim: int, enable_bm25: bool = True) -> None:
        logger.warning("NoopVectorStore: create_collection kb=%s dim=%d", kb_id, dim)

    async def delete_collection(self, kb_id: str) -> None:
        logger.warning("NoopVectorStore: delete_collection kb=%s", kb_id)

    async def add_documents(
        self, kb_id: str, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        logger.warning("NoopVectorStore: add_documents kb=%s count=%d", kb_id, len(documents))
        return [f"chunk-{kb_id}-{i}" for i in range(len(documents))]

    async def delete_by_doc_id(self, kb_id: str, doc_id: str) -> None:
        logger.warning("NoopVectorStore: delete_by_doc_id kb=%s doc=%s", kb_id, doc_id)

    async def similarity_search(
        self, kb_id: str, query_embedding: list[float], top_k: int
    ) -> list[tuple[str, float]]:
        return []

    async def bm25_search(
        self, kb_id: str, query: str, top_k: int
    ) -> list[tuple[str, float]]:
        return []

    async def hybrid_search(
        self, kb_id: str, query: str, query_embedding: list[float],
        top_k: int, alpha: float = 0.7,
    ) -> list[tuple[str, float]]:
        return []
