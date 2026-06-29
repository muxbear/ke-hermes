from datetime import datetime

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    file_size: int
    file_type: str
    user_id: str
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
