from fastapi import APIRouter

from api.agent import router as agent_router
from api.auth import router as auth_router
from api.captcha import router as captcha_router
from api.email import router as email_router
from api.oauth import router as oauth_router
from api.sms import router as sms_router
from api.conversation import router as conversation_router

router = APIRouter()
router.include_router(agent_router)
router.include_router(auth_router)
router.include_router(captcha_router)
router.include_router(email_router)
router.include_router(sms_router)
router.include_router(oauth_router)
router.include_router(conversation_router)

__all__ = ["router"]
