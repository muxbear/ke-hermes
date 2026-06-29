"""Account business logic layer."""

import logging
import secrets
import string

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.accounts.repository import AccountRepository
from api.accounts.schemas import (
    AccountCreateRequest,
    AccountListResponse,
    AccountPasswordChangeRequest,
    AccountResetPasswordResponse,
    AccountResponse,
    AccountUpdateRequest,
)
from core.cache import KeyValueCache
from core.security import hash_password, verify_password
from db.models.user import Account

logger = logging.getLogger(__name__)


class AccountService:
    """Orchestrates account business rules."""

    def __init__(self, db: AsyncSession, cache: KeyValueCache | None = None) -> None:
        """Initialize with a database session and optional cache."""
        self.repo = AccountRepository(db)
        self.cache = cache

    # ── Queries ─────────────────────────────────────────────────

    async def list_accounts(
        self, search: str = "", page: int = 1, page_size: int = 20
    ) -> AccountListResponse:
        """List accounts with pagination and search."""
        items, total = await self.repo.list_paginated(search, page, page_size)
        return AccountListResponse(
            items=[self._to_response(a) for a in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_account(self, account_id: str) -> AccountResponse:
        """Get single account detail."""
        account = await self.repo.get_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="账号不存在")
        return self._to_response(account)

    # ── Mutations ───────────────────────────────────────────────

    async def create(self, req: AccountCreateRequest) -> AccountResponse:
        """Create a new account with validation."""
        if await self.repo.get_by_username(req.username):
            raise HTTPException(status_code=409, detail=f"用户名 '{req.username}' 已存在")

        account = Account(
            username=req.username,
            nickname=req.nickname,
            password_hash=hash_password(req.password),
            email=req.email or None,
            phone=req.phone or None,
            is_active=req.is_active,
        )
        created = await self.repo.create(account)
        return self._to_response(created)

    async def update(self, account_id: str, req: AccountUpdateRequest) -> AccountResponse:
        """Partially update an account."""
        existing = await self.repo.get_by_id(account_id)
        if not existing:
            raise HTTPException(status_code=404, detail="账号不存在")

        updates: dict[str, object] = {}
        if req.username is not None:
            if await self.repo.get_by_username(req.username, exclude_id=account_id):
                raise HTTPException(status_code=409, detail=f"用户名 '{req.username}' 已存在")
            updates["username"] = req.username
        for field in ("nickname", "email", "phone", "is_active"):
            val = getattr(req, field, None)
            if val is not None:
                updates[field] = val or None

        if not updates:
            raise HTTPException(status_code=400, detail="没有要更新的字段")

        updated = await self.repo.update(account_id, updates)
        if not updated:
            raise HTTPException(status_code=500, detail="更新失败")
        return self._to_response(updated)

    async def delete(self, account_id: str) -> dict[str, object]:
        """Delete an account. Unbinds personnel before deletion."""
        existing = await self.repo.get_by_id(account_id)
        if not existing:
            raise HTTPException(status_code=404, detail="账号不存在")

        await self.repo.unbind_personnel(account_id)
        deleted = await self.repo.delete(account_id)
        return {"deleted": deleted, "id": account_id}

    async def toggle_status(self, account_id: str) -> AccountResponse:
        """Toggle account active/inactive."""
        existing = await self.repo.get_by_id(account_id)
        if not existing:
            raise HTTPException(status_code=404, detail="账号不存在")

        updated = await self.repo.update(account_id, {"is_active": not existing.is_active})
        if not updated:
            raise HTTPException(status_code=500, detail="操作失败")
        return self._to_response(updated)

    async def unlock(self, account_id: str) -> dict[str, object]:
        """Unlock an account by clearing login fail cache entries."""
        existing = await self.repo.get_by_id(account_id)
        if not existing:
            raise HTTPException(status_code=404, detail="账号不存在")

        # Clear cache entries for all possible login identifiers
        if self.cache:
            for identifier in filter(None, [existing.username, existing.phone, existing.email]):
                await self.cache.delete(f"login:fail:{identifier}")

        return {"unlocked": True, "id": account_id}

    async def reset_password(self, account_id: str) -> AccountResetPasswordResponse:
        """Admin force-reset password. Returns temporary password."""
        existing = await self.repo.get_by_id(account_id)
        if not existing:
            raise HTTPException(status_code=404, detail="账号不存在")

        temp_password = self._generate_password()
        await self.repo.update(
            account_id, {"password_hash": hash_password(temp_password)}
        )
        return AccountResetPasswordResponse(
            id=account_id, temp_password=temp_password
        )

    async def change_password(
        self, account_id: str, req: AccountPasswordChangeRequest
    ) -> dict[str, object]:
        """Change password with old password verification."""
        existing = await self.repo.get_by_id(account_id)
        if not existing:
            raise HTTPException(status_code=404, detail="账号不存在")

        if not existing.password_hash:
            raise HTTPException(status_code=400, detail="该账号未设置密码")

        if not verify_password(req.old_password, existing.password_hash):
            raise HTTPException(status_code=400, detail="旧密码不正确")

        await self.repo.update(
            account_id, {"password_hash": hash_password(req.new_password)}
        )
        return {"success": True}

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _to_response(a: Account) -> AccountResponse:
        """Convert ORM object to response DTO."""
        return AccountResponse(
            id=a.id,
            username=a.username or "",
            nickname=a.nickname or "",
            email=a.email or "",
            phone=a.phone or "",
            avatar=a.avatar or "",
            is_active=a.is_active,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )

    @staticmethod
    def _generate_password(length: int = 16) -> str:
        """Generate a random password."""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
