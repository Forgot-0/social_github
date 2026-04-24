from dataclasses import dataclass

from app.chats.dtos.attachments import AttachmentDTO
from app.chats.dtos.messages import MessageCursorPage, MessageDTO
from app.chats.exceptions import NotChatMemberException
from app.chats.repositories.attachment import AttachmentRepository
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
    include_read_details: bool = False


@dataclass(frozen=True)
class GetMessagesQueryHandler(BaseQueryHandler[GetMessagesQuery, MessageCursorPage]):
    chat_repository: ChatRepository
    message_repository: MessageRepository
    read_receipt_repository: ReadReceiptRepository
    attachment_repository: AttachmentRepository

    async def handle(self, query: GetMessagesQuery) -> MessageCursorPage:
        user_id = int(query.user_jwt_data.id)

        member = await self.chat_repository.get_member(query.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=query.chat_id, user_id=user_id)

        limit = min(query.limit, 100)
        messages = await self.message_repository.get_messages_cursor(
            chat_id=query.chat_id,
            limit=limit,
            before_id=query.before_id,
        )

        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        next_cursor = messages[-1].id if (has_more and messages) else None

        read_cursors: dict[int, int] = {}
        if query.include_read_details:
            member_ids = await self.chat_repository.get_member_user_ids(query.chat_id)
            read_cursors = await self.read_receipt_repository.get_read_cursors(
                chat_id=query.chat_id,
                user_ids=member_ids,
            )

        return MessageCursorPage(
            items=[MessageDTO.model_validate(m.to_dict()) for m in messages],
            next_cursor=next_cursor,
            has_more=has_more,
            read_cursors=read_cursors,
        )
