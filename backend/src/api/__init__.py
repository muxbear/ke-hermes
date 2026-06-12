from fastapi import APIRouter

from api.agent import router as agent_router
from api.agents import router as agents_router
from api.auth import router as auth_router
from api.captcha import router as captcha_router
from api.conversation import router as conversation_router
from api.email import router as email_router
from api.knowledge_base import kb_router, doc_router, graph_router
from api.mcp import router as mcp_router
from api.oauth import router as oauth_router
from api.providers import router as providers_router
from api.skill import router as skill_router
from api.sms import router as sms_router
from api.tools import router as tools_router

router = APIRouter()
router.include_router(agent_router)
router.include_router(agents_router)
router.include_router(auth_router)
router.include_router(captcha_router)
router.include_router(email_router)
router.include_router(sms_router)
router.include_router(oauth_router)
router.include_router(conversation_router)
router.include_router(providers_router)
router.include_router(skill_router)
router.include_router(tools_router)
router.include_router(mcp_router)
router.include_router(kb_router)
router.include_router(doc_router)
router.include_router(graph_router)

__all__ = ["router"]
