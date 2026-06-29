"""Personnel data access layer."""

import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.department import Department
from db.models.personnel import Personnel
from db.models.user import User

logger = logging.getLogger(__name__)


class PersonnelRepository:
    """Encapsulates all Personnel database queries."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with a database session."""
        self.db = db

    async def get_all(self, dept_id: str | None = None) -> list[Personnel]:
        """List personnel, optionally filtered by dept_id."""
        stmt = select(Personnel).order_by(Personnel.sort, Personnel.name)
        if dept_id:
            stmt = stmt.where(Personnel.dept_id == dept_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, personnel_id: str) -> Personnel | None:
        """Get a single personnel record by ID."""
        result = await self.db.execute(
            select(Personnel).where(Personnel.id == personnel_id)
        )
        return result.scalar_one_or_none()

    async def get_by_employee_id(
        self, employee_id: str, exclude_id: str | None = None
    ) -> Personnel | None:
        """Check employee_id uniqueness."""
        stmt = select(Personnel).where(Personnel.employee_id == employee_id)
        if exclude_id:
            stmt = stmt.where(Personnel.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> Personnel | None:
        """Check if a user is already linked to a personnel record."""
        result = await self.db.execute(
            select(Personnel).where(Personnel.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, personnel: Personnel) -> Personnel:
        """Insert a new personnel record."""
        self.db.add(personnel)
        await self.db.flush()
        await self.db.refresh(personnel)
        return personnel

    async def update(self, personnel_id: str, values: dict) -> Personnel | None:
        """Update a personnel record by ID and return the updated object."""
        values["updated_at"] = func.now()
        await self.db.execute(
            update(Personnel).where(Personnel.id == personnel_id).values(**values)
        )
        await self.db.flush()
        return await self.get_by_id(personnel_id)

    async def delete(self, personnel_id: str) -> bool:
        """Delete a personnel record."""
        result = await self.db.execute(
            delete(Personnel).where(Personnel.id == personnel_id)
        )
        return result.rowcount > 0  # type: ignore[no-any-return]

    async def clear_manager_for_personnel(self, personnel_id: str) -> None:
        """Set departments.manager_id = NULL where the deleted person was manager."""
        await self.db.execute(
            update(Department)
            .where(Department.manager_id == personnel_id)
            .values(manager_id=None)
        )

    # ── User / Account helpers ──────────────────────────────────

    async def get_user_by_email(self, email: str) -> User | None:
        """Find a user by email (for account linking)."""
        if not email:
            return None
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_phone(self, phone: str) -> User | None:
        """Find a user by phone (for account linking)."""
        if not phone:
            return None
        result = await self.db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """Check if a username is already taken."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        """Create a new auth user."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
