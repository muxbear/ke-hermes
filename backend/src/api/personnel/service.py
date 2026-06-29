"""Personnel business logic layer with AccountFactory."""

import logging
import secrets
import string

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.personnel.repository import PersonnelRepository
from api.personnel.schemas import (
    PersonnelCreateRequest,
    PersonnelResponse,
    PersonnelUpdateRequest,
)
from core.security import hash_password
from db.models.personnel import Personnel
from db.models.user import Account

logger = logging.getLogger(__name__)


class AccountFactory:
    """Creates or links a Account account when creating personnel."""

    def __init__(self, repo: PersonnelRepository) -> None:
        """Initialize with a personnel repository."""
        self.repo = repo

    async def ensure_account(
        self, email: str, phone: str, employee_id: str, account_id: str | None
    ) -> tuple[Account | None, str]:
        """Create or link a user account. Returns (user, temp_password)."""
        # If account_id is explicitly provided, use it directly
        if account_id:
            existing_personnel = await self.repo.get_by_account_id(account_id)
            if existing_personnel:
                raise HTTPException(status_code=409, detail="该认证用户已关联到其他人员")
            return None, ""  # caller creates personnel with this account_id

        # Check for existing user by email or phone
        user_by_email = await self.repo.get_user_by_email(email) if email else None
        user_by_phone = await self.repo.get_user_by_phone(phone) if phone else None

        if user_by_email and user_by_phone and user_by_email.id != user_by_phone.id:
            raise HTTPException(
                status_code=409,
                detail="邮箱和手机号分别匹配到不同账号，请手动指定 account_id",
            )

        existing_user = user_by_email or user_by_phone
        if existing_user:
            existing_personnel = await self.repo.get_by_account_id(existing_user.id)
            if existing_personnel:
                raise HTTPException(status_code=409, detail="该认证用户已关联到其他人员")
            return existing_user, ""

        # Create new user account
        temp_password = self._generate_password()
        username = await self._generate_username(employee_id)

        user = Account(
            username=username,
            nickname="",
            password_hash=hash_password(temp_password),
            email=email or None,
            phone=phone or None,
            is_active=True,
        )
        created_user = await self.repo.create_user(user)
        return created_user, temp_password

    def _generate_password(self, length: int = 16) -> str:
        """Generate a cryptographically random password."""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def _generate_username(self, employee_id: str) -> str:
        """Generate a unique username from employee_id, appending a suffix if taken."""
        base = employee_id.lower()
        username = base
        suffix = 1
        while await self.repo.get_user_by_username(username):
            username = f"{base}{suffix}"
            suffix += 1
        return username


