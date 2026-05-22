from agent.config.config import Settings


def test_default_values():
    s = Settings(
        DEEPSEEK_API_KEY="test",
        DASHSCOPE_API_KEY="test",
    )
    assert s.DEEPSEEK_MODEL == "deepseek-v4-pro"
    assert s.DASHSCOPE_EMBEDDING == "text-embedding-v4"
    assert s.HOST == "127.0.0.1"
    assert s.PORT == 8000


def test_env_override(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
    monkeypatch.setenv("DEEPSEEK_MODEL", "qwen3.6-plus")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-dashscope-key")

    s = Settings()
    assert s.DEEPSEEK_API_KEY == "sk-test-key"
    assert s.DEEPSEEK_MODEL == "qwen3.6-plus"
    assert s.DASHSCOPE_API_KEY == "sk-dashscope-key"


def test_base_url_defaults(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("DASHSCOPE_BASE_URL", raising=False)
    s = Settings(
        DEEPSEEK_API_KEY="test",
        DASHSCOPE_API_KEY="test",
        DEEPSEEK_BASE_URL="https://api.deepseek.com/v1",
        DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    assert s.DEEPSEEK_BASE_URL == "https://api.deepseek.com/v1"
    assert s.DASHSCOPE_BASE_URL == "https://dashscope.aliyuncs.com/compatible-mode/v1"