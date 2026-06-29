"""Department / org node management API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.departments.schemas import (
    DepartmentCreateRequest,
    DepartmentDeleteRequest,
    DepartmentTreeNode,
    DepartmentUpdateRequest,
    OrgNodeResponse,
)
from api.departments.service import DepartmentService
from api.deps import get_db
from core.decorators import handle_errors
from core.response import ApiResponse, ok

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("", response_model=ApiResponse[list[OrgNodeResponse]])
@handle_errors
async def department_list(db: AsyncSession = Depends(get_db)):
    """Return flat list of all departments for the org management page."""
    svc = DepartmentService(db)
    data = await svc.list_org_nodes()
    return ok(data)


@router.get("/tree", response_model=ApiResponse[list[DepartmentTreeNode]])
@handle_errors
async def department_tree(db: AsyncSession = Depends(get_db)):
    """Return nested department tree for the user management sidebar."""
    svc = DepartmentService(db)
    data = await svc.get_tree()
    return ok(data)


@router.post("", response_model=ApiResponse[OrgNodeResponse])
@handle_errors
async def department_create(
    req: DepartmentCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new department (org node)."""
    svc = DepartmentService(db)
    data = await svc.create(req)
    return ok(data, message="部门创建成功")


@router.put("/{dept_id}", response_model=ApiResponse[OrgNodeResponse])
@handle_errors
async def department_update(
    dept_id: str,
    req: DepartmentUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a department."""
    svc = DepartmentService(db)
    data = await svc.update(dept_id, req)
    return ok(data, message="部门更新成功")


@router.delete("", response_model=ApiResponse[dict])
@handle_errors
async def department_delete(
    req: DepartmentDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Batch delete departments with cascade."""
    svc = DepartmentService(db)
    data = await svc.delete_batch(req)
    return ok(data, message=f"已删除 {data['deleted']} 个部门")
