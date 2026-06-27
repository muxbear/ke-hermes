"""OAuth 提供者注册表——策略模式。"""

from api.oauth.providers.base import OAuthConfig, OAuthProvider, OAuthUserInfo

_providers: dict[str, OAuthProvider] = {}


def _create_providers() -> None:
    """懒加载创建 OAuth 提供者实例（需要 settings 可用时调用）。"""
    from agent.config import settings
    from api.oauth.providers.github import GitHubOAuthProvider
    from api.oauth.providers.google import GoogleOAuthProvider
    from api.oauth.providers.wechat import WeChatOAuthProvider

    _providers["github"] = GitHubOAuthProvider(
        OAuthConfig(
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            scope="read:user",
            client_id=settings.OAUTH_GITHUB_CLIENT_ID,
            client_secret=settings.OAUTH_GITHUB_CLIENT_SECRET,
        )
    )
    _providers["google"] = GoogleOAuthProvider(
        OAuthConfig(
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
            scope="openid profile email",
            client_id=settings.OAUTH_GOOGLE_CLIENT_ID,
            client_secret=settings.OAUTH_GOOGLE_CLIENT_SECRET,
        )
    )
    _providers["wechat"] = WeChatOAuthProvider(
        OAuthConfig(
            auth_url="https://open.weixin.qq.com/connect/qrconnect",
            token_url="https://api.weixin.qq.com/sns/oauth2/access_token",
            userinfo_url="https://api.weixin.qq.com/sns/userinfo",
            scope="snsapi_login",
            client_id=settings.OAUTH_WECHAT_CLIENT_ID,
            client_secret=settings.OAUTH_WECHAT_CLIENT_SECRET,
        )
    )


def get_oauth_provider(name: str) -> OAuthProvider:
    """获取 OAuth 提供者实例，首次调用时懒加载。"""
    if not _providers:
        _create_providers()
    if name not in _providers:
        raise ValueError(f"Unsupported OAuth provider: {name}")
    return _providers[name]


def list_providers() -> list[str]:
    """列出所有支持的 OAuth 提供者名称。"""
    if not _providers:
        _create_providers()
    return list(_providers.keys())
