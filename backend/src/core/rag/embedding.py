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
    """

    def __init__(self, model: str, api_base: str, api_key: str, dimensions: int | None = None):
        self.model = model
        self._base = api_base.rstrip("/")
        self._key = api_key
        self._dimensions = dimensions

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量向量化文本。"""
        payload: dict = {"model": self.model, "input": texts}
        if self._dimensions:
            payload["dimensions"] = self._dimensions

        async with httpx.AsyncClient(timeout=60) as client:
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
    return OpenAIEmbeddings(
        model=model_name,
        openai_api_base=api_base,
        openai_api_key=api_key,
        dimensions=dimensions,
        **kwargs,
    )
