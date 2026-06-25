"""Agent management API endpoints."""
from api.agents.agents_api import router as agents_router
from api.agents.policies_api import router as policies_router

router = agents_router
router.include_router(policies_router)

__all__ = ["router"]
