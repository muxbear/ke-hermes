"""验证码发送策略——模板方法 + 策略模式。

提取 SMS 和 Email 验证码服务的公共逻辑，消除重复代码。
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime

from fastapi import HTTPException

from agent.config import settings
from core.cache import KeyValueCache

logger = logging.getLogger(__name__)


class VerificationCodeSender(ABC):
    """验证码发送器抽象基类——模板方法模式。

    子类只需实现 key_prefix / daily_limit，即可获得完整的验证码发送流程。
    """

    key_prefix: str
    daily_limit: int

    def __init__(self, store: KeyValueCache) -> None:
        self._store = store

    async def send(self, identifier: str, captcha_ticket: str = "",
                   captcha_randstr: str = "") -> dict:
        """模板方法——发送验证码的完整流程。

        1. 校验验证码票据（可选）
        2. 检查每日频率限制
        3. 生成 6 位验证码
        4. 存储验证码（TTL 300s）
        5. 递增每日计数器（TTL 86400s）
        """
        # 图片验证码校验
        if captcha_ticket:
            randstr = await self._store.get(f"captcha:ticket:{captcha_ticket}")
            if not randstr or randstr != captcha_randstr:
                raise HTTPException(status_code=400, detail="Invalid captcha ticket")
            await self._store.delete(f"captcha:ticket:{captcha_ticket}")

        # 每日频率限制
        today = datetime.now().strftime("%Y%m%d")
        daily_key = f"{self.key_prefix}:daily:{identifier}:{today}"
        count = await self._store.get(daily_key)
        daily_count = int(count) if count else 0
        if daily_count >= self.daily_limit:
            raise HTTPException(status_code=429, detail="Daily limit exceeded")

        # 生成并存储验证码
        code = "".join(str(random.randint(0, 9)) for _ in range(6))
        await self._store.set(f"{self.key_prefix}:{identifier}", code, ttl=300)
        await self._store.set(daily_key, str(daily_count + 1), ttl=86400)

        # 开发模式——返回验证码，生产模式——发送后不返回
        await self._do_send(identifier, code)
        logger.info("%s code for %s: %s (dev mode)", self.key_prefix, identifier, code)
        return self._build_response(code)

    @abstractmethod
    async def _do_send(self, identifier: str, code: str) -> None:
        """实际发送逻辑（子类实现）。"""
        ...

    @abstractmethod
    def _build_response(self, code: str) -> dict:
        """构建响应数据（子类实现）。"""
        ...


class SmsCodeSender(VerificationCodeSender):
    """短信验证码发送器。"""

    key_prefix = "sms"
    daily_limit = settings.SMS_DAILY_LIMIT

    async def _do_send(self, identifier: str, code: str) -> None:
        """TODO: 集成短信服务商 API。"""

    def _build_response(self, code: str) -> dict:
        if not settings.SMS_PROVIDER:
            return {"devCode": code}
        return {}


class EmailCodeSender(VerificationCodeSender):
    """邮箱验证码发送器。"""

    key_prefix = "email"
    daily_limit = getattr(settings, "EMAIL_DAILY_LIMIT", 5)

    async def _do_send(self, identifier: str, code: str) -> None:
        """TODO: 集成邮箱服务商 API。"""

    def _build_response(self, code: str) -> dict:
        return {"devCode": code}
