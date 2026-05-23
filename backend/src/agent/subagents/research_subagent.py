from agent.models import qwen_llm

import os
from typing import Literal

from tavily import TavilyClient
from deepagents import create_deep_agent
from agent.config import settings

tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

research_subagent = {
    "name": "research-agent",
    "description": "通过调用互联网检索引擎检索问题。",
    "system_prompt": "你是一个互联网检索智能体，可用调用多种工具检索你要的信息",
    "tools": [internet_search],
    "model": qwen_llm
}

__all__ = ["research_subagent"]