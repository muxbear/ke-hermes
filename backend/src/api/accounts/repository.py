"""Account data access layer."""

import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import Account

logger = logging.getLogger(__name__)


class AccountRepository:
    """Encapsulates all Account database queries."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with a database session."""
        self.db = db

    async def list_paginated(
        self, search: str = "", page: int = 1, page_size: int = 20
    ) -> tuple[list[Account], int]:
        """Return paginated account list with optional search."""
        stmt = select(Account)
        count_stmt = select(func.count(Account.id))

        if search:
            q = f"%{search}%"
            filter_expr = (
                Account.username.ilike(q)
                | Account.nickname.ilike(q)
                | Account.email.ilike(q)
                | Account.phone.ilike(q)
            )
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        # Total count
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Paginated items
        offset = (page - 1) * page_size
        result = await self.db.execute(
            stmt.order_by(Account.created_at.desc()).offset(offset).limit(page_size)
        )
        items = list(result.scalars().all())

        return items, total

    async def get_by_id(self, account_id: str) -> Account | None:
        """Get a single account by ID."""
        result = await self.db.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str, exclude_id: str | None = None) -> Account | None:
        """Check username uniqueness."""
        stmt = select(Account).where(Account.username == username)
        if exclude_id:
            stmt = stmt.where(Account.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, account: Account) -> Account:
        """Insert a new account."""
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def update(self, account_id: str, values: dict) -> Account | None:
        """Partially update an account."""
        values["updated_at"] = func.now()
        await self.db.execute(
            update(Account).where(Account.id == account_id).values(**values)
        )
        await self.db.flush()
        return await self.get_by_id(account_id)

    async def delete(self, account_id: str) -> bool:
        """Delete an account."""
        result = await self.db.execute(
            delete(Account).where(Account.id == account_id)
        )
        return result.rowcount > 0  # type: ignore[no-any-return]

    async def unbind_personnel(self, account_id: str) -> None:
        """Set personnel.account_id = NULL for the deleted account."""
        from db.models.personnel import Personnel

        await self.db.execute(
            update(Personnel)
            .where(Personnel.account_id == account_id)
            .values(account_id=None)
        )
