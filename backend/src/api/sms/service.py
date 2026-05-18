import logging
import random
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel, Field

from agent.config import settings
from core.store import KeyValueStore

logger = logging.getLogger(__name__)


class SendSmsRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    captchaTicket: str
    captchaRandstr: str


async def send_sms(req: SendSmsRequest, store: KeyValueStore) -> dict:
    """Send SMS verification code. Returns dev code in response when no SMS provider configured."""
    randstr = await store.get(f"captcha:ticket:{req.captchaTicket}")
    if not randstr or randstr != req.captchaRandstr:
        raise HTTPException(status_code=400, detail="Invalid captcha ticket")

    today = datetime.now().strftime("%Y%m%d")
    daily_key = f"sms:daily:{req.phone}:{today}"
    count = await store.get(daily_key)
    daily_count = int(count) if count else 0
    if daily_count >= settings.SMS_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail="Daily SMS limit exceeded")

    code = "".join(str(random.randint(0, 9)) for _ in range(6))
    await store.set(f"sms:{req.phone}", code, ttl=300)
    await store.set(daily_key, str(daily_count + 1), ttl=86400)
    await store.delete(f"captcha:ticket:{req.captchaTicket}")

    logger.info("SMS code for %s: %s (dev mode — not sent)", req.phone, code)
    return {"devCode": code} if not settings.SMS_PROVIDER else {}
