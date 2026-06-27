"""GitHub OAuth 提供者。"""

from api.oauth.providers.base import OAuthProvider, OAuthUserInfo


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth 2.0 适配器。"""

    name = "github"

    def normalize_user_info(self, raw: dict) -> OAuthUserInfo:
        return OAuthUserInfo(
            open_id=str(raw.get("id", "")),
            nickname=raw.get("login", ""),
            avatar=raw.get("avatar_url", ""),
            email=raw.get("email", ""),
        )
