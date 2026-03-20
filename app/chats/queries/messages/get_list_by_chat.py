from dataclasses import dataclass

from app.chats.dtos.messages import MessageCursorPage, MessageDTO
from app.chats.exceptions import NotFoundChatException
from app.chats.repositories.chats import ChatRepository
from app.chats.repositories.messages import MessageRepository
from app.chats.repositories.read_receipts import ReadReceiptRepository
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
    chat_repository: ChatRepository
    message_repository: MessageRepository
    read_receipt_repository: ReadReceiptRepository

    async def handle(self, query: GetMessagesQuery) -> MessageCursorPage:
        chat = await self.chat_repository.get_by_id(query.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=query.chat_id)

        rows = await self.message_repository.get_page(
            chat_id=query.chat_id,
            limit=query.limit,
            before_id=query.before_id,
        )

        has_more = len(rows) > query.limit
        items = rows[:query.limit]

        read_cursors = await self.read_receipt_repository.get_cursors_for_chat(
            chat_id=query.chat_id,
            user_ids=[chat.user_id_1, chat.user_id_2],
        )

        return MessageCursorPage(
            items=[MessageDTO.model_validate(m.to_dict()) for m in items],
            next_cursor=items[-1].id if has_more and items else None,
            has_more=has_more,
            read_cursors=read_cursors,
        )