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

    # async def get_or_create(self, user_id_1: int, user_id_2: int) -> Chat:
    #     uid1, uid2 = Chat.canonical_pair(user_id_1, user_id_2)

    #     result = await self.session.execute(
    #         select(Chat).where(Chat.user_id_1 == uid1, Chat.user_id_2 == uid2)
    #     )
    #     chat = result.scalar()
    #     if chat:
    #         return chat

    #     stmt = (
    #         insert(Chat)
    #         .values(user_id_1=uid1, user_id_2=uid2)
    #         .on_conflict_do_nothing(constraint="uq_chat_users")
    #         .returning(Chat)
    #     )
    #     result = await self.session.execute(stmt)
    #     chat = result.scalar()
    #     if chat:
    #         return chat

    #     result = await self.session.execute(
    #         select(Chat).where(Chat.user_id_1 == uid1, Chat.user_id_2 == uid2)
    #     )
    #     return result.scalar_one()

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
