from fastapi import APIRouter, Depends, Request

from api.deps import get_cache
from api.sms.service import SendSmsRequest, send_sms
from core.decorators import handle_errors, rate_limit
from core.response import ok
from core.cache import KeyValueCache

router = APIRouter(prefix="/api/sms", tags=["sms"])


@router.post("/send")
@rate_limit(max_calls=10, period_seconds=60, key_prefix="sms")
@handle_errors
async def send(
    req: SendSmsRequest,
    request: Request,
    cache: KeyValueCache = Depends(get_cache),
):
    result = await send_sms(req, cache)
    return ok(result)
