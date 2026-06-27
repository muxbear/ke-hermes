"""向量库工厂——工厂方法模式。

支持自动注册和按名称创建向量库后端，消除 if/elif 分支。
"""

from __future__ import annotations

from typing import Any

from core.rag.vector_store import BaseVectorStore


class VectorStoreFactory:
    """向量库工厂——按 backend 名称创建对应的 BaseVectorStore 实现。

    使用方式:
        VectorStoreFactory.register("milvus", MilvusVectorStore)
        store = VectorStoreFactory.create("milvus", uri="...", ...)
    """

    _registry: dict[str, type[BaseVectorStore]] = {}

    @classmethod
    def register(cls, backend: str, store_cls: type[BaseVectorStore]) -> None:
        """注册向量库后端。"""
        cls._registry[backend] = store_cls

    @classmethod
    def create(cls, backend: str, **kwargs: Any) -> BaseVectorStore:
        """创建指定后端的向量库实例。"""
        if backend not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(
                f"不支持的向量数据库后端: {backend}，可选: {available}"
            )
        return cls._registry[backend](**kwargs)

    @classmethod
    def available_backends(cls) -> list[str]:
        """获取所有已注册的后端名称。"""
        return list(cls._registry.keys())
