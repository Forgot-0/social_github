from dataclasses import dataclass
from uuid import UUID

from app.chats.dtos.messages import MessageDTO, MessagesDTO
from app.chats.exceptions import NotChatMemberException
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True, kw_only=True)
class GetMessageContextQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: UUID
    target_seq: int
    limit: int = 40


@dataclass(frozen=True)
class GetMessageContextQueryHandler(BaseQueryHandler[GetMessageContextQuery, MessagesDTO]):
    chat_repository: ChatRepository
    message_repository: MessageRepository

    async def handle(self, query: GetMessageContextQuery) -> MessagesDTO:
        user_id = int(query.user_jwt_data.id)

        member = await self.chat_repository.get_member_chat(query.chat_id, user_id, with_role=False)
        if not member or member.is_banned:
            raise NotChatMemberException(chat_id=str(query.chat_id), user_id=user_id)

        limit = min(max(query.limit, 1), 100)
        messages = await self.message_repository.get_message_context(
            chat_id=query.chat_id,
            target_seq=query.target_seq,
            limit=limit,
        )
        messages = sorted(messages, key=lambda msg: msg.seq)
        return MessagesDTO(
            messages=[MessageDTO.model_validate(msg.to_dict()) for msg in messages],
            has_next=False,
            next_cursor=None,
        )
