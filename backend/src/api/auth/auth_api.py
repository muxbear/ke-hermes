from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.schemas import (
    AccountLoginRequest,
    AuthResponse,
    EmailRegisterRequest,
    LoginFailInfo,
    PhoneLoginRequest,
    RefreshRequest,
    RegisterRequest,
)
from api.auth.service import (
    account_login,
    get_fail_count_svc,
    get_public_key_svc,
    phone_login,
    refresh_token_svc,
    register_email,
    register_phone,
)
from api.deps import get_client_ip, get_db, get_store
from core.decorators import handle_errors
from core.response import ApiResponse, ok
from core.store import KeyValueStore

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/public-key")
async def public_key():
    pub = await get_public_key_svc()
    return ok({"publicKey": pub})


@router.post("/login/account", response_model=ApiResponse[AuthResponse])
@handle_errors
async def login_account(
    req: AccountLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    store: KeyValueStore = Depends(get_store),
):
    result = await account_login(req, db, store, ip=get_client_ip(request))
    return ok(result)


@router.post("/login/phone", response_model=ApiResponse[AuthResponse])
@handle_errors
async def login_phone(
    req: PhoneLoginRequest,
    db: AsyncSession = Depends(get_db),
    store: KeyValueStore = Depends(get_store),
):
    result = await phone_login(req, db, store)
    return ok(result)


@router.post("/register/phone", response_model=ApiResponse[AuthResponse])
@handle_errors
async def register_phone_route(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    store: KeyValueStore = Depends(get_store),
):
    result = await register_phone(req, db, store)
    return ok(result)


@router.post("/register/email", response_model=ApiResponse[AuthResponse])
@handle_errors
async def register_email_route(
    req: EmailRegisterRequest,
    db: AsyncSession = Depends(get_db),
    store: KeyValueStore = Depends(get_store),
):
    result = await register_email(req, db, store)
    return ok(result)


@router.post("/logout")
async def logout():
    return ok(None)


@router.post("/refresh", response_model=ApiResponse[AuthResponse])
@handle_errors
async def refresh(
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await refresh_token_svc(req, db)
    return ok(result)


@router.get("/fail-count")
async def fail_count(
    account: str,
    store: KeyValueStore = Depends(get_store),
):
    info = await get_fail_count_svc(account, store)
    return ok(info.model_dump())
