"""Request and response schemas for provider and model management."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ---- 模型参数 ----

class ModelParamSchema(BaseModel):
    """单个模型默认参数。"""

    key: str
    label: str
    value: float | str
    min: float | None = None
    max: float | None = None
    step: float | None = None
    type: str  # number | text | select
    options: list[str] | None = None


# ---- 模型请求 ----

class ModelCreateRequest(BaseModel):
    """创建模型的请求体。"""

    name: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=16)
    status: str = "active"
    context_window: int | None = None
    description: str = ""
    release_date: str | None = None
    params: list[ModelParamSchema] = []


class ModelUpdateRequest(BaseModel):
    """更新模型的请求体。"""

    name: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=16)
    status: str = "active"
    context_window: int | None = None
    call_count: int = 0
    description: str = ""
    release_date: str | None = None
    params: list[ModelParamSchema] = []
    used_by_agents: list[str] = []


# ---- 模型响应 ----

class ModelResponse(BaseModel):
    """模型响应体（与前端 AIModel 接口对齐）。"""

    id: str
    name: str
    display_name: str
    type: str
    status: str
    context_window: int | None = None
    call_count: int = 0
    description: str
    release_date: str | None = None
    params: list[ModelParamSchema] = []
    used_by_agents: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- 提供商请求 ----

class ProviderCreateRequest(BaseModel):
    """创建提供商的请求体。"""

    name: str = Field(min_length=1, max_length=128)
    logo: str = "🤖"
    api_base: str = Field(min_length=1, max_length=512)
    api_key: str = ""
    description: str = ""
    website: str = ""


class ProviderUpdateRequest(BaseModel):
    """更新提供商的请求体。"""

    name: str = Field(min_length=1, max_length=128)
    logo: str = "🤖"
    api_base: str = Field(min_length=1, max_length=512)
    api_key: str = ""
    status: str = "unconfigured"
    description: str = ""
    website: str = ""


# ---- 提供商响应 ----

class ProviderResponse(BaseModel):
    """提供商响应体（含嵌套模型列表，与前端 Provider 接口对齐）。"""

    id: str
    name: str
    logo: str
    status: str
    api_base: str
    api_key: str
    description: str
    website: str
    models: list[ModelResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
