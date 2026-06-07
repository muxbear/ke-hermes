import os

import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="module")
def api_key():
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        pytest.skip("TAVILY_API_KEY not set")
    return key


def _search(**kwargs):
    from tavily import TavilyClient
    from agent.config import settings
    client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return client.search(**kwargs)


class TestTavilyBasic:
    def test_search_returns_results(self, api_key):
        result = _search(query="Python FastAPI", max_results=3, topic="general")
        assert "results" in result
        assert len(result["results"]) > 0
        assert len(result["results"]) <= 3

    def test_result_structure(self, api_key):
        result = _search(query="weather today", max_results=1)
        r = result["results"][0]
        for field in ("title", "url", "content"):
            assert field in r, f"Missing field: {field}"
            assert isinstance(r[field], str)
            assert len(r[field]) > 0

    def test_result_has_score(self, api_key):
        result = _search(query="machine learning", max_results=1)
        assert "score" in result["results"][0]


class TestTavilySearchDepth:
    def test_basic_search_depth(self, api_key):
        result = _search(query="Rust programming language", search_depth="basic", max_results=2)
        assert len(result["results"]) > 0

    def test_advanced_search_depth(self, api_key):
        result = _search(query="Rust programming language", search_depth="advanced", max_results=2)
        assert len(result["results"]) > 0


class TestTavilyTopic:
    def test_general_topic(self, api_key):
        result = _search(query="Python 3.12", topic="general", max_results=2)
        assert len(result["results"]) > 0

    def test_news_topic(self, api_key):
        result = _search(query="AI technology", topic="news", max_results=2)
        assert len(result["results"]) > 0

    def test_finance_topic(self, api_key):
        result = _search(query="Apple stock", topic="finance", max_results=2)
        assert len(result["results"]) > 0


class TestTavilyIncludeAnswer:
    def test_include_answer_enabled(self, api_key):
        result = _search(query="What is GraphQL", max_results=2, include_answer=True)
        assert "answer" in result
        answer = result.get("answer")
        assert answer is not None and len(answer) > 0

    def test_include_raw_content(self, api_key):
        result = _search(query="TypeScript vs JavaScript", max_results=1, include_raw_content=True)
        r = result["results"][0]
        assert "raw_content" in r


class TestTavilyMaxResults:
    def test_single_result(self, api_key):
        result = _search(query="Django framework", max_results=1)
        assert len(result["results"]) == 1

    def test_multiple_results(self, api_key):
        result = _search(query="React hooks", max_results=5)
        assert 1 <= len(result["results"]) <= 5


class TestTavilyTimeRange:
    def test_time_range_day(self, api_key):
        result = _search(query="latest tech news", time_range="day", max_results=2)
        assert isinstance(result, dict)
        assert "results" in result

    def test_time_range_week(self, api_key):
        result = _search(query="newest AI models", time_range="week", max_results=2)
        assert isinstance(result, dict)


class TestTavilyChinese:
    def test_chinese_query(self, api_key):
        result = _search(query="大语言模型最新进展", max_results=3, include_answer=True)
        assert len(result["results"]) > 0

    def test_chinese_query_with_advanced_depth(self, api_key):
        result = _search(query="Python 异步编程教程", search_depth="advanced", max_results=2)
        assert len(result["results"]) > 0
