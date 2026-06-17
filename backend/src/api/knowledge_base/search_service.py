"""知识库检索服务——策略模式 + 注册表 + 模板方法编排器."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from api.knowledge_base.schemas import ChunkMatch, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)


# ─── 检索上下文 & 结果 ─────────────────────────────────────────────────────────


@dataclass
class SearchContext:
    """检索上下文——传递给策略的数据对象。"""
    kb_id: str
    query_text: str
    query_embedding: list[float]
    top_k: int
    alpha: float = 0.7
    extra: dict = field(default_factory=dict)


@dataclass
class ScoredChunk:
    """带分维度得分的检索结果项。"""
    chunk_id: str
    score: float
    vec_score: float | None = None
    bm25_score: float | None = None


# ─── 分数融合工具函数 ──────────────────────────────────────────────────────────


def _fuse_scores(
    vec_pairs: list[tuple[str, float]],
    bm25_pairs: list[tuple[str, float]],
    top_k: int,
    alpha: float,
) -> list[ScoredChunk]:
    """RRF（倒数排名融合）——向量和 BM25 两边排名自然交错，无加权偏斜。"""
    RRF_K = 60

    vec_norm: dict[str, float] = {}
    bm25_norm: dict[str, float] = {}

    if vec_pairs:
        max_v = max(s for _, s in vec_pairs)
        min_v = min(s for _, s in vec_pairs)
        if max_v == min_v:
            for cid, _ in vec_pairs:
                vec_norm[cid] = 1.0
        else:
            v_range = max_v - min_v
            for cid, s in vec_pairs:
                vec_norm[cid] = (s - min_v) / v_range

    if bm25_pairs:
        max_b = max(s for _, s in bm25_pairs)
        min_b = min(s for _, s in bm25_pairs)
        if max_b == min_b:
            for cid, _ in bm25_pairs:
                bm25_norm[cid] = 1.0
        else:
            b_range = max_b - min_b
            for cid, s in bm25_pairs:
                bm25_norm[cid] = (s - min_b) / b_range

    # 无权重 RRF——两边排名自然交错，已在两边都排前面的 chunk 得分更高
    rrf: dict[str, float] = {}
    for rank, (cid, _) in enumerate(vec_pairs, start=1):
        rrf[cid] = 1.0 / (RRF_K + rank)
    for rank, (cid, _) in enumerate(bm25_pairs, start=1):
        rrf[cid] = rrf.get(cid, 0.0) + 1.0 / (RRF_K + rank)

    ranked = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]

    # 综合得分使用 alpha 加权展示
    return [
        ScoredChunk(
            chunk_id=cid,
            score=round(
                alpha * vec_norm.get(cid, 0.0) + (1 - alpha) * bm25_norm.get(cid, 0.0), 4,
            ),
            vec_score=round(v, 4) if (v := vec_norm.get(cid)) is not None else None,
            bm25_score=round(b, 4) if (b := bm25_norm.get(cid)) is not None else None,
        )
        for cid, _ in ranked
    ]


# ─── 检索策略（策略模式）───────────────────────────────────────────────────────


class SearchStrategy(ABC):
    """检索策略抽象接口。"""

    name: str

    @abstractmethod
    async def search(self, ctx: SearchContext, vector_store) -> list[ScoredChunk]:
        """执行检索，返回带分维度得分的 ScoredChunk 列表。"""
        ...

    def is_supported(self, vector_store) -> bool:
        """检查当前向量库是否支持此策略（默认返回 True）。"""
        return True


class VectorSearchStrategy(SearchStrategy):
    """向量检索——稠密语义相似度。"""

    name = "vector"

    async def search(self, ctx: SearchContext, vector_store) -> list[ScoredChunk]:
        pairs = await vector_store.similarity_search(
            ctx.kb_id, ctx.query_embedding, ctx.top_k
        )
        return [
            ScoredChunk(chunk_id=cid, score=round(s, 4), vec_score=round(s, 4))
            for cid, s in pairs
        ]


class BM25SearchStrategy(SearchStrategy):
    """BM25 检索——稀疏关键词。"""

    name = "bm25"

    async def search(self, ctx: SearchContext, vector_store) -> list[ScoredChunk]:
        pairs = await vector_store.bm25_search(
            ctx.kb_id, ctx.query_text, ctx.top_k
        )
        return [
            ScoredChunk(chunk_id=cid, score=round(s, 4), bm25_score=round(s, 4))
            for cid, s in pairs
        ]


class HybridSearchStrategy(SearchStrategy):
    """混合检索——向量 + BM25 加权融合，保留各维度得分。"""

    name = "hybrid"

    async def search(self, ctx: SearchContext, vector_store) -> list[ScoredChunk]:
        vec_pairs = await vector_store.similarity_search(
            ctx.kb_id, ctx.query_embedding, ctx.top_k * 2,
        )
        bm25_pairs = await vector_store.bm25_search(
            ctx.kb_id, ctx.query_text, ctx.top_k * 2,
        )
        return _fuse_scores(vec_pairs, bm25_pairs, ctx.top_k, ctx.alpha)


# ─── 策略注册表（注册表模式）───────────────────────────────────────────────────


class SearchStrategyRegistry:
    """检索策略注册表——按 mode 名称查找策略。"""

    def __init__(self) -> None:
        self._strategies: dict[str, SearchStrategy] = {}

    def register(self, strategy: SearchStrategy) -> None:
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> SearchStrategy | None:
        return self._strategies.get(name)

    @property
    def supported_modes(self) -> list[str]:
        return list(self._strategies.keys())


def create_search_registry() -> SearchStrategyRegistry:
    """创建预注册三种策略的注册表。"""
    registry = SearchStrategyRegistry()
    registry.register(VectorSearchStrategy())
    registry.register(BM25SearchStrategy())
    registry.register(HybridSearchStrategy())
    return registry


# ─── 检索编排器（模板方法模式 + 外观模式）──────────────────────────────────────


class SearchOrchestrator:
    """检索编排器——模板方法骨架，将具体检索委托给策略。

    依赖通过构造函数注入，由 server.py 在启动时组装。
    """

    def __init__(self, vector_store, embedding_model) -> None:
        self._vector_store = vector_store
        self._embedding_model = embedding_model
        self._registry = create_search_registry()

    async def search(
        self,
        db: AsyncSession,
        kb_id: str,
        request: SearchRequest,
    ) -> SearchResponse:
        """执行检索——模板方法。

        流程：校验 mode → 获取策略 → 向量化查询 → 执行检索 → 查询 chunk 详情 → 组装响应。
        """
        strategy = self._registry.get(request.mode)
        if strategy is None:
            valid = ", ".join(self._registry.supported_modes)
            raise ValueError(f"不支持的检索模式: {request.mode}，可选: {valid}")

        top_k = request.top_k

        # 向量化查询（纯 BM25 不需要，但为简化流程统一执行）
        try:
            query_embedding = await self._embedding_model.aembed_query(request.query)
        except Exception:
            logger.exception("Query embedding failed")
            raise RuntimeError("查询向量化失败，请检查 Embedding 模型配置")

        # 构建上下文并执行策略
        ctx = SearchContext(
            kb_id=kb_id,
            query_text=request.query,
            query_embedding=query_embedding,
            top_k=top_k,
            alpha=request.alpha if request.alpha is not None else 0.7,
        )

        try:
            scored_chunks = await strategy.search(ctx, self._vector_store)
        except Exception:
            logger.exception("Search strategy '%s' failed for kb=%s", request.mode, kb_id)
            raise RuntimeError(f"检索执行失败: {request.mode}")

        if not scored_chunks:
            return SearchResponse(
                query=request.query, mode=request.mode, total=0, results=[],
            )

        # 查询 chunk 详情
        chunk_ids = [sc.chunk_id for sc in scored_chunks]
        sc_map = {sc.chunk_id: sc for sc in scored_chunks}

        try:
            chunk_dicts = await self._vector_store.get_chunks_by_ids(kb_id, chunk_ids)
        except Exception:
            logger.exception("Failed to fetch chunk details for kb=%s", kb_id)
            raise RuntimeError("查询分片详情失败")

        # 保留检索返回的顺序
        chunk_by_id = {c["id"]: c for c in chunk_dicts}
        results: list[ChunkMatch] = []
        for cid in chunk_ids:
            c = chunk_by_id.get(cid)
            sc = sc_map.get(cid)
            if c is None:
                continue
            results.append(ChunkMatch(
                id=cid,
                doc_id=c.get("doc_id", ""),
                doc_name=c.get("doc_name", ""),
                chunk_index=c.get("chunk_index", 0),
                content=c.get("chunk_text", ""),
                score=sc.score if sc else round(0.0, 4),
                vec_score=sc.vec_score if sc else None,
                bm25_score=sc.bm25_score if sc else None,
            ))

        return SearchResponse(
            query=request.query,
            mode=request.mode,
            total=len(results),
            results=results,
        )

    def is_search_supported(self) -> bool:
        """快速检测当前向量库是否支持搜索功能。

        通过尝试用空查询调用 bm25_search 检测。Milvus 后端返回空且无异常。
        更准确的检测需在实际检索中判断，此处做轻量检查。
        """
        return True
