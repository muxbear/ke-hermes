"""Department data access layer."""

import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.department import Department
from db.models.personnel import Personnel

logger = logging.getLogger(__name__)


class DepartmentRepository:
    """Encapsulates all Department database queries."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with a database session."""
        self.db = db

    async def get_all(self) -> list[Department]:
        """Return all departments ordered by level then sort."""
        result = await self.db.execute(
            select(Department).order_by(Department.level, Department.sort)
        )
        return list(result.scalars().all())

    async def get_by_id(self, dept_id: str) -> Department | None:
        """Get a single department by ID."""
        result = await self.db.execute(
            select(Department).where(Department.id == dept_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str, exclude_id: str | None = None) -> Department | None:
        """Check code uniqueness. Pass exclude_id to ignore self on update."""
        stmt = select(Department).where(Department.code == code)
        if exclude_id:
            stmt = stmt.where(Department.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_descendant_ids(self, parent_ids: set[str]) -> set[str]:
        """Collect all descendant IDs for the given parent IDs."""
        descendant_ids: set[str] = set()
        current_level = parent_ids
        while current_level:
            result = await self.db.execute(
                select(Department.id).where(Department.parent_id.in_(current_level))
            )
            children = set(result.scalars().all())
            descendant_ids.update(children)
            current_level = children
        return descendant_ids

    async def check_circular_parent(self, dept_id: str, new_parent_id: str) -> bool:
        """Return True if setting new_parent_id would create a cycle."""
        if dept_id == new_parent_id:
            return True
        current = new_parent_id
        visited: set[str] = set()
        while current:
            if current in visited:
                return True
            if current == dept_id:
                return True
            visited.add(current)
            result = await self.db.execute(
                select(Department.parent_id).where(Department.id == current)
            )
            row = result.scalar_one_or_none()
            current = row if row else None
        return False

    async def create(self, dept: Department) -> Department:
        """Insert a new department."""
        self.db.add(dept)
        await self.db.flush()
        await self.db.refresh(dept)
        return dept

    async def update(self, dept_id: str, values: dict) -> Department | None:
        """Update a department by ID and return the updated object."""
        values["updated_at"] = func.now()
        await self.db.execute(
            update(Department).where(Department.id == dept_id).values(**values)
        )
        await self.db.flush()
        return await self.get_by_id(dept_id)

    async def delete_batch(self, ids: set[str]) -> int:
        """Delete departments by ID set. Returns count deleted."""
        result = await self.db.execute(
            delete(Department).where(Department.id.in_(ids))
        )
        return result.rowcount  # type: ignore[no-any-return]

    async def unbind_personnel_from_departments(self, dept_ids: set[str]) -> None:
        """Set personnel.dept_id = NULL for all personnel in given departments."""
        await self.db.execute(
            update(Personnel)
            .where(Personnel.dept_id.in_(dept_ids))
            .values(dept_id=None)
        )

    async def compute_member_counts(self, dept_ids: list[str]) -> dict[str, int]:
        """Return {dept_id: count} for given department IDs via GROUP BY."""
        result = await self.db.execute(
            select(Personnel.dept_id, func.count(Personnel.id))
            .where(Personnel.dept_id.in_(dept_ids))
            .group_by(Personnel.dept_id)
        )
        return {row[0]: row[1] for row in result.all()}

    async def batch_get_leader_names(self, manager_ids: list[str]) -> dict[str, str]:
        """Return {manager_id: name} for given personnel IDs."""
        if not manager_ids:
            return {}
        result = await self.db.execute(
            select(Personnel.id, Personnel.name).where(
                Personnel.id.in_(manager_ids)
            )
        )
        return {row[0]: row[1] for row in result.all()}
