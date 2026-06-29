import logging
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.attachment.repository import (
    create_attachment,
    delete_attachment,
    get_attachment_by_id,
)
from api.attachment.schemas import AttachmentResponse
from api.deps import get_current_user_id
from core.decorators import handle_errors
from core.response import ok
from db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat-attachments"])

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".py", ".java", ".csv", ".md", ".json", ".xml",
    ".yaml", ".yml", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


def _get_upload_dir() -> Path:
    workspace = Path(__file__).resolve().parent.parent.parent.parent / "workspace"
    upload_dir = workspace / "chat_upload" / date.today().isoformat()
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@router.post("/upload")
@handle_errors
async def upload_attachment(
    file: UploadFile,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    ext = Path(file.filename or "unknown").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 100MB 限制")

    stored_name = f"{uuid.uuid4()}{ext}"
    upload_dir = _get_upload_dir()
    file_disk_path = upload_dir / stored_name
    file_disk_path.write_bytes(content)

    rel_path = str(
        Path("chat_upload") / date.today().isoformat() / stored_name
    )

    attachment = await create_attachment(
        db=db,
        filename=file.filename or "unknown",
        file_path=rel_path,
        file_size=len(content),
        file_type=file.content_type or "application/octet-stream",
        user_id=user_id,
    )

    return ok(AttachmentResponse.model_validate(attachment).model_dump())


@router.delete("/upload/{attachment_id}")
@handle_errors
async def delete_attachment_endpoint(
    attachment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    attachment = await get_attachment_by_id(db, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="附件不存在")
    if attachment.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权操作此附件")

    workspace = Path(__file__).resolve().parent.parent.parent.parent / "workspace"
    file_path = workspace / attachment.file_path
    if file_path.exists():
        file_path.unlink()

    await delete_attachment(db, attachment)
    return ok(None)
