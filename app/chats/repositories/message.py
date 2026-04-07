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

    async def get_messages_cursor(
        self,
        chat_id: int,
        limit: int = 30,
        before_id: int | None = None,
    ) -> list[Message]:
        stmt = select(Message).where(
            Message.chat_id == chat_id,
            Message.is_deleted.is_(False),
        ).options(selectinload(Message.reply_to))

        if before_id is not None:
            stmt = stmt.where(Message.id < before_id)

        stmt = stmt.order_by(Message.id.desc()).limit(limit + 1)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_messages_count(
        self,
        chat_id: int,
        after_message_id: int,
    ) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Message)
            .where(
                Message.chat_id == chat_id,
                Message.id > after_message_id,
                Message.is_deleted.is_(False),
            )
        )
        return result.scalar_one()

    async def create(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def soft_delete(self, message: Message) -> None:
        message.is_deleted = True
        await self.session.flush()

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
