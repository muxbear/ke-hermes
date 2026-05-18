from fastapi import APIRouter, Depends

from api.deps import get_store
from api.sms.service import SendSmsRequest, send_sms
from core.response import ApiResponse, error, ok
from core.store import KeyValueStore

router = APIRouter(prefix="/api/sms", tags=["sms"])


@router.post("/send")
async def send(
    req: SendSmsRequest,
    store: KeyValueStore = Depends(get_store),
):
    try:
        result = await send_sms(req, store)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise
