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

    async def get_by_message_id(self, message_id: int) -> list[MessageAttachment]:
        result = await self.session.execute(
            select(MessageAttachment)
            .where(MessageAttachment.message_id == message_id)
            .order_by(MessageAttachment.created_at)
        )
        return list(result.scalars().all())

    async def get_by_message_ids(self, message_ids: list[int]) -> dict[int, list[MessageAttachment]]:
        if not message_ids:
            return {}

        result = await self.session.execute(
            select(MessageAttachment)
            .where(MessageAttachment.message_id.in_(message_ids))
            .order_by(MessageAttachment.message_id, MessageAttachment.created_at)
        )
        rows = result.scalars().all()

        grouped: dict[int, list[MessageAttachment]] = {}
        for att in rows:
            grouped.setdefault(att.message_id, []).append(att)
        return grouped

    async def create_bulk(self, attachments: list[MessageAttachment]) -> list[MessageAttachment]:
        for attachment in attachments:
            self.session.add(attachment)
        await self.session.flush()
        return attachments

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
