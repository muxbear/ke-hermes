"""Tests for VectorStoreFactory."""

import pytest
from core.rag.vector_store import BaseVectorStore, ChromaVectorStore, MilvusVectorStore


class FakeVectorStore(BaseVectorStore):
    """Fake implementation for testing factory registration."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def create_collection(self, kb_id, dim, enable_bm25=True):
        pass

    async def delete_collection(self, kb_id):
        pass

    async def add_documents(self, kb_id, documents, embeddings):
        return ["id1"]

    async def delete_by_doc_id(self, kb_id, doc_id):
        pass

    async def get_chunks_by_doc_id(self, kb_id, doc_id):
        return []

    async def get_chunks_by_ids(self, kb_id, chunk_ids):
        return []

    async def delete_chunk_by_id(self, kb_id, chunk_id):
        pass

    async def update_chunk(self, kb_id, chunk_id, new_text, new_embedding):
        pass

    async def similarity_search(self, kb_id, query_embedding, top_k):
        return []

    async def bm25_search(self, kb_id, query, top_k):
        return []

    async def hybrid_search(self, kb_id, query, query_embedding, top_k, alpha=0.7):
        return []


class TestVectorStoreFactory:
    def setup_method(self):
        from core.rag.vector_store_factory import VectorStoreFactory
        # 确保内置后端已注册
        VectorStoreFactory.register("fake", FakeVectorStore)

    def test_register_and_create(self):
        """注册后端后应能通过名称创建实例。"""
        from core.rag.vector_store_factory import VectorStoreFactory

        store = VectorStoreFactory.create("fake", host="localhost", port=9999)
        assert isinstance(store, FakeVectorStore)
        assert store.kwargs == {"host": "localhost", "port": 9999}

    def test_create_unknown_backend_raises(self):
        """创建未注册后端应抛出 ValueError。"""
        from core.rag.vector_store_factory import VectorStoreFactory

        with pytest.raises(ValueError, match="不支持的向量数据库后端"):
            VectorStoreFactory.create("nonexistent")

    def test_available_backends(self):
        """available_backends 应返回已注册后端列表。"""
        from core.rag.vector_store_factory import VectorStoreFactory

        backends = VectorStoreFactory.available_backends()
        assert "fake" in backends
