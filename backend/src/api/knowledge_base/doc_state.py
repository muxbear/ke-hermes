"""文档索引状态机——状态模式。

定义文档在索引流水线中的 8 种状态及其转换规则。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Awaitable

if TYPE_CHECKING:
    from api.knowledge_base.doc_service import IndexingPipeline
    from core.rag.splitters import ChunkStrategyRegistry

logger = logging.getLogger(__name__)


@dataclass
class IndexingContext:
    """索引上下文——状态模式中的 Context 角色。

    持有当前文档的索引状态、阶段产物，以及各阶段的执行回调。
    """
    doc_id: str
    kb_id: str
    file_path: str
    file_type: str
    config: dict

    current_state: DocState | None = None
    status: str = "queued"
    progress: int = 0
    error_message: str | None = None

    documents: list = field(default_factory=list)
    chunks: list = field(default_factory=list)
    embeddings: list = field(default_factory=list)
    entities_count: int = 0
    relations_count: int = 0

    embedding_model: Any | None = None
    chunk_registry: ChunkStrategyRegistry | None = None

    on_status_change: Callable[["IndexingContext"], Awaitable[None]] | None = None

    async def transition_to(self, state: DocState, status: str, progress: int) -> None:
        self.current_state = state
        self.status = status
        self.progress = progress
        if self.on_status_change:
            await self.on_status_change(self)

    async def fail(self, error: str) -> None:
        self.error_message = error
        await self.transition_to(FailedState(), "failed", -1)


class DocState(ABC):
    """文档索引状态抽象接口。"""

    name: str

    @abstractmethod
    async def handle(self, ctx: IndexingContext, pipeline: IndexingPipeline) -> None:
        """执行当前状态的处理逻辑。"""
        ...


class QueuedState(DocState):
    name = "queued"

    async def handle(self, ctx: IndexingContext, pipeline: IndexingPipeline) -> None:
        await ctx.transition_to(ParsingState(), "parsing", 3)


class ParsingState(DocState):
    name = "parsing"

    async def handle(self, ctx: IndexingContext, pipeline: IndexingPipeline) -> None:
        try:
            ctx.documents = pipeline.loader_registry.load(ctx.file_path, ctx.file_type)
            await ctx.transition_to(ChunkingState(), "chunking", 15)
        except Exception as e:
            await ctx.fail(f"文档解析失败: {e}")


class ChunkingState(DocState):
    name = "chunking"

    async def handle(self, ctx: IndexingContext, pipeline: IndexingPipeline) -> None:
        try:
            strategy_name = ctx.config.get("chunk_strategy", "recursive")
            chunk_reg = ctx.chunk_registry or pipeline.chunk_registry
            ctx.chunks = chunk_reg.split(strategy_name, ctx.documents)
            await ctx.transition_to(EmbeddingState(), "embedding", 30)
        except Exception as e:
            await ctx.fail(f"文本切片失败: {e}")


class EmbeddingState(DocState):
    name = "embedding"

    async def handle(self, ctx: IndexingContext, pipeline: IndexingPipeline) -> None:
        try:
            texts = [chunk.page_content for chunk in ctx.chunks]
            emb_model = ctx.embedding_model or pipeline.embedding_model
            ctx.embeddings = await emb_model.aembed_documents(texts)
            await ctx.transition_to(BM25State(), "bm25", 55)
        except Exception as e:
            await ctx.fail(f"向量化失败: {e}")


class BM25State(DocState):
    name = "bm25"

    async def handle(self, ctx: IndexingContext, pipeline: IndexingPipeline) -> None:
        import logging
        _logger = logging.getLogger(__name__)
        try:
            # Inject doc-level metadata into every chunk before storing
            doc_name = ctx.file_path.replace("\\", "/").rsplit("/", 1)[-1]
            header_keys = {"h1", "h2", "h3", "h4", "h5", "h6"}
            for i, chunk in enumerate(ctx.chunks):
                if not chunk.metadata.get("doc_id"):
                    chunk.metadata["doc_id"] = ctx.doc_id
                if not chunk.metadata.get("chunk_index"):
                    chunk.metadata["chunk_index"] = i
                chunk.metadata["doc_name"] = doc_name
                chunk.metadata["doc_type"] = ctx.file_type
                # Collect header/section info from splitter metadata
                extra_meta = chunk.metadata.get("metadata_", {})
                for k in header_keys:
                    if k in chunk.metadata:
                        extra_meta[k] = chunk.metadata[k]
                chunk.metadata["metadata_"] = extra_meta

            await pipeline.vector_store.add_documents(ctx.kb_id, ctx.chunks, ctx.embeddings)
            await ctx.transition_to(ExtractingState(), "extracting", 70)
        except Exception as e:
            _logger.exception("BM25 add_documents failed for doc=%s kb=%s", ctx.doc_id, ctx.kb_id)
            await ctx.fail(f"BM25 索引失败: {e}")


class ExtractingState(DocState):
    name = "extracting"

    async def handle(self, ctx: IndexingContext, pipeline: IndexingPipeline) -> None:
        import logging
        _logger = logging.getLogger(__name__)
        try:
            # 兼容前端 camelCase 和后端 snake_case 两种 key 格式
            enable_graph = (
                ctx.config.get("enable_graph", None)
                or ctx.config.get("enableGraph", None)
            )
            if enable_graph is not False:  # 默认开启
                _logger.info("Running graph extraction for doc=%s", ctx.doc_id)
                entities, relations = await pipeline.graph_service.extract_entities_and_relations(
                    ctx.kb_id, ctx.doc_id, ctx.chunks,
                )
                ctx.entities_count = len(entities)
                ctx.relations_count = len(relations)
            await ctx.transition_to(IndexedState(), "indexed", 100)
        except Exception:
            _logger.exception("Entity extraction failed for doc=%s", ctx.doc_id)
            # 抽取失败不阻塞索引——文档仍然标记为已索引
            await ctx.transition_to(IndexedState(), "indexed", 100)


class IndexedState(DocState):
    name = "indexed"

    async def handle(self, ctx: IndexingContext, pipeline: IndexingPipeline) -> None:
        pass


class FailedState(DocState):
    name = "failed"

    async def handle(self, ctx: IndexingContext, pipeline: IndexingPipeline) -> None:
        pass
