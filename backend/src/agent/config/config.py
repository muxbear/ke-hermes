from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_EMBEDDING: str = "text-embedding-v4"
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    HOST: str = "127.0.0.1"
    PORT: int = 8000