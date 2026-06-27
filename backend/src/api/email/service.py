import logging

from pydantic import BaseModel, EmailStr

from core.store import KeyValueStore
from core.verification import EmailCodeSender

logger = logging.getLogger(__name__)


class SendEmailRequest(BaseModel):
    email: EmailStr
    captchaTicket: str = ""
    captchaRandstr: str = ""


async def send_email_code(req: SendEmailRequest, store: KeyValueStore) -> dict:
    """发送邮箱验证码——委托给 EmailCodeSender 策略。"""
    sender = EmailCodeSender(store)
    return await sender.send(req.email, req.captchaTicket, req.captchaRandstr)
