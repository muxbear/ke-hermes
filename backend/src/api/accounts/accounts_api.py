"""Account management API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.accounts.schemas import (
    AccountCreateRequest,
    AccountListResponse,
    AccountPasswordChangeRequest,
    AccountResetPasswordResponse,
    AccountResponse,
    AccountUpdateRequest,
)
from api.accounts.service import AccountService
from api.deps import get_cache, get_db
from core.cache import KeyValueCache
from core.decorators import handle_errors
from core.response import ApiResponse, ok

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=ApiResponse[AccountListResponse])
@handle_errors
async def account_list(
    search: str = Query(default="", description="Search username/nickname/email/phone"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
):
    """List accounts with pagination and optional search."""
    svc = AccountService(db)
    data = await svc.list_accounts(search=search, page=page, page_size=page_size)
    return ok(data)


@router.get("/{account_id}", response_model=ApiResponse[AccountResponse])
@handle_errors
async def account_detail(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get account detail."""
    svc = AccountService(db)
    data = await svc.get_account(account_id)
    return ok(data)


@router.post("", response_model=ApiResponse[AccountResponse])
@handle_errors
async def account_create(
    req: AccountCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new account."""
    svc = AccountService(db)
    data = await svc.create(req)
    return ok(data, message="账号创建成功")


@router.put("/{account_id}", response_model=ApiResponse[AccountResponse])
@handle_errors
async def account_update(
    account_id: str,
    req: AccountUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update an account."""
    svc = AccountService(db)
    data = await svc.update(account_id, req)
    return ok(data, message="账号更新成功")


@router.delete("/{account_id}", response_model=ApiResponse[dict])
@handle_errors
async def account_delete(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an account."""
    svc = AccountService(db)
    data = await svc.delete(account_id)
    return ok(data, message="账号已删除")


@router.post("/{account_id}/toggle-status", response_model=ApiResponse[AccountResponse])
@handle_errors
async def account_toggle_status(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Toggle account active/inactive."""
    svc = AccountService(db)
    data = await svc.toggle_status(account_id)
    msg = "账号已启用" if data.is_active else "账号已禁用"
    return ok(data, message=msg)


@router.post("/{account_id}/unlock", response_model=ApiResponse[dict])
@handle_errors
async def account_unlock(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    cache: KeyValueCache = Depends(get_cache),
):
    """Unlock an account by clearing login fail cache."""
    svc = AccountService(db, cache)
    data = await svc.unlock(account_id)
    return ok(data, message="账号已解锁")


@router.post(
    "/{account_id}/reset-password",
    response_model=ApiResponse[AccountResetPasswordResponse],
)
@handle_errors
async def account_reset_password(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Admin force-reset account password."""
    svc = AccountService(db)
    data = await svc.reset_password(account_id)
    return ok(data, message="密码已重置")


@router.put("/{account_id}/password", response_model=ApiResponse[dict])
@handle_errors
async def account_change_password(
    account_id: str,
    req: AccountPasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Change account password (requires old password)."""
    svc = AccountService(db)
    data = await svc.change_password(account_id, req)
    return ok(data, message="密码已修改")
