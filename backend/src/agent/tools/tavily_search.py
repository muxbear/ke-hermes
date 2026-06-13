"""Tavily 网络搜索系统工具，支持深度搜索、时间范围过滤、AI 摘要等功能。"""

from typing import Any, Literal, cast

from tavily import TavilyClient

from agent.config import settings

_tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


def tavily_search(
    query: str,
    search_depth: str = "basic",
    topic: str = "general",
    time_range: str | None = None,
    max_results: int = 10,
    include_answer: bool = True,
    include_raw_content: bool = False,
) -> dict[str, Any]:
    """通过 Tavily Search API 对互联网进行实时检索，返回搜索结果、AI 摘要及来源 URL。

    Args:
        query: 搜索关键词或问题。
        search_depth: 搜索深度，"basic" 快速搜索（1-2秒），"advanced" 深度搜索（5-10秒，结果更全）。
        topic: 搜索主题，"general" 通用搜索，"news" 新闻搜索，"finance" 金融搜索。
        time_range: 时间过滤，"day" 一天内 / "week" 一周内 / "month" 一月内 / "year" 一年内。不传则不限制。
        max_results: 返回的最大结果数，默认 10，范围 1-20。
        include_answer: 是否返回 AI 生成的摘要回答，默认开启。
        include_raw_content: 是否包含原始网页 Markdown 内容，默认关闭。

    Returns:
        包含以下字段的字典：
            - query: 实际搜索关键词
            - results: 搜索结果列表 [{title, url, content, score, raw_content}]
            - answer: AI 生成的摘要回答（include_answer=True 时）
            - images: 相关图片列表
            - response_time: 响应耗时（秒）
    """
    if search_depth not in ("basic", "advanced"):
        search_depth = "basic"
    if topic not in ("general", "news", "finance"):
        topic = "general"
    if time_range not in (None, "day", "week", "month", "year"):
        time_range = None
    if max_results < 1:
        max_results = 1
    elif max_results > 20:
        max_results = 20

    if time_range:
        result = _tavily_client.search(
            query=query,
            search_depth=search_depth,  # type: ignore[arg-type]
            topic=topic,  # type: ignore[arg-type]
            time_range=cast(Literal["day", "week", "month", "year"], time_range),
            max_results=max_results,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
        )
    else:
        result = _tavily_client.search(
            query=query,
            search_depth=search_depth,  # type: ignore[arg-type]
            topic=topic,  # type: ignore[arg-type]
            max_results=max_results,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
        )

    # 补充 query 信息，帮助 LLM 理解结果上下文
    result["query"] = result.get("query", query)

    return result


__all__ = ["tavily_search"]
