from fastapi import APIRouter, Depends, HTTPException

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
    except HTTPException as e:
        # 类型检查器知道这里的 e 是 HTTPException，拥有 status_code 和 detail
        return error(e.status_code, e.detail)
    except Exception as e:
        # 处理其他未知异常
        raise
