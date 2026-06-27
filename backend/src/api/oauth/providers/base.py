"""OAuth 提供者抽象接口——策略模式 + 适配器模式。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OAuthConfig:
    """OAuth 提供者配置。"""
    auth_url: str
    token_url: str
    userinfo_url: str
    scope: str
    client_id: str
    client_secret: str


@dataclass
class OAuthUserInfo:
    """标准化用户信息——各平台适配器输出统一格式。"""
    open_id: str
    nickname: str
    avatar: str
    email: str


class OAuthProvider(ABC):
    """OAuth 提供者抽象接口。

    每个具体实现封装一个 OAuth 平台的差异：
    - 授权 URL 构建（参数名、额外片段）
    - Token 交换
    - 用户信息获取与标准化
    """

    name: str

    def __init__(self, config: OAuthConfig) -> None:
        self._config = config
        self._redirect_uri = "http://localhost:5173/oauth/callback"

    def build_auth_url(self, state: str) -> str:
        """构建授权 URL。子类可覆盖以处理平台差异（如微信的 #wechat_redirect）。"""
        return (
            f"{self._config.auth_url}?"
            f"client_id={self._config.client_id}&"
            f"redirect_uri={self._redirect_uri}&"
            f"scope={self._config.scope}&"
            f"state={state}&"
            f"response_type=code"
        )

    def get_token_params(self, code: str) -> dict:
        """构建 Token 交换请求参数。子类可覆盖以使用不同参数名。"""
        return {
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "code": code,
            "redirect_uri": self._redirect_uri,
        }

    @property
    def redirect_uri(self) -> str:
        return self._redirect_uri

    @property
    def token_url(self) -> str:
        return self._config.token_url

    @property
    def userinfo_url(self) -> str:
        return self._config.userinfo_url

    @abstractmethod
    def normalize_user_info(self, raw: dict) -> OAuthUserInfo:
        """将平台原始用户数据标准化为 OAuthUserInfo。"""
        ...
