from dataclasses import dataclass
from uuid import UUID

from app.chats.dtos.chats import ChatDetaiDTO
from app.chats.dtos.members import MemberChatDTO
from app.chats.exceptions import NotChatMemberException, NotFoundChatException
from app.chats.repositories.chat import ChatRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True, kw_only=True)
class GetChatDetailQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: UUID


@dataclass(frozen=True)
class GetChatDetailQueryHandler(BaseQueryHandler[GetChatDetailQuery, ChatDetaiDTO]):
    chat_repository: ChatRepository

    async def handle(self, query: GetChatDetailQuery) -> ChatDetaiDTO:
        user_id = int(query.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(query.chat_id, with_members=True)
        if chat is None:
            raise NotFoundChatException(chat_id=str(query.chat_id))

        member = await self.chat_repository.get_member_chat(query.chat_id, user_id, with_role=False)
        if member is None or member.is_banned:
            raise NotChatMemberException(chat_id=str(query.chat_id), user_id=user_id)

        return ChatDetaiDTO(
            id=chat.id,
            seq_counter=chat.seq_counter,
            last_activity_at=chat.last_activity_at,
            type=chat.type,
            name=chat.name,
            description=chat.description,
            avatar_s3_key=chat.avatar_s3_key,
            is_public=chat.is_public,
            admin_only=chat.admin_only,
            slow_mode_seconds=chat.slow_mode_seconds,
            permissions=chat.permissions or {},
            created_by=chat.created_by,
            member_count=chat.member_count,
            members=[MemberChatDTO.model_validate(member.to_dict()) for member in chat.members],
        )
