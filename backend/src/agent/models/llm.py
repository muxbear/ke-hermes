from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from agent.config import settings

llm = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,
    api_key=SecretStr(settings.DEEPSEEK_API_KEY),
    base_url=settings.DEEPSEEK_BASE_URL,
    extra_body={"thinking": {"type": "disabled"}}  # 关闭 deepseek 的思考过程
)

qwen_llm = ChatOpenAI(
    model="qwen3.6-plus",
    api_key=SecretStr(settings.DASHSCOPE_API_KEY),
    base_url=settings.DASHSCOPE_BASE_URL
)

__all__ = ["llm", "qwen_llm"]