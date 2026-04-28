from dataclasses import dataclass
from uuid import UUID

from app.chats.dtos.messages import MessageDTO, MessagesDTO
from app.chats.exceptions import NotChatMemberException
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True)
class GetMessagesQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: UUID
    limit: int = 30
    last_id: int | None = None


@dataclass(frozen=True)
class GetMessagesQueryHandler(BaseQueryHandler[GetMessagesQuery, MessagesDTO]):
    chat_repository: ChatRepository
    message_repository: MessageRepository

    async def handle(self, query: GetMessagesQuery) -> MessagesDTO:
        user_id = int(query.user_jwt_data.id)

        member = await self.chat_repository.get_member_chat(query.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=str(query.chat_id), user_id=user_id)

        limit = min(query.limit, 100)
        messages = await self.message_repository.get_messages(
            chat_id=query.chat_id,
            last_message_seq=query.last_id,
            limit=limit,
        )
        return MessagesDTO(
            messages=[MessageDTO.model_validate(msg.to_dict()) for msg in messages[:-1]],
            has_next=len(messages) > query.limit,
            next_cursor=messages[-1].seq
        )
