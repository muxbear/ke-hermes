from langchain_openai import ChatOpenAI

from agent.config import settings

llm = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    extra_body={"thinking": {"type": "disabled"}} # 关闭 deepseek 的思考过程
)

__all__ = ["llm"]