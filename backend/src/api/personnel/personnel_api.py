"""Personnel management API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.personnel.schemas import (
    PersonnelCreateRequest,
    PersonnelResponse,
    PersonnelUpdateRequest,
)
from api.personnel.service import PersonnelService
from core.decorators import handle_errors
from core.response import ApiResponse, ok

router = APIRouter(prefix="/api/personnel", tags=["personnel"])


@router.get("", response_model=ApiResponse[list[PersonnelResponse]])
@handle_errors
async def personnel_list(
    dept_id: str | None = Query(None, description="Filter by department ID"),
    db: AsyncSession = Depends(get_db),
):
    """List personnel, optionally filtered by department."""
    svc = PersonnelService(db)
    data = await svc.list_personnel(dept_id=dept_id)
    return ok(data)


@router.post("", response_model=ApiResponse[PersonnelResponse])
@handle_errors
async def personnel_create(
    req: PersonnelCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a personnel record, optionally creating a linked user account."""
    svc = PersonnelService(db)
    data = await svc.create(req)
    return ok(data, message="人员创建成功")


@router.put("/{personnel_id}", response_model=ApiResponse[PersonnelResponse])
@handle_errors
async def personnel_update(
    personnel_id: str,
    req: PersonnelUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a personnel record."""
    svc = PersonnelService(db)
    data = await svc.update(personnel_id, req)
    return ok(data, message="人员更新成功")


@router.delete("/{personnel_id}", response_model=ApiResponse[dict])
@handle_errors
async def personnel_delete(
    personnel_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a personnel record."""
    svc = PersonnelService(db)
    data = await svc.delete(personnel_id)
    return ok(data, message="人员已删除")
