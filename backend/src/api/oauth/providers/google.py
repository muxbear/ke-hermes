"""Google OAuth 提供者。"""

from api.oauth.providers.base import OAuthProvider, OAuthUserInfo


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth 2.0 适配器。"""

    name = "google"

    def normalize_user_info(self, raw: dict) -> OAuthUserInfo:
        return OAuthUserInfo(
            open_id=str(raw.get("id", "")),
            nickname=raw.get("name", ""),
            avatar=raw.get("picture", ""),
            email=raw.get("email", ""),
        )
