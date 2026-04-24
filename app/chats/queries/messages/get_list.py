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
class GetAttachmentsQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: int
    limit: int = 30
    before_id: int | None = None
    include_read_details: bool = False


@dataclass(frozen=True)
class GetAttachmentsQueryHandler(BaseQueryHandler[GetAttachmentsQuery, MessageCursorPage]):
    chat_repository: ChatRepository
    message_repository: MessageRepository
    read_receipt_repository: ReadReceiptRepository
    attachment_repository: AttachmentRepository

    async def handle(self, query: GetAttachmentsQuery) -> MessageCursorPage:
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

        message_ids = [m.id for m in rows]
        attachments_map = await self.attachment_repository.get_by_message_ids(message_ids)

        read_cursors: dict[int, int] = {}
        if query.include_read_details:
            member_ids = await self.chat_repository.get_member_user_ids(query.chat_id)
            read_cursors = await self.read_receipt_repository.get_read_cursors(
                chat_id=query.chat_id,
                user_ids=member_ids,
            )

        items = []
        for m in rows:
            msg_dto = MessageDTO.model_validate(m.to_dict())
            msg_dto.attachments = [
                AttachmentDTO.model_validate(a.to_dict())
                for a in attachments_map.get(m.id, [])
            ]
            items.append(msg_dto)

        return MessageCursorPage(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
            read_cursors=read_cursors,
        )
