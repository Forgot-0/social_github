from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert

from app.chats.models.chat import Chat
from app.chats.models.chat_members import ChatMember
from app.chats.models.message import Message
from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter


@dataclass
class ChatRepository(IRepository[Chat], CacheRepository):
    _LIST_VERSION_KEY = "chat:list"

    async def create(self, chat: Chat) -> None:
        self.session.add(chat)

    async def get_user_chats(self, user_id: int) -> list[Chat]:
        result = await self.session.execute(
            select(Chat)
            .where(ChatMember.user_id == user_id)
            .order_by(Chat.last_activity_at.desc().nullslast())
        )
        return list(result.scalars().all())

    async def get_by_id(self, chat_id: int) -> Chat | None:
        result = await self.session.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        return result.scalar()

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
