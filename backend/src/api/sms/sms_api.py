from fastapi import APIRouter, Depends, Request

from api.deps import get_store
from api.sms.service import SendSmsRequest, send_sms
from core.decorators import handle_errors, rate_limit
from core.response import ok
from core.store import KeyValueStore

router = APIRouter(prefix="/api/sms", tags=["sms"])


@router.post("/send")
@rate_limit(max_calls=10, period_seconds=60, key_prefix="sms")
@handle_errors
async def send(
    req: SendSmsRequest,
    request: Request,
    store: KeyValueStore = Depends(get_store),
):
    result = await send_sms(req, store)
    return ok(result)
