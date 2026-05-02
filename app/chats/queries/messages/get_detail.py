from dataclasses import dataclass
from uuid import UUID

from app.chats.dtos.messages import MessageDTO
from app.chats.exceptions import NotChatMemberException, NotFoundMessageException
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True, kw_only=True)
class GetMessageDetailQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: UUID
    message_id: UUID


@dataclass(frozen=True)
class GetMessageDetailQueryHandler(BaseQueryHandler[GetMessageDetailQuery, MessageDTO]):
    chat_repository: ChatRepository
    message_repository: MessageRepository

    async def handle(self, query: GetMessageDetailQuery) -> MessageDTO:
        user_id = int(query.user_jwt_data.id)

        member = await self.chat_repository.get_member_chat(query.chat_id, user_id, with_role=False)
        if not member or member.is_banned:
            raise NotChatMemberException(chat_id=str(query.chat_id), user_id=user_id)

        message = await self.message_repository.get_by_id(query.message_id, with_attachment=True)
        if message is None or message.chat_id != query.chat_id:
            raise NotFoundMessageException(message_id=str(query.message_id))

        return MessageDTO.model_validate(message.to_dict())
