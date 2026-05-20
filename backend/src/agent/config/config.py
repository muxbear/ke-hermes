from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # ---- LLM (DeepSeek) ----
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL")

    # ---- Embeddings (DashScope) ----
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY")
    DASHSCOPE_EMBEDDING: str = os.getenv("DASHSCOPE_EMBEDDING")
    DASHSCOPE_BASE_URL: str = os.getenv("DASHSCOPE_BASE_URL")

    # ---- Tavily ----
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY")

    # ---- Server ----
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = os.getenv("PORT", 8000)

    # ---- Database ----
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # ---- JWT ----
    JWT_SECRET_KEY: str = ""
    JWT_ACCESS_EXPIRE: int = os.getenv("JWT_ACCESS_EXPIRE", 7200)
    JWT_REFRESH_EXPIRE: int = os.getenv("JWT_REFRESH_EXPIRE", 604800)

    # ---- RSA ----
    RSA_KEY_SIZE: int = os.getenv("RSA_KEY_SIZE", 2048)

    # ---- Rate Limit ----
    LOGIN_MAX_FAILS: int = os.getenv("LOGIN_MAX_FAILS", 5)
    LOGIN_LOCK_MINUTES: int = os.getenv("LOGIN_LOCK_MINUTES", 30)
    SMS_DAILY_LIMIT: int = os.getenv("SMS_DAILY_LIMIT", 5)

    # ---- Captcha ----
    CAPTCHA_EXPIRE: int = os.getenv("CAPTCHA_EXPIRE", 300)
    SLIDE_THRESHOLD: int = os.getenv("SLIDE_THRESHOLD", 5)

    # ---- Redis ----
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    # ---- OAuth ----
    OAUTH_GITHUB_CLIENT_ID: str = os.getenv("OAUTH_GITHUB_CLIENT_ID", "")
    OAUTH_GITHUB_CLIENT_SECRET: str = os.getenv("OAUTH_GITHUB_CLIENT_SECRET", "")
    OAUTH_GOOGLE_CLIENT_ID: str = ""
    OAUTH_GOOGLE_CLIENT_SECRET: str = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "")
    OAUTH_WECHAT_CLIENT_ID: str = os.getenv("OAUTH_WECHAT_CLIENT_ID", "")
    OAUTH_WECHAT_CLIENT_SECRET: str = os.getenv("OAUTH_WECHAT_CLIENT_SECRET", "")

    # ---- SMS ----
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "")
    SMS_ACCESS_KEY: str = os.getenv("SMS_ACCESS_KEY", "")
    SMS_SECRET_KEY: str = os.getenv("SMS_SECRET_KEY", "")
    SMS_SIGN_NAME: str = os.getenv("SMS_SIGN_NAME", "")
    SMS_TEMPLATE_CODE: str = os.getenv("SMS_TEMPLATE_CODE", "")
