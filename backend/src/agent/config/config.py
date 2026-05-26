from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


def get_default_workspace() -> str:
    """Return the agent filesystem workspace directory.

    Uses ``WORKSPACE`` from the environment when set to a non-empty path;
    otherwise resolves to ``backend/workspace`` under the backend package root.
    """
    env = os.getenv("WORKSPACE", "").strip()
    if env:
        return os.path.abspath(env)

    # config.py lives at backend/src/agent/config/ — four levels up to backend/
    backend_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    )
    return os.path.join(backend_root, "workspace")


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

    # ---- Workspace ----
    WORKSPACE: str = Field(default_factory=get_default_workspace)

    @field_validator("WORKSPACE", mode="before")
    @classmethod
    def _workspace_use_default_when_empty(cls, value: object) -> str:
        if value is None or (isinstance(value, str) and not value.strip()):
            return get_default_workspace()
        return str(value)

    # ---- Database ----
    DATABASE_BACKEND: str = os.getenv("DATABASE_BACKEND", "sqlite")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH")


    # ---- Checkpoint Database
    CHECKPOINT_BACKEND: str = os.getenv("CHECKPOINT_BACKEND", "sqlite")
    CHECKPOINT_DB_URL: str = os.getenv("CHECKPOINT_DB_URL", "postgresql://127.0.0.1:5432/ke_hermes")
    CHECKPOINT_DB_PATH: str = os.getenv("CHECKPOINT_DB_PATH", "./db/ke_hermes.db")

    # ---- Store Database
    STORE_BACKEND: str = os.getenv("STORE_BACKEND", "sqlite")
    STORE_DB_URL: str = os.getenv("STORE_DB_URL", "postgresql://127.0.0.1:5432/ke_hermes")
    STORE_DB_PATH: str = os.getenv("STORE_DB_PATH", "./db/ke_hermes.db")

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
    SLIDE_THRESHOLD: int = os.getenv("SLIDE_THRESHOLD", 8)

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
