import logging
import time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.schemas import (
    AccountLoginRequest,
    AuthResponse,
    AuthTokens,
    EmailRegisterRequest,
    LoginFailInfo,
    PhoneLoginRequest,
    RefreshRequest,
    RegisterRequest,
    UserInfo,
)
from core.security import (
    create_token_pair,
    decode_token,
    decrypt_password,
    get_public_key as _get_public_key,
    hash_password,
    verify_password,
)
from core.cache import KeyValueCache
from db.models import LoginRecord, Account

logger = logging.getLogger(__name__)


async def get_public_key_svc() -> str:
    return _get_public_key()


async def _get_fail_info(account: str, store: KeyValueCache) -> LoginFailInfo:
    data = await store.get(f"login:fail:{account}")
    if not data:
        return LoginFailInfo(failCount=0, lockedUntil=None)
    try:
        count_str, until_str = data.split(":", 1)
        fail_count = int(count_str)
        locked_until = int(until_str) if until_str and until_str != "0" else None
        if locked_until and time.time() > locked_until:
            return LoginFailInfo(failCount=0, lockedUntil=None)
        return LoginFailInfo(failCount=fail_count, lockedUntil=locked_until)
    except (ValueError, IndexError):
        return LoginFailInfo(failCount=0, lockedUntil=None)


async def _check_locked(account: str, store: KeyValueCache):
    info = await _get_fail_info(account, store)
    if info.lockedUntil and time.time() < info.lockedUntil:
        remaining = int(info.lockedUntil - time.time())
        raise HTTPException(
            status_code=403,
            detail=f"Account locked. Try again in {remaining // 60 + 1} minutes.",
        )


async def _record_login(session: AsyncSession, account: str, success: bool, ip: str = ""):
    session.add(LoginRecord(account=account, success=success, ip=ip))


async def _incr_fail(account: str, store: KeyValueCache):
    from agent.config import settings

    count = await store.incr(f"login:fail:{account}")
    if count >= settings.LOGIN_MAX_FAILS:
        until = int(time.time()) + settings.LOGIN_LOCK_MINUTES * 60
        await store.set(f"login:fail:{account}", f"{count}:{until}", ttl=settings.LOGIN_LOCK_MINUTES * 60)
    else:
        await store.set(f"login:fail:{account}", f"{count}:0", ttl=settings.LOGIN_LOCK_MINUTES * 60 * 2)


async def _clear_fail(account: str, store: KeyValueCache):
    await store.delete(f"login:fail:{account}")


def _user_to_info(user: Account) -> UserInfo:
    return UserInfo(
        id=user.id,
        nickname=user.nickname or "",
        avatar=user.avatar or "",
        phone=user.phone or "",
        email=user.email or "",
        workspaceId=user.workspace_id or "default",
    )


def _to_auth_response(user: Account, token_pair) -> AuthResponse:
    return AuthResponse(
        tokens=AuthTokens(
            accessToken=token_pair.accessToken,
            refreshToken=token_pair.refreshToken,
            expiresIn=token_pair.expiresIn,
        ),
        user=_user_to_info(user),
    )


async def account_login(
    req: AccountLoginRequest,
    db: AsyncSession,
    store: KeyValueCache,
    ip: str = "",
) -> AuthResponse:
    await _check_locked(req.account, store)

    try:
        plain_password = decrypt_password(req.password)
    except HTTPException:
        await _incr_fail(req.account, store)
        raise

    result = await db.execute(
        select(Account).where(
            (Account.username == req.account) | (Account.phone == req.account) | (Account.email == req.account)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(plain_password, user.password_hash):
        await _record_login(db, req.account, False, ip)
        await _incr_fail(req.account, store)
        raise HTTPException(status_code=401, detail="Invalid account or password")

    await _record_login(db, req.account, True, ip)
    await _clear_fail(req.account, store)
    token_pair = create_token_pair(user.id)
    return _to_auth_response(user, token_pair)


async def phone_login(
    req: PhoneLoginRequest,
    db: AsyncSession,
    store: KeyValueCache,
) -> AuthResponse:
    code = await store.get(f"sms:{req.phone}")
    if not code or code != req.smsCode:
        raise HTTPException(status_code=400, detail="Invalid or expired SMS code")
    await store.delete(f"sms:{req.phone}")

    result = await db.execute(select(Account).where(Account.phone == req.phone))
    user = result.scalar_one_or_none()

    if not user:
        user = Account(phone=req.phone, nickname=f"Account{req.phone[-4:]}")
        db.add(user)
        await db.flush()
        await db.refresh(user)

    token_pair = create_token_pair(user.id)
    return _to_auth_response(user, token_pair)


async def register_phone(
    req: RegisterRequest,
    db: AsyncSession,
    store: KeyValueCache,
) -> AuthResponse:
    code = await store.get(f"sms:{req.phone}")
    if not code or code != req.smsCode:
        raise HTTPException(status_code=400, detail="Invalid or expired SMS code")
    await store.delete(f"sms:{req.phone}")

    existing = await db.execute(select(Account).where(Account.phone == req.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Phone already registered")

    try:
        plain_password = decrypt_password(req.password)
    except HTTPException:
        raise HTTPException(status_code=400, detail="Invalid password encryption")

    user = Account(
        phone=req.phone,
        nickname=req.nickname,
        password_hash=hash_password(plain_password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token_pair = create_token_pair(user.id)
    return _to_auth_response(user, token_pair)


async def register_email(
    req: EmailRegisterRequest,
    db: AsyncSession,
    store: KeyValueCache,
) -> AuthResponse:
    code = await store.get(f"email:{req.email}")
    if not code or code != req.emailCode:
        raise HTTPException(status_code=400, detail="Invalid or expired email code")
    await store.delete(f"email:{req.email}")

    existing = await db.execute(select(Account).where(Account.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        plain_password = decrypt_password(req.password)
    except HTTPException:
        raise HTTPException(status_code=400, detail="Invalid password encryption")

    user = Account(
        email=req.email,
        nickname=req.nickname,
        password_hash=hash_password(plain_password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token_pair = create_token_pair(user.id)
    return _to_auth_response(user, token_pair)


async def refresh_token_svc(
    req: RefreshRequest,
    db: AsyncSession,
) -> AuthResponse:
    payload = decode_token(req.refreshToken, expected_type="refresh")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(Account).where(Account.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Account not found")

    token_pair = create_token_pair(user.id)
    return _to_auth_response(user, token_pair)


async def get_fail_count_svc(account: str, store: KeyValueCache) -> LoginFailInfo:
    return await _get_fail_info(account, store)
