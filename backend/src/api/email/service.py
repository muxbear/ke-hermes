import logging
import random
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr

from agent.config import settings
from core.store import KeyValueStore

logger = logging.getLogger(__name__)


class SendEmailRequest(BaseModel):
    email: EmailStr
    captchaTicket: str = ""
    captchaRandstr: str = ""


async def send_email_code(req: SendEmailRequest, store: KeyValueStore) -> dict:
    """Send email verification code. Returns dev code when no email provider configured."""
    if req.captchaTicket:
        randstr = await store.get(f"captcha:ticket:{req.captchaTicket}")
        if not randstr or randstr != req.captchaRandstr:
            raise HTTPException(status_code=400, detail="Invalid captcha ticket")
        await store.delete(f"captcha:ticket:{req.captchaTicket}")

    today = datetime.now().strftime("%Y%m%d")
    daily_key = f"email:daily:{req.email}:{today}"
    count = await store.get(daily_key)
    daily_count = int(count) if count else 0
    if daily_count >= getattr(settings, "EMAIL_DAILY_LIMIT", 5):
        raise HTTPException(status_code=429, detail="Daily email code limit exceeded")

    code = "".join(str(random.randint(0, 9)) for _ in range(6))
    await store.set(f"email:{req.email}", code, ttl=300)
    await store.set(daily_key, str(daily_count + 1), ttl=86400)

    logger.info("Email code for %s: %s (dev mode — not sent)", req.email, code)
    return {"devCode": code}
