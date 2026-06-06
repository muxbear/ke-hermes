from typing import Literal

from tavily import TavilyClient

from agent.config import settings

_tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

def tavily_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search via Tavily."""
    return _tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
