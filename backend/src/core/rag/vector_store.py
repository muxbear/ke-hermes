"""向量数据库抽象层——策略模式。

统一 Milvus 和 Chroma 的操作接口，支持向量检索和 BM25 全文检索。
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

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
    async def get_chunks_by_doc_id(self, kb_id: str, doc_id: str) -> list[dict]:
        """按文档 ID 查询所有切片，按 chunk_index 排序。"""

    @abstractmethod
    async def get_chunks_by_ids(self, kb_id: str, chunk_ids: list[str]) -> list[dict]:
        """按切片 ID 列表批量查询切片详情。"""

    @abstractmethod
    async def delete_chunk_by_id(self, kb_id: str, chunk_id: str) -> None:
        """按切片 ID 删除单个切片。"""

    @abstractmethod
    async def update_chunk(
        self, kb_id: str, chunk_id: str, new_text: str,
        new_embedding: list[float],
    ) -> None:
        """更新切片文本和向量。"""

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
        self._collections: dict[str, Any] = {}

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
                await utility.drop_collection(collection_name)

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
            await collection.create_index(
                field_name="embedding",
                index_params={
                    "metric_type": "COSINE",
                    "index_type": "HNSW",
                    "params": {"M": 16, "efConstruction": 200},
                },
            )

            # Scalar indices
            for field_name in ["doc_id", "kb_id"]:
                await collection.create_index(
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
            await utility.drop_collection(collection_name)
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

    async def _get_collection(self, kb_id: str) -> Any:
        """获取或加载 Milvus Collection。"""
        await self._ensure_connected()
        collection = self._collections.get(kb_id)
        if collection is None:
            from pymilvus import Collection
            collection = Collection(name=self._collection_name(kb_id))
            collection.load()
            self._collections[kb_id] = collection
        return collection

    _CHUNK_OUTPUT_FIELDS = [
        "id", "doc_id", "kb_id", "chunk_index", "chunk_text",
        "doc_name", "doc_type", "metadata_",
    ]

    async def get_chunks_by_doc_id(self, kb_id: str, doc_id: str) -> list[dict]:
        collection = await self._get_collection(kb_id)
        results = collection.query(
            expr=f'doc_id == "{doc_id}"',
            output_fields=self._CHUNK_OUTPUT_FIELDS,
        )
        results.sort(key=lambda r: r.get("chunk_index", 0))
        logger.info("Milvus queried %d chunks for doc=%s", len(results), doc_id)
        return results

    async def get_chunks_by_ids(self, kb_id: str, chunk_ids: list[str]) -> list[dict]:
        """按切片 ID 列表批量查询切片详情。"""
        if not chunk_ids:
            return []

        collection = await self._get_collection(kb_id)
        ids_str = ", ".join(f'"{cid}"' for cid in chunk_ids)
        expr = f"id in [{ids_str}]"
        try:
            results = collection.query(
                expr=expr,
                output_fields=self._CHUNK_OUTPUT_FIELDS,
            )
            return results
        except Exception:
            logger.exception("Milvus get_chunks_by_ids failed for kb=%s", kb_id)
            return []

    async def delete_chunk_by_id(self, kb_id: str, chunk_id: str) -> None:
        collection = await self._get_collection(kb_id)
        collection.delete(f'id == "{chunk_id}"')
        collection.flush()
        logger.info("Milvus deleted chunk=%s in kb=%s", chunk_id, kb_id)

    async def update_chunk(
        self, kb_id: str, chunk_id: str, new_text: str,
        new_embedding: list[float],
    ) -> None:
        import time
        collection = await self._get_collection(kb_id)
        now_ms = int(time.time() * 1000)
        collection.upsert([{
            "id": chunk_id,
            "chunk_text": new_text[:65535],
            "embedding": new_embedding,
            "created_at": now_ms,
        }])
        collection.flush()
        logger.info("Milvus updated chunk=%s in kb=%s", chunk_id, kb_id)

    async def similarity_search(
        self, kb_id: str, query_embedding: list[float], top_k: int
    ) -> list[tuple[str, float]]:
        """Milvus 向量检索——ANN 搜索 embedding 字段。"""
        collection = await self._get_collection(kb_id)
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 64}},
            limit=top_k,
            output_fields=[],
        )
        pairs: list[tuple[str, float]] = []
        if results and results[0]:
            for hit in results[0]:
                # Milvus COSINE distance: 0=identical, 2=opposite
                # Convert to similarity: 1 - distance/2 → [0, 1]
                similarity = 1.0 - (hit.distance / 2.0)
                pairs.append((hit.id, round(similarity, 6)))
        logger.info("Milvus similarity search kb=%s top_k=%d returned=%d", kb_id, top_k, len(pairs))
        return pairs

    async def bm25_search(
        self, kb_id: str, query: str, top_k: int
    ) -> list[tuple[str, float]]:
        """Milvus BM25 检索——客户端侧词频打分（避免 LIKE 大小写敏感问题）。

        获取全部 chunk 文本后在客户端侧做大小写不敏感的 TF 评分。
        """
        import re

        query_terms = re.findall(r"\w+", query.lower())
        if not query_terms:
            return []

        collection = await self._get_collection(kb_id)

        try:
            candidates = collection.query(
                expr="id != ''",
                output_fields=["id", "chunk_text"],
            )
        except Exception:
            logger.warning("Milvus BM25 query failed for kb=%s", kb_id)
            return []

        if not candidates:
            return []

        scores: list[tuple[str, float]] = []
        for row in candidates:
            text = (row.get("chunk_text") or "").lower()
            tf = sum(text.count(t) for t in query_terms)
            if tf > 0:
                scores.append((row["id"], float(tf)))

        scores.sort(key=lambda x: x[1], reverse=True)
        logger.info("Milvus BM25 kb=%s top_k=%d candidates=%d returned=%d",
                     kb_id, top_k, len(candidates), len(scores[:top_k]))
        return scores[:top_k]

    async def hybrid_search(
        self, kb_id: str, query: str, query_embedding: list[float],
        top_k: int, alpha: float = 0.7,
    ) -> list[tuple[str, float]]:
        """Milvus 混合检索——向量 + BM25 加权融合。"""
        vec_results = await self.similarity_search(kb_id, query_embedding, top_k * 2)
        bm25_results = await self.bm25_search(kb_id, query, top_k * 2)

        vec_scores: dict[str, float] = {}
        bm25_scores: dict[str, float] = {}

        if vec_results:
            max_v = max(s for _, s in vec_results)
            min_v = min(s for _, s in vec_results)
            if max_v == min_v:
                for cid, _ in vec_results:
                    vec_scores[cid] = 1.0
            else:
                v_range = max_v - min_v
                for cid, s in vec_results:
                    vec_scores[cid] = (s - min_v) / v_range

        if bm25_results:
            max_b = max(s for _, s in bm25_results)
            min_b = min(s for _, s in bm25_results)
            if max_b == min_b:
                for cid, _ in bm25_results:
                    bm25_scores[cid] = 1.0
            else:
                b_range = max_b - min_b
                for cid, s in bm25_results:
                    bm25_scores[cid] = (s - min_b) / b_range

        fused: dict[str, float] = {}
        for cid in set(vec_scores) | set(bm25_scores):
            v = vec_scores.get(cid, 0.0)
            b = bm25_scores.get(cid, 0.0)
            fused[cid] = alpha * v + (1 - alpha) * b

        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        logger.info("Milvus hybrid kb=%s top_k=%d vec=%d bm25=%d fused=%d",
                     kb_id, top_k, len(vec_results), len(bm25_results), len(ranked))
        return ranked


class ChromaVectorStore(BaseVectorStore):
    """基于 Chroma 的向量数据库实现。

    Collection 命名规则: kb_{kb_id}
    文档文本存储为 Chroma documents 字段以支持全文检索。
    BM25 通过 Chroma 内置 where_document 全文搜索 + TF 打分实现。
    """

    @staticmethod
    def _collection_name(kb_id: str) -> str:
        return f"kb_{kb_id.replace('-', '_')}"

    def __init__(
        self,
        host: str = "",
        port: int = 8001,
        persist_dir: str = "./chroma_data",
    ):
        self._host = host
        self._port = port
        self._persist_dir = persist_dir
        self._client: Any = None

    def _get_client(self) -> Any:
        """获取或初始化 Chroma 客户端。"""
        if self._client is None:
            import chromadb
            if self._host:
                self._client = chromadb.HttpClient(host=self._host, port=self._port)
            else:
                self._client = chromadb.PersistentClient(path=self._persist_dir)
        return self._client

    def _get_collection(self, kb_id: str) -> Any:
        """获取 Collection，不存在时抛出异常。"""
        client = self._get_client()
        return client.get_collection(self._collection_name(kb_id))

    async def create_collection(self, kb_id: str, dim: int, enable_bm25: bool = True) -> None:
        client = self._get_client()
        collection_name = self._collection_name(kb_id)

        try:
            client.delete_collection(collection_name)
            logger.info("Dropped existing Chroma collection: %s", collection_name)
        except Exception:
            pass

        client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine", "dim": dim},
        )
        logger.info("Chroma collection created: %s (dim=%d)", collection_name, dim)

    async def delete_collection(self, kb_id: str) -> None:
        client = self._get_client()
        collection_name = self._collection_name(kb_id)
        try:
            client.delete_collection(collection_name)
            logger.info("Chroma collection deleted: %s", collection_name)
        except Exception as e:
            logger.error("Failed to delete Chroma collection %s: %s", collection_name, e)

    async def add_documents(
        self, kb_id: str, documents: list[Document], embeddings: list[list[float]],
    ) -> list[str]:
        import json
        import uuid

        collection = self._get_collection(kb_id)

        chunk_ids = [str(uuid.uuid4()) for _ in documents]
        chroma_docs: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for i, doc in enumerate(documents):
            chroma_docs.append(doc.page_content)
            metadatas.append({
                "doc_id": doc.metadata.get("doc_id", ""),
                "kb_id": kb_id,
                "chunk_index": doc.metadata.get("chunk_index", i),
                "doc_name": doc.metadata.get("doc_name", ""),
                "doc_type": doc.metadata.get("doc_type", ""),
                "metadata_": json.dumps(doc.metadata.get("metadata_", {})),
                "created_at": doc.metadata.get("created_at", 0),
            })

        collection.add(
            ids=chunk_ids,
            documents=chroma_docs,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Chroma inserted %d chunks for kb=%s", len(chunk_ids), kb_id)
        return chunk_ids

    async def delete_by_doc_id(self, kb_id: str, doc_id: str) -> None:
        collection = self._get_collection(kb_id)
        # Find all chunk IDs for this doc
        result = collection.get(
            where={"doc_id": doc_id},
            include=[],
        )
        if result["ids"]:
            collection.delete(ids=result["ids"])
            logger.info("Chroma deleted %d chunks for doc=%s in kb=%s", len(result["ids"]), doc_id, kb_id)

    async def get_chunks_by_doc_id(self, kb_id: str, doc_id: str) -> list[dict]:
        import json

        collection = self._get_collection(kb_id)
        result = collection.get(
            where={"doc_id": doc_id},
            include=["documents", "metadatas"],
        )

        chunks: list[dict] = []
        if not result["ids"]:
            return chunks

        for i, cid in enumerate(result["ids"]):
            meta = (result["metadatas"] or [{}])[i] if i < len(result["metadatas"] or []) else {}
            metadata_str = meta.get("metadata_", "{}")
            try:
                metadata_obj = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
            except (json.JSONDecodeError, TypeError):
                metadata_obj = {}

            chunks.append({
                "id": cid,
                "doc_id": meta.get("doc_id", ""),
                "kb_id": meta.get("kb_id", kb_id),
                "chunk_index": meta.get("chunk_index", i),
                "chunk_text": (result["documents"] or [""])[i] if i < len(result["documents"] or []) else "",
                "doc_name": meta.get("doc_name", ""),
                "doc_type": meta.get("doc_type", ""),
                "metadata_": metadata_obj,
            })

        chunks.sort(key=lambda r: r.get("chunk_index", 0))
        logger.info("Chroma queried %d chunks for doc=%s", len(chunks), doc_id)
        return chunks

    async def get_chunks_by_ids(self, kb_id: str, chunk_ids: list[str]) -> list[dict]:
        """按切片 ID 列表批量查询切片详情。"""
        import json

        if not chunk_ids:
            return []

        collection = self._get_collection(kb_id)
        result = collection.get(
            ids=chunk_ids,
            include=["documents", "metadatas"],
        )

        chunks: list[dict] = []
        if not result["ids"]:
            return chunks

        for i, cid in enumerate(result["ids"]):
            meta = (result.get("metadatas") or [{}])[i] if i < len(result.get("metadatas") or []) else {}
            metadata_str = meta.get("metadata_", "{}")
            try:
                metadata_obj = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
            except (json.JSONDecodeError, TypeError):
                metadata_obj = {}

            chunks.append({
                "id": cid,
                "doc_id": meta.get("doc_id", ""),
                "kb_id": meta.get("kb_id", kb_id),
                "chunk_index": meta.get("chunk_index", i),
                "chunk_text": (result.get("documents") or [""])[i] if i < len(result.get("documents") or []) else "",
                "doc_name": meta.get("doc_name", ""),
                "doc_type": meta.get("doc_type", ""),
                "metadata_": metadata_obj,
            })

        return chunks

    async def delete_chunk_by_id(self, kb_id: str, chunk_id: str) -> None:
        collection = self._get_collection(kb_id)
        collection.delete(ids=[chunk_id])
        logger.info("Chroma deleted chunk=%s in kb=%s", chunk_id, kb_id)

    async def update_chunk(
        self, kb_id: str, chunk_id: str, new_text: str,
        new_embedding: list[float],
    ) -> None:
        import time

        collection = self._get_collection(kb_id)
        now_ms = int(time.time() * 1000)
        collection.update(
            ids=[chunk_id],
            documents=[new_text],
            embeddings=[new_embedding],
            metadatas=[{"created_at": now_ms}],
        )
        logger.info("Chroma updated chunk=%s in kb=%s", chunk_id, kb_id)

    async def similarity_search(
        self, kb_id: str, query_embedding: list[float], top_k: int,
    ) -> list[tuple[str, float]]:
        collection = self._get_collection(kb_id)
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=[],
        )

        pairs: list[tuple[str, float]] = []
        if not result["ids"] or not result["ids"][0]:
            return pairs

        for i, cid in enumerate(result["ids"][0]):
            distance = (result["distances"] or [[]])[0][i] if result.get("distances") else 0.0
            pairs.append((cid, distance))

        logger.info("Chroma similarity search kb=%s top_k=%d returned=%d", kb_id, top_k, len(pairs))
        return pairs

    async def bm25_search(
        self, kb_id: str, query: str, top_k: int,
    ) -> list[tuple[str, float]]:
        """BM25 全文搜索——通过 Chroma where_document 过滤 + TF 打分。

        Chroma 的全文搜索能力有限，用 $contains 过滤候选文档后按词频排序。
        """
        import re

        collection = self._get_collection(kb_id)
        query_terms = re.findall(r"\w+", query.lower())
        if not query_terms:
            return []

        # Use the longest query term for Chroma full-text filtering
        longest_term = max(query_terms, key=len)
        try:
            result = collection.get(
                where_document={"$contains": longest_term},
                include=["documents"],
            )
        except Exception:
            logger.warning("Chroma BM25 get failed for kb=%s, term=%s", kb_id, longest_term)
            return []

        if not result["ids"]:
            return []

        scores: list[tuple[str, float]] = []
        for i, cid in enumerate(result["ids"]):
            doc_text = ((result["documents"] or [""])[i] or "").lower()
            tf = sum(doc_text.count(term) for term in query_terms if term)
            if tf > 0:
                scores.append((cid, float(tf)))

        scores.sort(key=lambda x: x[1], reverse=True)
        logger.info("Chroma BM25 kb=%s top_k=%d candidates=%d returned=%d", kb_id, top_k, len(result["ids"]), len(scores[:top_k]))
        return scores[:top_k]

    async def hybrid_search(
        self, kb_id: str, query: str, query_embedding: list[float],
        top_k: int, alpha: float = 0.7,
    ) -> list[tuple[str, float]]:
        """混合搜索——向量相似度 + BM25 加权融合。

        alpha: 向量权重 (0=纯BM25, 1=纯向量)
        """
        vec_results = await self.similarity_search(kb_id, query_embedding, top_k * 2)
        bm25_results = await self.bm25_search(kb_id, query, top_k * 2)

        # Build score maps, normalize to [0, 1]
        vec_scores: dict[str, float] = {}
        bm25_scores: dict[str, float] = {}

        if vec_results:
            max_vec = max(s for _, s in vec_results)
            min_vec = min(s for _, s in vec_results)
            vec_range = max_vec - min_vec if max_vec != min_vec else 1.0
            for cid, s in vec_results:
                vec_scores[cid] = 1.0 - (s - min_vec) / vec_range

        if bm25_results:
            max_bm25 = max(s for _, s in bm25_results)
            min_bm25 = min(s for _, s in bm25_results)
            bm25_range = max_bm25 - min_bm25 if max_bm25 != min_bm25 else 1.0
            for cid, s in bm25_results:
                bm25_scores[cid] = (s - min_bm25) / bm25_range

        # Fuse scores
        fused: dict[str, float] = {}
        for cid in set(vec_scores) | set(bm25_scores):
            v = vec_scores.get(cid, 0.0)
            b = bm25_scores.get(cid, 0.0)
            fused[cid] = alpha * v + (1 - alpha) * b

        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        logger.info("Chroma hybrid kb=%s top_k=%d alpha=%.2f returned=%d", kb_id, top_k, alpha, len(ranked))
        return ranked
