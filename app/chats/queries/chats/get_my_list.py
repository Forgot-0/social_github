from dataclasses import dataclass

from app.chats.dtos.chats import ChatListItemDTO
from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.core.db.repository import PageResult
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True)
class GetChatsQuery(BaseQuery):
    user_jwt_data: UserJWTData
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class GetChatsQueryHandler(BaseQueryHandler[GetChatsQuery, PageResult[ChatListItemDTO]]):
    chat_repository: ChatRepository
    read_receipt_repository: ReadReceiptRepository

    async def handle(self, query: GetChatsQuery) -> PageResult[ChatListItemDTO]:
        user_id = int(query.user_jwt_data.id)

        page = await self.chat_repository.get_user_chats(
            user_id=user_id,
            page=query.page,
            page_size=query.page_size,
        )

        if not page.items:
            return PageResult(items=[], total=page.total, page=page.page, page_size=page.page_size)

        chat_ids = [c.id for c in page.items]
        keys = [ChatKeys.unread_count(user_id, cid) for cid in chat_ids]
        raw_counts = await self.chat_repository.redis.mget(*keys)
        unread_map = {
            cid: (int(v) if v is not None else 0)
            for cid, v in zip(chat_ids, raw_counts)
        }

        items = [
            ChatListItemDTO(
                id=chat.id,
                type=chat.type,
                name=chat.name,
                description=chat.description,
                avatar_url=chat.avatar_url,
                is_public=chat.is_public,
                created_by=chat.created_by,
                last_activity_at=chat.last_activity_at,
                unread_count=unread_map.get(chat.id, 0),
                member_count=len(chat.members),
            )
            for chat in page.items
        ]

        return PageResult(
            items=items,
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )
