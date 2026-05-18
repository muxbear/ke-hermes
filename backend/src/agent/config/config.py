from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ---- LLM (DeepSeek) ----
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # ---- Embeddings (DashScope) ----
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_EMBEDDING: str = "text-embedding-v4"
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ---- Server ----
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # ---- Database ----
    DATABASE_URL: str = "sqlite+aiosqlite:///./ke-hermes.db"

    # ---- JWT ----
    JWT_SECRET_KEY: str = ""
    JWT_ACCESS_EXPIRE: int = 7200
    JWT_REFRESH_EXPIRE: int = 604800

    # ---- RSA ----
    RSA_KEY_SIZE: int = 2048

    # ---- Rate Limit ----
    LOGIN_MAX_FAILS: int = 5
    LOGIN_LOCK_MINUTES: int = 30
    SMS_DAILY_LIMIT: int = 5

    # ---- Captcha ----
    CAPTCHA_EXPIRE: int = 300
    SLIDE_THRESHOLD: int = 5

    # ---- Redis ----
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # ---- OAuth ----
    OAUTH_GITHUB_CLIENT_ID: str = ""
    OAUTH_GITHUB_CLIENT_SECRET: str = ""
    OAUTH_GOOGLE_CLIENT_ID: str = ""
    OAUTH_GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_WECHAT_CLIENT_ID: str = ""
    OAUTH_WECHAT_CLIENT_SECRET: str = ""

    # ---- SMS ----
    SMS_PROVIDER: str = ""
    SMS_ACCESS_KEY: str = ""
    SMS_SECRET_KEY: str = ""
    SMS_SIGN_NAME: str = ""
    SMS_TEMPLATE_CODE: str = ""
