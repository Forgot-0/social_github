from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.chats.models.chat import Chat
from app.chats.models.chat_members import ChatMember
from app.chats.models.read_receipts import ReadReceipt
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

    async def get_member_chat(self, chat_id: UUID, member_id: int, with_role=True) -> ChatMember | None:
        stmt = select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == member_id,
        )
        if with_role:
            stmt = stmt.options(selectinload(ChatMember.role))

        result = await self.session.execute(stmt)
        return result.scalar()

    async def delete_member(self, member: ChatMember) -> None:
        await self.session.delete(member)

    async def create(self, chat: Chat) -> None:
        self.session.add(chat)

    async def get_chats(
        self, user_id: int, limit: int,
        last_activity_at: datetime | None=None, chat_id: UUID | None=None
    ) -> list[tuple[Chat, ChatMember, ReadReceipt | None]]:
        stmt = select(Chat, ChatMember, ReadReceipt).where(
            ChatMember.user_id==user_id,
            ChatMember.is_banned.is_(False),
            Chat.deleted_at.is_(None),
        ).join(
            ChatMember, and_(ChatMember.chat_id == Chat.id, ChatMember.user_id==user_id)
        ).outerjoin(
            ReadReceipt,
            and_(
                ReadReceipt.chat_id == Chat.id,
                ReadReceipt.user_id == user_id,
            ),
        ).order_by(
            Chat.last_activity_at.desc().nullslast(), Chat.id.desc()
        ).limit(limit + 1)

        if last_activity_at is not None and chat_id is not None:
            stmt = stmt.where(
            or_(
                Chat.last_activity_at < last_activity_at,
                and_(
                    Chat.last_activity_at == last_activity_at,
                    Chat.id < chat_id,
                ),
            )
        )

        result = await self.session.execute(stmt)
        return list(*result.all())

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
