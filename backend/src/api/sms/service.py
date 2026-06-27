import logging

from pydantic import BaseModel, Field

from core.store import KeyValueStore
from core.verification import SmsCodeSender

logger = logging.getLogger(__name__)


class SendSmsRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    captchaTicket: str
    captchaRandstr: str


async def send_sms(req: SendSmsRequest, store: KeyValueStore) -> dict:
    """发送短信验证码——委托给 SmsCodeSender 策略。"""
    sender = SmsCodeSender(store)
    return await sender.send(req.phone, req.captchaTicket, req.captchaRandstr)
