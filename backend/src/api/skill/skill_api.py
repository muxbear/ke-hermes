"""Skill upload API endpoints."""
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id, get_db
from api.skill.schemas import (
    SkillBatchDeleteRequest,
    SkillCreateRequest,
    SkillDeleteResponse,
    SkillInfo,
    SkillListResponse,
    SkillsUploadResponse,
    SkillToggleRequest,
    SkillUpdateRequest,
)
from api.skill.service import (
    create_skill,
    delete_skill,
    delete_skills_batch,
    get_skill,
    list_skills,
    process_skills_upload,
    search_skills,
    toggle_skill_enabled,
    update_skill,
)
from core.response import ApiResponse, error, ok

router = APIRouter(prefix="/api/skill", tags=["skill"])


@router.post("/upload_skills", response_model=ApiResponse[SkillsUploadResponse])
async def upload_skills(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """上传 skills 的压缩包（zip, tar.gz, tar.bz2, tar.xz），校验并安装到 workspace/skills/。

    解压后每个子目录视为一个 skill 包，按 Agent Skills 规范校验 SKILL.md。
    校验失败的 skill 仍会复制到目标目录，在响应中标记 valid=false。
    每个成功安装的 skill 入库到 skills 表。
    """  # noqa: D415
    try:
        result = await process_skills_upload(file, db, user_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.get("/list", response_model=ApiResponse[SkillListResponse])
async def skill_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    category: str | None = Query(None, description="分类筛选"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """分页列出所有已入库的技能，按上传时间倒序排列。"""  # noqa: D415
    try:
        result = await list_skills(db, page, page_size, category)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.get("/search", response_model=ApiResponse[SkillListResponse])
async def skill_search(
    name: str = Query(..., min_length=1, description="技能名称关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """按技能名称模糊搜索已入库的技能，支持分页。"""  # noqa: D415
    try:
        result = await search_skills(db, name, page, page_size)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.post("", response_model=ApiResponse[SkillInfo])
async def skill_create(
    req: SkillCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """手动创建单个技能，写入 SKILL.md 并入库。"""  # noqa: D415
    try:
        result = await create_skill(db, req, user_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.get("/{skill_id}", response_model=ApiResponse[SkillInfo])
async def skill_get(
    skill_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取单个技能详情。"""  # noqa: D415
    try:
        result = await get_skill(db, skill_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.put("/{skill_id}", response_model=ApiResponse[SkillInfo])
async def skill_update(
    skill_id: str,
    req: SkillUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新技能元数据，只更新传入的非空字段。"""  # noqa: D415
    try:
        result = await update_skill(db, skill_id, req)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.patch("/{skill_id}/toggle", response_model=ApiResponse[SkillInfo])
async def skill_toggle(
    skill_id: str,
    req: SkillToggleRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """切换技能的启用/禁用状态。"""  # noqa: D415
    try:
        result = await toggle_skill_enabled(db, skill_id, req.enabled)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.delete("/batch", response_model=ApiResponse[SkillDeleteResponse])
async def skill_batch_delete(
    req: SkillBatchDeleteRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """批量删除技能，同时删除数据库记录和 workspace 目录。"""  # noqa: D415
    try:
        result = await delete_skills_batch(db, req.ids)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise


@router.delete("/{skill_id}", response_model=ApiResponse[SkillDeleteResponse])
async def skill_delete(
    skill_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除单个技能，同时删除数据库记录和 workspace 目录。"""  # noqa: D415
    try:
        result = await delete_skill(db, skill_id)
        return ok(result)
    except Exception as e:
        if hasattr(e, "status_code"):
            return error(e.status_code, e.detail)
        raise
