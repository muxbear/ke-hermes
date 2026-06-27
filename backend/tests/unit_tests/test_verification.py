"""Tests for verification code sender strategy."""

from unittest.mock import AsyncMock, patch

import pytest
from core.verification import EmailCodeSender, SmsCodeSender


class TestSmsCodeSender:
    @pytest.mark.asyncio
    async def test_sends_code_and_returns_dev_response(self):
        """无 SMS_PROVIDER 时应返回 devCode。"""
        store = AsyncMock()
        # 第一次 get 返回 "rand" (captcha)，后续返回 None (daily count)
        store.get.side_effect = ["rand", None]

        sender = SmsCodeSender(store)
        with patch("core.verification.settings") as mock_settings:
            mock_settings.SMS_PROVIDER = ""
            mock_settings.SMS_DAILY_LIMIT = 10
            sender.daily_limit = 10
            result = await sender.send("13800138000", "ticket", "rand")

        assert "devCode" in result
        assert len(result["devCode"]) == 6
        assert result["devCode"].isdigit()

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_raises(self):
        """超过每日限制应抛出 429。"""
        from fastapi import HTTPException

        store = AsyncMock()
        store.get.return_value = "10"

        sender = SmsCodeSender(store)
        sender.daily_limit = 10

        with pytest.raises(HTTPException) as exc:
            await sender.send("13800138000")
        assert exc.value.status_code == 429


class TestEmailCodeSender:
    @pytest.mark.asyncio
    async def test_sends_code_and_returns_dev_response(self):
        """应返回 devCode。"""
        store = AsyncMock()
        store.get.return_value = None

        sender = EmailCodeSender(store)
        sender.daily_limit = 5
        result = await sender.send("test@example.com")

        assert "devCode" in result
        assert len(result["devCode"]) == 6
