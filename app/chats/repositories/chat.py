from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.chats.models.chat import Chat
from app.chats.models.chat_members import ChatMember
from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter


@dataclass
class ChatRepository(IRepository[Chat], CacheRepository):
    _LIST_VERSION_KEY = "chats:list"

    async def get_by_id(
        self, chat_id: UUID, with_members: bool = False
    ) -> Chat | None:
        stmt = select(Chat).where(
            Chat.id == chat_id,
            Chat.deleted_at.is_(None),
        )

        if with_members:
            stmt = stmt.options(selectinload(Chat.members))

        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_memebr_chat(self, chat_id: UUID, member_id: int) -> ChatMember | None:
        stmt = select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == member_id,
        ).options(selectinload(ChatMember.role))

        result = await self.session.execute(stmt)
        return result.scalar()

    async def delete_member(self, member: ChatMember) -> None:
        await self.session.delete(member)

    async def create(self, chat: Chat) -> None:
        self.session.add(chat)

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
