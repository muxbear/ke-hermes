from fastapi import APIRouter, Depends, Request

from api.deps import get_cache
from api.email.service import SendEmailRequest, send_email_code
from core.decorators import handle_errors, rate_limit
from core.response import ok
from core.cache import KeyValueCache

router = APIRouter(prefix="/api/email", tags=["email"])


@router.post("/send")
@rate_limit(max_calls=5, period_seconds=60, key_prefix="email")
@handle_errors
async def send(
    req: SendEmailRequest,
    request: Request,
    cache: KeyValueCache = Depends(get_cache),
):
    result = await send_email_code(req, cache)
    return ok(result)
