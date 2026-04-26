from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, select

from app.chats.models.attachment import MessageAttachment
from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter


@dataclass
class AttachmentRepository(IRepository[MessageAttachment]):

    async def get_by_id(self, attachment_id: UUID) -> MessageAttachment | None:
        result = await self.session.execute(
            select(MessageAttachment).where(MessageAttachment.id == attachment_id)
        )
        return result.scalar()

    async def create(self, attachment: MessageAttachment) -> None:
        self.session.add(attachment)

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
