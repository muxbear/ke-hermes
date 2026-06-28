import uuid

from fastapi import APIRouter, Depends, Request, Response

from api.captcha.schemas import (
    ImageCaptchaData,
    ImageVerifyRequest,
    SlidePuzzleData,
    SlideVerifyRequest,
    SlideVerifyResponse,
)
from api.captcha.service import (
    generate_image_captcha,
    generate_slide_puzzle,
    verify_image,
    verify_slide,
)
from api.deps import get_cache
from core.decorators import handle_errors
from core.response import ApiResponse, error, ok
from core.cache import KeyValueCache

router = APIRouter(prefix="/api/captcha", tags=["captcha"])

CAPTCHA_SESSION_COOKIE = "captcha_session"


def _get_session_id(request: Request, response: Response) -> str:
    sid = request.cookies.get(CAPTCHA_SESSION_COOKIE)
    if not sid:
        sid = str(uuid.uuid4())
        response.set_cookie(
            CAPTCHA_SESSION_COOKIE,
            sid,
            max_age=600,
            path="/api/captcha",
            httponly=True,
            samesite="lax",
        )
    return sid


@router.get("/slide", response_model=ApiResponse[SlidePuzzleData])
@handle_errors
async def get_slide(
    request: Request,
    response: Response,
    cache: KeyValueCache = Depends(get_cache),
):
    sid = _get_session_id(request, response)
    data = await generate_slide_puzzle(sid, cache)
    return ok(data)


@router.post("/slide/verify", response_model=ApiResponse[SlideVerifyResponse])
@handle_errors
async def verify_slide_route(
    req: SlideVerifyRequest,
    request: Request,
    cache: KeyValueCache = Depends(get_cache),
):
    # Prefer sessionId from request body; fall back to cookie
    sid = req.sessionId or request.cookies.get(CAPTCHA_SESSION_COOKIE)
    if not sid:
        return error(400, "Captcha session not found, please refresh")
    result = await verify_slide(req, sid, cache)
    return ok(result)


@router.get("/image", response_model=ApiResponse[ImageCaptchaData])
@handle_errors
async def get_image(cache: KeyValueCache = Depends(get_cache)):
    data = await generate_image_captcha(cache)
    return ok(data)


@router.post("/image/verify")
@handle_errors
async def verify_image_route(
    req: ImageVerifyRequest,
    cache: KeyValueCache = Depends(get_cache),
):
    success = await verify_image(req.key, req.code, cache)
    return ok({"success": success})
