from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat_attachment import ChatAttachment


async def create_attachment(
    db: AsyncSession,
    filename: str,
    file_path: str,
    file_size: int,
    file_type: str,
    user_id: str,
) -> ChatAttachment:
    attachment = ChatAttachment(
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        user_id=user_id,
        status="success",
    )
    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)
    return attachment


async def get_attachment_by_id(
    db: AsyncSession, attachment_id: str
) -> ChatAttachment | None:
    result = await db.execute(
        select(ChatAttachment).where(ChatAttachment.id == attachment_id)
    )
    return result.scalar_one_or_none()


async def get_attachments_by_ids(
    db: AsyncSession, attachment_ids: list[str]
) -> list[ChatAttachment]:
    result = await db.execute(
        select(ChatAttachment).where(ChatAttachment.id.in_(attachment_ids))
    )
    return list(result.scalars().all())


async def delete_attachment(db: AsyncSession, attachment: ChatAttachment) -> None:
    await db.delete(attachment)
    await db.flush()
