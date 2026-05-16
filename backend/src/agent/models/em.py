from langchain_openai import OpenAIEmbeddings

from agent.config import settings

embeddings = OpenAIEmbeddings(
    model=settings.DASHSCOPE_EMBEDDING,
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.DASHSCOPE_BASE_URL,
)

__all__ = ["embeddings"]