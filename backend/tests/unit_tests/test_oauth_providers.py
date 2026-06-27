"""Tests for OAuth provider strategies."""

from api.oauth.providers.base import OAuthConfig, OAuthUserInfo
from api.oauth.providers.github import GitHubOAuthProvider
from api.oauth.providers.google import GoogleOAuthProvider
from api.oauth.providers.wechat import WeChatOAuthProvider


class TestGitHubOAuthProvider:
    def setup_method(self):
        self.config = OAuthConfig(
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            scope="read:user",
            client_id="gh_client_123",
            client_secret="gh_secret_456",
        )
        self.provider = GitHubOAuthProvider(self.config)

    def test_name(self):
        assert self.provider.name == "github"

    def test_build_auth_url(self):
        url = self.provider.build_auth_url("state123")
        assert "client_id=gh_client_123" in url
        assert "state=state123" in url
        assert "response_type=code" in url

    def test_normalize_user_info(self):
        raw = {"id": 1, "login": "octocat", "avatar_url": "http://a.com/1.png", "email": "a@b.com"}
        info = self.provider.normalize_user_info(raw)
        assert info.open_id == "1"
        assert info.nickname == "octocat"
        assert info.avatar == "http://a.com/1.png"

    def test_get_token_params(self):
        params = self.provider.get_token_params("code123")
        assert params["client_id"] == "gh_client_123"
        assert params["code"] == "code123"


class TestGoogleOAuthProvider:
    def setup_method(self):
        self.config = OAuthConfig(
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
            scope="openid profile email",
            client_id="g_client",
            client_secret="g_secret",
        )
        self.provider = GoogleOAuthProvider(self.config)

    def test_normalize_user_info(self):
        raw = {"id": "123", "name": "Test User", "picture": "http://pic", "email": "t@t.com"}
        info = self.provider.normalize_user_info(raw)
        assert info.nickname == "Test User"
        assert info.avatar == "http://pic"


class TestWeChatOAuthProvider:
    def setup_method(self):
        self.config = OAuthConfig(
            auth_url="https://open.weixin.qq.com/connect/qrconnect",
            token_url="https://api.weixin.qq.com/sns/oauth2/access_token",
            userinfo_url="https://api.weixin.qq.com/sns/userinfo",
            scope="snsapi_login",
            client_id="wx_appid",
            client_secret="wx_secret",
        )
        self.provider = WeChatOAuthProvider(self.config)

    def test_build_auth_url_uses_appid(self):
        url = self.provider.build_auth_url("state456")
        assert "appid=wx_appid" in url
        assert "#wechat_redirect" in url

    def test_token_params_uses_appid_secret(self):
        params = self.provider.get_token_params("code789")
        assert params["appid"] == "wx_appid"
        assert params["secret"] == "wx_secret"
        assert params["grant_type"] == "authorization_code"

    def test_normalize_user_info(self):
        raw = {"openid": "wx_openid", "nickname": "WeChatUser", "headimgurl": "http://head"}
        info = self.provider.normalize_user_info(raw)
        assert info.open_id == "wx_openid"
        assert info.nickname == "WeChatUser"
