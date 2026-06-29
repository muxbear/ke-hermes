"""Department business logic layer."""

import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.departments.repository import DepartmentRepository
from api.departments.schemas import (
    DepartmentCreateRequest,
    DepartmentDeleteRequest,
    DepartmentTreeNode,
    DepartmentUpdateRequest,
    OrgNodeResponse,
)
from db.models.department import Department
from db.models.personnel import Personnel

logger = logging.getLogger(__name__)


class DepartmentService:
    """Orchestrates department business rules and cross-module integrity."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with a database session."""
        self.repo = DepartmentRepository(db)

    # ── Queries ─────────────────────────────────────────────────

    async def list_org_nodes(self) -> list[OrgNodeResponse]:
        """Return flat list of departments with computed employee_count and leader."""
        depts = await self.repo.get_all()
        if not depts:
            return []

        dept_ids = [d.id for d in depts]
        member_map = await self.repo.compute_member_counts(dept_ids)
        leader_map = await self._resolve_leader_names(depts)

        responses: list[OrgNodeResponse] = []
        for d in depts:
            responses.append(self._build_org_node(d, member_map, leader_map))
        return responses

    async def get_tree(self) -> list[DepartmentTreeNode]:
        """Build nested department tree for the user management sidebar."""
        depts = await self.repo.get_all()
        if not depts:
            return []

        dept_ids = [d.id for d in depts]
        member_map = await self.repo.compute_member_counts(dept_ids)

        # Build id -> node map
        node_map: dict[str, DepartmentTreeNode] = {}
        for d in depts:
            node_map[d.id] = DepartmentTreeNode(
                id=d.id,
                name=d.name,
                parent_id=d.parent_id,
                manager_id=d.manager_id,
                description=d.description or "",
                member_count=member_map.get(d.id, 0),
                children=[],
            )

        roots: list[DepartmentTreeNode] = []
        for d in depts:
            node = node_map[d.id]
            if d.parent_id and d.parent_id in node_map:
                node_map[d.parent_id].children.append(node)
            else:
                roots.append(node)

        return roots

    # ── Mutations ───────────────────────────────────────────────

    async def create(self, req: DepartmentCreateRequest) -> OrgNodeResponse:
        """Create a department with validation."""
        # Code uniqueness
        if await self.repo.get_by_code(req.code):
            raise HTTPException(status_code=409, detail=f"部门编码 '{req.code}' 已存在")

        # Parent must exist
        if req.parent_id:
            parent = await self.repo.get_by_id(req.parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail="父部门不存在")

        # Manager must be valid personnel
        if req.manager_id:
            if not await self._manager_exists(req.manager_id):
                raise HTTPException(status_code=404, detail="负责人不存在")

        dept = Department(
            name=req.name,
            code=req.code,
            parent_id=req.parent_id,
            type=req.type,
            level=req.level,
            manager_id=req.manager_id,
            description=req.description or None,
            address=req.address or None,
            phone=req.phone or None,
            email=req.email or None,
            sort=req.sort,
            status=req.status,
        )
        created = await self.repo.create(dept)

        # Resolve leader name
        leader_name = ""
        if created.manager_id:
            leader_map = await self.repo.batch_get_leader_names([created.manager_id])
            leader_name = leader_map.get(created.manager_id, "")

        return OrgNodeResponse(
            id=created.id,
            name=created.name,
            code=created.code,
            parent_id=created.parent_id,
            type=created.type,
            level=created.level,
            leader=leader_name,
            phone=created.phone or "",
            email=created.email or "",
            address=created.address or "",
            desc=created.description or "",
            employee_count=0,
            sort=created.sort,
            status=created.status,
            created_at=created.created_at,
        )

    async def update(self, dept_id: str, req: DepartmentUpdateRequest) -> OrgNodeResponse:
        """Update a department with validation."""
        dept = await self.repo.get_by_id(dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="部门不存在")

        updates: dict[str, object] = {}

        if req.name is not None:
            updates["name"] = req.name
        if req.code is not None:
            if await self.repo.get_by_code(req.code, exclude_id=dept_id):
                raise HTTPException(status_code=409, detail=f"部门编码 '{req.code}' 已存在")
            updates["code"] = req.code
        if req.parent_id is not None:
            if req.parent_id:
                if not await self.repo.get_by_id(req.parent_id):
                    raise HTTPException(status_code=404, detail="父部门不存在")
                if await self.repo.check_circular_parent(dept_id, req.parent_id):
                    raise HTTPException(status_code=400, detail="不能将部门移动到其子部门下")
            updates["parent_id"] = req.parent_id
        if req.manager_id is not None:
            if req.manager_id and not await self._manager_exists(req.manager_id):
                raise HTTPException(status_code=404, detail="负责人不存在")
            updates["manager_id"] = req.manager_id
        for field in ("type", "level", "description", "address", "phone", "email", "sort", "status"):
            val = getattr(req, field, None)
            if val is not None:
                updates[field] = val

        if not updates:
            raise HTTPException(status_code=400, detail="没有要更新的字段")

        updated = await self.repo.update(dept_id, updates)
        if not updated:
            raise HTTPException(status_code=500, detail="更新失败")

        return await self._to_org_node_response(updated)

    async def delete_batch(self, req: DepartmentDeleteRequest) -> dict[str, object]:
        """Batch delete departments with cascade."""
        ids_set = set(req.ids)

        # Collect all descendant IDs to delete
        descendant_ids = await self.repo.get_all_descendant_ids(ids_set)
        all_ids = ids_set | descendant_ids

        # Unbind personnel from the deleted departments
        await self.repo.unbind_personnel_from_departments(all_ids)

        # Delete all affected departments
        count = await self.repo.delete_batch(all_ids)

        return {"deleted": count, "ids": list(all_ids)}

    # ── Private helpers ─────────────────────────────────────────

    async def _manager_exists(self, manager_id: str) -> bool:
        """Check if a personnel record exists."""
        from sqlalchemy import select

        result = await self.repo.db.execute(
            select(Personnel.id).where(Personnel.id == manager_id)
        )
        return result.scalar_one_or_none() is not None

    async def _to_org_node_response(self, d: Department) -> OrgNodeResponse:
        """Convert Department ORM to OrgNodeResponse with computed fields."""
        member_map = await self.repo.compute_member_counts([d.id])
        leader_map = await self._resolve_leader_names([d])
        return self._build_org_node(d, member_map, leader_map)

    async def _resolve_leader_names(
        self, depts: list[Department]
    ) -> dict[str, str]:
        """Batch-resolve manager_id -> personnel.name."""
        manager_ids = [d.manager_id for d in depts if d.manager_id]
        return await self.repo.batch_get_leader_names(manager_ids)

    @staticmethod
    def _build_org_node(
        d: Department,
        member_map: dict[str, int],
        leader_map: dict[str, str],
    ) -> OrgNodeResponse:
        """Build OrgNodeResponse from Department + computed maps."""
        leader = ""
        if d.manager_id:
            leader = leader_map.get(d.manager_id, "")
        return OrgNodeResponse(
            id=d.id,
            name=d.name,
            code=d.code,
            parent_id=d.parent_id,
            type=d.type,
            level=d.level,
            leader=leader,
            phone=d.phone or "",
            email=d.email or "",
            address=d.address or "",
            desc=d.description or "",
            employee_count=member_map.get(d.id, 0),
            sort=d.sort,
            status=d.status,
            created_at=d.created_at,
        )
