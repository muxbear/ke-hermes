"""Request and response schemas for skill upload."""
from datetime import datetime

from pydantic import BaseModel


class SkillValidationError(BaseModel):
    """A single validation error for a skill."""

    field: str
    message: str


class SkillResult(BaseModel):
    """Validation result for one extracted skill directory."""

    name: str
    valid: bool
    errors: list[SkillValidationError] = []


class SkillsUploadResponse(BaseModel):
    """Overall response from the upload_skills endpoint."""

    skills_dir: str
    total: int
    valid_count: int
    invalid_count: int
    skipped_count: int
    results: list[SkillResult]
    skipped: list[str] = []


class SkillInfo(BaseModel):
    """Single skill record for list/search responses."""

    id: str
    name: str
    valid: bool
    source: str
    description: str
    license: str
    icon: str = ""
    category: str = "custom"
    prompt: str = ""
    enabled: bool = True
    is_builtin: bool = False
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM model compatibility."""
        from_attributes = True


class SkillListResponse(BaseModel):
    """Paginated list of skills."""

    items: list[SkillInfo]
    total: int
    page: int
    page_size: int


class SkillUpdateRequest(BaseModel):
    """Request body for updating a skill's metadata."""

    name: str | None = None
    description: str | None = None
    icon: str | None = None
    category: str | None = None
    prompt: str | None = None
    enabled: bool | None = None


class SkillCreateRequest(BaseModel):
    """Request body for manually creating a single skill."""

    name: str
    description: str = ""
    icon: str = "Zap"
    category: str = "custom"
    prompt: str = ""


class SkillToggleRequest(BaseModel):
    """Request body for toggling skill enabled state."""

    enabled: bool


class SkillBatchDeleteRequest(BaseModel):
    """Request body for batch-deleting skills by ID."""

    ids: list[str]


class SkillDeleteResult(BaseModel):
    """Result detail for a single skill deletion."""

    id: str
    name: str
    deleted: bool
    reason: str = ""


class SkillDeleteResponse(BaseModel):
    """Response for single or batch skill deletion."""

    deleted_count: int
    failed_count: int
    results: list[SkillDeleteResult]
