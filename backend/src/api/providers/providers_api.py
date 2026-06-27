"""Provider and model management API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id, get_db
from api.providers.schemas import (
    ModelCreateRequest,
    ModelResponse,
    ModelUpdateRequest,
    ProviderCreateRequest,
    ProviderResponse,
    ProviderUpdateRequest,
)
from api.providers.service import (
    clone_model,
    create_model,
    create_provider,
    delete_model,
    delete_provider,
    list_providers,
    toggle_model_status,
    update_model,
    update_provider,
)
from core.decorators import handle_errors
from core.response import ApiResponse, ok

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("", response_model=ApiResponse[list[ProviderResponse]])
@handle_errors
async def provider_list(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有模型提供商（含嵌套模型列表）。"""
    result = await list_providers(db, user_id)
    return ok(result)


@router.post("", response_model=ApiResponse[ProviderResponse])
@handle_errors
async def provider_create(
    req: ProviderCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新的模型提供商。"""
    result = await create_provider(db, req, user_id)
    return ok(result)


@router.put("/{provider_id}", response_model=ApiResponse[ProviderResponse])
@handle_errors
async def provider_update(
    provider_id: str,
    req: ProviderUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新模型提供商信息。"""
    result = await update_provider(db, provider_id, req, user_id)
    return ok(result)


@router.delete("/{provider_id}", response_model=ApiResponse[None])
@handle_errors
async def provider_delete(
    provider_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除模型提供商（级联删除其下所有模型）。"""
    await delete_provider(db, provider_id, user_id)
    return ok(None, "Provider deleted successfully")


@router.post("/{provider_id}/models", response_model=ApiResponse[ModelResponse])
@handle_errors
async def model_create(
    provider_id: str,
    req: ModelCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """在指定提供商下创建新模型。"""
    result = await create_model(db, provider_id, req, user_id)
    return ok(result)


@router.put("/{provider_id}/models/{model_id}", response_model=ApiResponse[ModelResponse])
@handle_errors
async def model_update(
    provider_id: str,
    model_id: str,
    req: ModelUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新指定模型的信息。"""
    result = await update_model(db, provider_id, model_id, req, user_id)
    return ok(result)


@router.delete("/{provider_id}/models/{model_id}", response_model=ApiResponse[None])
@handle_errors
async def model_delete(
    provider_id: str,
    model_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除指定模型。"""
    await delete_model(db, provider_id, model_id, user_id)
    return ok(None, "Model deleted successfully")


@router.post("/{provider_id}/models/{model_id}/clone", response_model=ApiResponse[ModelResponse])
@handle_errors
async def model_clone(
    provider_id: str,
    model_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """克隆指定模型，复制所有配置并使用新的 ID。"""
    result = await clone_model(db, provider_id, model_id, user_id)
    return ok(result)


@router.patch("/{provider_id}/models/{model_id}/status", response_model=ApiResponse[ModelResponse])
@handle_errors
async def model_toggle_status(
    provider_id: str,
    model_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """切换模型的启用/禁用状态。"""
    result = await toggle_model_status(db, provider_id, model_id, user_id)
    return ok(result)
