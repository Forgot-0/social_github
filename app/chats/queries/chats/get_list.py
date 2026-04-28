from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.chats.dtos.chats import ChatDTO, ListChats
from app.chats.dtos.members import MemberChatDTO
from app.chats.dtos.messages import ReadDetail
from app.chats.repositories.chat import ChatRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True, kw_only=True)
class GetListChatUserQuery(BaseQuery):
    user_jwt_data: UserJWTData
    limit: int = 50
    last_chat_id: UUID | None
    last_activity_at: datetime | None


@dataclass(frozen=True)
class GetListChatUserQueryHandler(BaseQueryHandler[GetListChatUserQuery, ListChats]):
    chat_repository: ChatRepository

    async def handle(self, query: GetListChatUserQuery) -> ListChats:
        chats = await self.chat_repository.get_chats(
            user_id=int(query.user_jwt_data.id),
            limit=query.limit,
            last_activity_at=query.last_activity_at,
            chat_id=query.last_chat_id
        )

        return ListChats(
            has_next=len(chats) > query.limit,
            chats=[ChatDTO(
                id=chat[0].id,
                seq_counter=chat[0].seq_counter,
                last_activity_at=chat[0].last_activity_at,
                type=chat[0].type,
                name=chat[0].name,
                description=chat[0].description,
                avatar_s3_key=chat[0].avatar_s3_key,
                is_public=chat[0].is_public,
                created_by=chat[0].created_by,
                member_count=chat[0].member_count,
                unread_count=(
                    chat[0].seq_counter-chat[2].last_read_message_seq
                    if chat[2] is not None
                    else 99
                ),
                me=MemberChatDTO.model_validate(chat[1].to_dict()),
                last_read=ReadDetail.model_validate(chat[2].to_dict() if chat[2] is not None else None)
            ) for chat in chats],
            next_date=chats[-1][0].last_activity_at,
            next_chat_id=chats[-1][0].id
        )

