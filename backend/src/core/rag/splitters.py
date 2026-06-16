"""文本切片器——策略模式。

支持 5 种切片策略：fixed / recursive / semantic / markdown / agentic。
"""

import logging
from abc import ABC, abstractmethod

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class ChunkStrategy(ABC):
    """文本切片策略抽象接口。"""

    @abstractmethod
    def split(self, documents: list[Document]) -> list[Document]:
        """将文档列表切分为更小的分片。"""
        ...


class FixedChunkStrategy(ChunkStrategy):
    """固定长度切片。"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        from langchain_text_splitters import CharacterTextSplitter
        splitter = CharacterTextSplitter(
            separator="\n\n", chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )
        return splitter.split_documents(documents)


class RecursiveChunkStrategy(ChunkStrategy):
    """递归分隔符切片——按段落→换行→句号→空格递归切分。"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size, chunk_overlap=self._chunk_overlap,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        return splitter.split_documents(documents)


class SemanticChunkStrategy(ChunkStrategy):
    """语义切片——基于 embedding 向量相似度自动确定主题边界。"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200,
                 embedding_model=None):
        if embedding_model is None:
            raise ValueError("语义切分策略需要一个嵌入模型。")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._embedding_model = embedding_model

    def split(self, documents: list[Document]) -> list[Document]:
        from langchain_experimental.text_splitter import SemanticChunker
        splitter = SemanticChunker(
            embeddings=self._embedding_model,
            breakpoint_threshold_type="percentile",
        )
        return splitter.split_documents(documents)


class MarkdownChunkStrategy(ChunkStrategy):
    """Markdown 结构切片——按标题层级切分。"""

    def split(self, documents: list[Document]) -> list[Document]:
        from langchain_text_splitters import MarkdownHeaderTextSplitter
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4"),
            ],
            strip_headers=True,
        )
        results: list[Document] = []
        for doc in documents:
            chunks = splitter.split_text(doc.page_content)
            for i, chunk in enumerate(chunks):
                chunk.metadata.update(doc.metadata)
                chunk.metadata["chunk_index"] = i
            results.extend(chunks)
        return results


class AgenticChunkStrategy(ChunkStrategy):
    """Agentic 智能切片——调用 LLM 判断主题边界（规划中）。"""

    def __init__(self, llm=None, chunk_size: int = 512, chunk_overlap: int = 64):
        self._llm = llm
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        raise NotImplementedError("AgenticChunkStrategy: 将在后续版本实现")


class ChunkStrategyRegistry:
    """切片策略注册表。"""

    def __init__(self):
        self._strategies: dict[str, ChunkStrategy] = {}

    def register(self, name: str, strategy: ChunkStrategy) -> None:
        self._strategies[name] = strategy

    def get(self, name: str) -> ChunkStrategy:
        if name not in self._strategies:
            raise ValueError(f"Unknown chunk strategy: {name}")
        return self._strategies[name]

    def split(self, name: str, documents: list[Document]) -> list[Document]:
        return self.get(name).split(documents)


def create_chunk_registry(config: dict, embedding_model=None, llm=None) -> ChunkStrategyRegistry:
    """根据索引配置创建切片注册表。

    仅注册 embedding_model 可用的策略（semantic 需要 embedding，agentic 需要 llm）。
    """
    chunk_size = config.get("chunk_size", 1000)
    chunk_overlap = config.get("chunk_overlap", 200)

    registry = ChunkStrategyRegistry()
    registry.register("fixed", FixedChunkStrategy(chunk_size, chunk_overlap))
    registry.register("recursive", RecursiveChunkStrategy(chunk_size, chunk_overlap))
    registry.register("markdown", MarkdownChunkStrategy())

    if embedding_model is not None:
        registry.register("semantic", SemanticChunkStrategy(chunk_size, chunk_overlap, embedding_model))

    if llm is not None:
        registry.register("agentic", AgenticChunkStrategy(llm, chunk_size, chunk_overlap))

    return registry
