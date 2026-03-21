from dataclasses import dataclass

from app.chats.dtos.messages import MessageCursorPage, MessageDTO
from app.chats.exceptions import NotChatMemberException
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True)
class GetMessagesQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: int
    limit: int = 30
    before_id: int | None = None


@dataclass(frozen=True)
class GetMessagesQueryHandler(BaseQueryHandler[GetMessagesQuery, MessageCursorPage]):
    chat_repository: ChatRepository
    message_repository: MessageRepository
    read_receipt_repository: ReadReceiptRepository

    async def handle(self, query: GetMessagesQuery) -> MessageCursorPage:
        user_id = int(query.user_jwt_data.id)

        member = await self.chat_repository.get_member(query.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=query.chat_id, user_id=user_id)

        limit = min(query.limit, 100)
        rows = await self.message_repository.get_messages_cursor(
            chat_id=query.chat_id,
            limit=limit,
            before_id=query.before_id,
        )

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = rows[-1].id if (has_more and rows) else None

        member_ids = await self.chat_repository.get_member_user_ids(query.chat_id)
        read_cursors = await self.read_receipt_repository.get_read_cursors(
            chat_id=query.chat_id,
            user_ids=member_ids,
        )

        items = [
            MessageDTO(
                id=m.id,
                chat_id=m.chat_id,
                author_id=m.author_id,
                type=m.type,
                content=m.content,
                reply_to_id=m.reply_to_id,
                media_url=m.media_url,
                is_deleted=m.is_deleted,
                is_edited=m.is_edited,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in rows
        ]

        return MessageCursorPage(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
            read_cursors=read_cursors,
        )