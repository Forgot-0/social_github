from dataclasses import dataclass

from app.chats.dtos.messages import MemberReadCursorDTO, MessageReadDetailsPageDTO
from app.chats.exceptions import NotChatMemberException
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True)
class GetMessageReadDetailsQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: int
    limit: int = 50
    after_user_id: int | None = None


@dataclass(frozen=True)
class GetMessageReadDetailsQueryHandler(
    BaseQueryHandler[GetMessageReadDetailsQuery, MessageReadDetailsPageDTO]
):
    chat_repository: ChatRepository
    read_receipt_repository: ReadReceiptRepository

    async def handle(self, query: GetMessageReadDetailsQuery) -> MessageReadDetailsPageDTO:
        user_id = int(query.user_jwt_data.id)
        member = await self.chat_repository.get_member(query.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=query.chat_id, user_id=user_id)

        limit = min(query.limit, 200)
        rows = await self.read_receipt_repository.get_read_cursors_page(
            chat_id=query.chat_id,
            limit=limit,
            after_user_id=query.after_user_id,
        )
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [
            MemberReadCursorDTO(user_id=uid, last_read_message_id=cursor)
            for uid, cursor in rows
        ]
        next_cursor = rows[-1][0] if (has_more and rows) else None
        return MessageReadDetailsPageDTO(items=items, next_cursor=next_cursor, has_more=has_more)
