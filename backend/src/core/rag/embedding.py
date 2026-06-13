"""Embedding 模型工厂。

对 DashScope 等非 OpenAI 原生 API，使用 httpx 直接调用以避免
OpenAIEmbeddings 自动 tokenize 输入（tiktoken）或从 HuggingFace 下载 tokenizer。
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class _DashScopeEmbeddings:
    """DashScope Embedding 模型（兼容 OpenAI API 格式的文本向量化）。

    直接使用 httpx 发送原始文本，避免 OpenAIEmbeddings 的 tokenize 行为。
    DashScope API 单次批量上限 10 条，自动分批。
    """

    _BATCH_SIZE = 10  # DashScope 兼容模式 API 限制

    def __init__(self, model: str, api_base: str, api_key: str, dimensions: int | None = None):
        self.model = model
        self._base = api_base.rstrip("/")
        self._key = api_key
        self._dimensions = dimensions

    async def _embed_batch(self, texts: list[str], client: httpx.AsyncClient) -> list[list[float]]:
        """发送单次 embedding 请求（≤_BATCH_SIZE 条）。"""
        payload: dict = {"model": self.model, "input": texts}
        if self._dimensions:
            payload["dimensions"] = self._dimensions

        resp = await client.post(
            f"{self._base}/embeddings",
            headers={
                "Authorization": f"Bearer {self._key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        if "data" not in data:
            raise RuntimeError(f"Embedding API error: {data}")
        return [item["embedding"] for item in data["data"]]

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量向量化文本，自动分片以符合 API 限制。"""
        if len(texts) <= self._BATCH_SIZE:
            async with httpx.AsyncClient(timeout=60) as client:
                return await self._embed_batch(texts, client)

        results: list[list[float]] = []
        async with httpx.AsyncClient(timeout=120) as client:
            for i in range(0, len(texts), self._BATCH_SIZE):
                batch = texts[i:i + self._BATCH_SIZE]
                batch_results = await self._embed_batch(batch, client)
                results.extend(batch_results)
                logger.debug("Embedded batch %d/%d", i // self._BATCH_SIZE + 1,
                           (len(texts) + self._BATCH_SIZE - 1) // self._BATCH_SIZE)
        return results

    async def aembed_query(self, text: str) -> list[float]:
        """单条文本向量化。"""
        results = await self.aembed_documents([text])
        return results[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """同步向量化（内部调用异步版）。"""
        import asyncio
        return asyncio.run(self.aembed_documents(texts))

    def embed_query(self, text: str) -> list[float]:
        """同步单条向量化。"""
        import asyncio
        return asyncio.run(self.aembed_query(text))


def get_embedding_model(model_name: str, api_base: str, api_key: str,
                        dimensions: int | None = None, **kwargs):
    """获取 Embedding 模型实例。

    对 DashScope API 使用 httpx 直接调用（避免 OpenAIEmbeddings 的 tokenize 问题）。
    对 OpenAI 原生 API 使用 langchain_openai.OpenAIEmbeddings。
    """
    if "dashscope" in api_base:
        return _DashScopeEmbeddings(
            model=model_name,
            api_base=api_base,
            api_key=api_key,
            dimensions=dimensions,
        )

    from langchain_openai import OpenAIEmbeddings
    from pydantic import SecretStr

    return OpenAIEmbeddings(
        model=model_name,
        base_url=api_base,
        api_key=SecretStr(api_key),
        dimensions=dimensions,
        **kwargs,
    )
