"""微信 OAuth 提供者。"""

from api.oauth.providers.base import OAuthProvider, OAuthUserInfo


class WeChatOAuthProvider(OAuthProvider):
    """微信开放平台 OAuth 2.0 适配器。"""

    name = "wechat"

    def build_auth_url(self, state: str) -> str:
        """微信使用 appid 参数名，且需要 #wechat_redirect 片段。"""
        return (
            f"{self._config.auth_url}?"
            f"appid={self._config.client_id}&"
            f"redirect_uri={self._redirect_uri}&"
            f"scope={self._config.scope}&"
            f"state={state}&"
            f"response_type=code"
            f"#wechat_redirect"
        )

    def get_token_params(self, code: str) -> dict:
        """微信使用 appid/secret 参数名。"""
        return {
            "appid": self._config.client_id,
            "secret": self._config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }

    def normalize_user_info(self, raw: dict) -> OAuthUserInfo:
        return OAuthUserInfo(
            open_id=str(raw.get("openid", "")),
            nickname=raw.get("nickname", ""),
            avatar=raw.get("headimgurl", ""),
            email="",
        )