class PersonnelService:
    """Orchestrates personnel business rules and cross-module integrity."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with a database session and account factory."""
        self.repo = PersonnelRepository(db)
        self.account_factory = AccountFactory(self.repo)

    # ── Queries ─────────────────────────────────────────────────

    async def list_personnel(self, dept_id: str | None = None) -> list[PersonnelResponse]:
        """List personnel, optionally filtered by department."""
        items = await self.repo.get_all(dept_id=dept_id if dept_id else None)
        return [self._to_response(p) for p in items]

    # ── Mutations ───────────────────────────────────────────────

    async def create(self, req: PersonnelCreateRequest) -> PersonnelResponse:
        """Create personnel, optionally creating a linked user account."""
        # Employee ID uniqueness
        if await self.repo.get_by_employee_id(req.employee_id):
            raise HTTPException(status_code=409, detail=f"工号 '{req.employee_id}' 已存在")

        # Department must exist if specified
        if req.dept_id:
            if not await self._dept_exists(req.dept_id):
                raise HTTPException(status_code=404, detail="所属部门不存在")

        # Validate explicit account_id
        if req.account_id:
            existing_personnel = await self.repo.get_by_account_id(req.account_id)
            if existing_personnel:
                raise HTTPException(status_code=409, detail="该认证用户已关联到其他人员")

        join_date = None
        if req.join_date:
            from datetime import date

            join_date = date.fromisoformat(req.join_date)

        # Handle account creation via AccountFactory
        account_id = req.account_id
        temp_password = ""
        account_created = False

        if req.create_account and not req.account_id:
            linked_user, temp_password = await self.account_factory.ensure_account(
                email=req.email,
                phone=req.phone,
                employee_id=req.employee_id,
                account_id=None,
            )
            if linked_user:
                account_id = linked_user.id
                account_created = temp_password != ""

        personnel = Personnel(
            account_id=account_id or None,
            dept_id=req.dept_id or None,
            name=req.name,
            employee_id=req.employee_id,
            position=req.position,
            email=req.email,
            phone=req.phone,
            status=req.status,
            join_date=join_date,
            avatar=req.avatar,
            sort=0,
        )
        created = await self.repo.create(personnel)

        response = self._to_response(created)
        response.account_created = account_created
        if account_created:
            # Get the created user's username
            user_record = await self.repo.get_user_by_username(req.employee_id.lower())
            response.username = user_record.username if user_record else req.employee_id.lower()
            response.temp_password = temp_password
        return response

    async def update(
        self, personnel_id: str, req: PersonnelUpdateRequest
    ) -> PersonnelResponse:
        """Update a personnel record with validation."""
        existing = await self.repo.get_by_id(personnel_id)
        if not existing:
            raise HTTPException(status_code=404, detail="人员不存在")

        updates: dict[str, object] = {}

        if req.name is not None:
            updates["name"] = req.name
        if req.employee_id is not None:
            if await self.repo.get_by_employee_id(
                req.employee_id, exclude_id=personnel_id
            ):
                raise HTTPException(status_code=409, detail=f"工号 '{req.employee_id}' 已存在")
            updates["employee_id"] = req.employee_id
        if req.dept_id is not None:
            if req.dept_id and not await self._dept_exists(req.dept_id):
                raise HTTPException(status_code=404, detail="所属部门不存在")
            updates["dept_id"] = req.dept_id or None
        for field in ("position", "email", "phone", "status", "avatar"):
            val = getattr(req, field, None)
            if val is not None:
                updates[field] = val or None
        if req.join_date is not None:
            from datetime import date

            updates["join_date"] = (
                date.fromisoformat(req.join_date) if req.join_date else None
            )
        if req.account_id is not None:
            if req.account_id:
                existing_personnel = await self.repo.get_by_account_id(req.account_id)
                if existing_personnel and existing_personnel.id != personnel_id:
                    raise HTTPException(status_code=409, detail="该认证用户已关联到其他人员")
                updates["account_id"] = req.account_id
            else:
                updates["account_id"] = None

        if not updates:
            raise HTTPException(status_code=400, detail="没有要更新的字段")

        updated = await self.repo.update(personnel_id, updates)
        if not updated:
            raise HTTPException(status_code=500, detail="更新失败")

        return self._to_response(updated)

    async def delete(self, personnel_id: str) -> dict[str, object]:
        """Delete a personnel record, clearing department manager references."""
        existing = await self.repo.get_by_id(personnel_id)
        if not existing:
            raise HTTPException(status_code=404, detail="人员不存在")

        # Clear manager references before deleting
        await self.repo.clear_manager_for_personnel(personnel_id)

        deleted = await self.repo.delete(personnel_id)
        return {"deleted": deleted, "id": personnel_id}

    # ── Private helpers ─────────────────────────────────────────

    async def _dept_exists(self, dept_id: str) -> bool:
        """Check if a department exists."""
        from sqlalchemy import select

        from db.models.department import Department

        result = await self.repo.db.execute(
            select(Department.id).where(Department.id == dept_id)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _to_response(p: Personnel) -> PersonnelResponse:
        """Convert Personnel ORM object to response DTO."""
        return PersonnelResponse(
            id=p.id,
            name=p.name,
            employee_id=p.employee_id,
            dept_id=p.dept_id or "",
            position=p.position or "",
            email=p.email or "",
            phone=p.phone or "",
            status=p.status,
            join_date=p.join_date.isoformat() if p.join_date else "",
            avatar=p.avatar or "",
            account_id=p.account_id,
            account_created=False,
            username="",
            temp_password="",
        )
