from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.chats.models.chat_members import ChatMember
from app.core.db.repository import CacheRepository, IRepository


@dataclass
class ChatMembersRepository(IRepository[ChatMember], CacheRepository):
    _LIST_VERSION_KEY = "chat_members:list"


    async def get_memebers_by_chat(self, chat_id: int, with_role: bool=False) -> ChatMember | None:
        stmt = select(ChatMember).where(ChatMember.chat_id == chat_id)
        if with_role:
            stmt = stmt.options(selectinload(ChatMember.role))
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_memeber_by_chat(self, chat_id: int, user_id: int, with_role: bool=False) -> ChatMember | None:
        stmt = select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id==user_id)
        if with_role:
            stmt = stmt.options(selectinload(ChatMember.role))
        result = await self.session.execute(stmt)
        return result.scalar()
