"""RAG 核心模块。

NOTE: 为避免与 core.__init__ 的循环导入，各子模块在使用时按需导入。
"""


def _lazy_import(name: str):
    """延迟导入以避免循环依赖。"""
    import importlib
    return importlib.import_module(name, __package__)


def __getattr__(name: str):
    _exports = {
        "BaseVectorStore": ".vector_store",
        "NoopVectorStore": ".vector_store",
        "BM25Indexer": ".bm25_index",
        "ChunkStrategy": ".splitters",
        "ChunkStrategyRegistry": ".splitters",
        "create_chunk_registry": ".splitters",
        "DocumentLoaderRegistry": ".loaders",
        "DocumentLoaderStrategy": ".loaders",
        "FallbackLoaderStrategy": ".loaders",
        "create_default_loader_registry": ".loaders",
        "get_embedding_model": ".embedding",
    }
    if name in _exports:
        mod = _lazy_import(_exports[name])
        attr = getattr(mod, name)
        globals()[name] = attr
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseVectorStore",
    "BM25Indexer",
    "ChunkStrategy",
    "ChunkStrategyRegistry",
    "create_chunk_registry",
    "create_default_loader_registry",
    "DocumentLoaderRegistry",
    "DocumentLoaderStrategy",
    "FallbackLoaderStrategy",
    "get_embedding_model",
    "NoopVectorStore",
]
