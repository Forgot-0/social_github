from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.chats.models.message import Message
from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter


@dataclass
class MessageRepository(IRepository[Message]):

    async def get_by_id(self, message_id: int) -> Message | None:
        result = await self.session.execute(
            select(Message).where(
                Message.id == message_id,
                Message.is_deleted.is_(False),
            )
        )
        return result.scalar()

    async def create(self, message: Message) -> None:
        self.session.add(message)

    async def soft_delete(self, message: Message) -> None:
        message.is_deleted = True

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
