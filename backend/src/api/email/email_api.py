from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_store
from api.email.service import SendEmailRequest, send_email_code
from core.response import error, ok
from core.store import KeyValueStore

router = APIRouter(prefix="/api/email", tags=["email"])


@router.post("/send")
async def send(
    req: SendEmailRequest,
    store: KeyValueStore = Depends(get_store),
):
    try:
        result = await send_email_code(req, store)
        return ok(result)
    except HTTPException as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
    except Exception as e:
        raise
