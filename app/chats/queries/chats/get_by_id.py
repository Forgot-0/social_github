from dataclasses import dataclass

from app.chats.dtos.chats import ChatDetailDTO
from app.chats.dtos.members import MemberInfoDTO
from app.chats.exceptions import NotChatMemberException, NotFoundChatException
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True)
class GetChatByIdQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: int


@dataclass(frozen=True)
class GetChatByIdQueryHandler(BaseQueryHandler[GetChatByIdQuery, ChatDetailDTO]):
    chat_repository: ChatRepository
    read_receipt_repository: ReadReceiptRepository

    async def handle(self, query: GetChatByIdQuery) -> ChatDetailDTO:
        user_id = int(query.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(query.chat_id, with_members=True)
        if not chat:
            raise NotFoundChatException(chat_id=query.chat_id)

        member = await self.chat_repository.get_member(chat.id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=chat.id, user_id=user_id)

        unread = await self.read_receipt_repository.get_unread_count(user_id, chat.id)

        return ChatDetailDTO(
            id=chat.id,
            type=chat.type,
            name=chat.name,
            description=chat.description,
            avatar_url=chat.avatar_url,
            is_public=chat.is_public,
            created_by=chat.created_by,
            members=[
                MemberInfoDTO(
                    user_id=m.user_id,
                    role_id=m.role_id,
                    is_muted=m.is_muted,
                )
                for m in chat.members
            ],
            unread_count=unread,
        )
