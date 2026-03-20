from dataclasses import dataclass

from app.chats.dtos.messages import MessageCursorPage, MessageDTO
from app.chats.repositories.messages import MessageRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True)
class GetMessagesQuery(BaseQuery):
    chat_id: int
    user_jwt: UserJWTData
    limit: int = 30
    before_id: int | None = None


@dataclass(frozen=True)
class GetMessagesQueryHandler(BaseQueryHandler[GetMessagesQuery, MessageCursorPage]):
    message_repository: MessageRepository

    async def handle(self, query: GetMessagesQuery) -> MessageCursorPage:
        rows = await self.message_repository.get_page(
            chat_id=query.chat_id,
            limit=query.limit,
            before_id=query.before_id,
        )

        has_more = len(rows) > query.limit
        items = rows[:query.limit]
        if items:
            await self.message_repository.mark_read(
                chat_id=query.chat_id,
                user_id=int(query.user_jwt.id),
                up_to_message_id=items[0].id,
            )

        return MessageCursorPage(
            items=[MessageDTO.model_validate(m.to_dict()) for m in items],
            next_cursor=items[-1].id if has_more and items else None,
            has_more=has_more,
        )
