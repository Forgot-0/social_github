from dataclasses import dataclass
from uuid import UUID

from app.chats.dtos.members import ListMembers, MemberChatDTO, MemberPresenceDTO
from app.chats.exceptions import NotChatMemberException, NotFoundChatException
from app.chats.repositories.chat import ChatRepository
from app.chats.services.presence import PresenceService
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True, kw_only=True)
class GetChatMembersQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: UUID
    limit: int = 100
    cursor_user_id: int | None = None
    include_presence: bool = False


@dataclass(frozen=True)
class GetChatMembersQueryHandler(BaseQueryHandler[GetChatMembersQuery, ListMembers]):
    chat_repository: ChatRepository
    presence_service: PresenceService

    async def handle(self, query: GetChatMembersQuery) -> ListMembers:
        requester_id = int(query.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(query.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=str(query.chat_id))

        requester = await self.chat_repository.get_member_chat(query.chat_id, requester_id, with_role=False)
        if requester is None or requester.is_banned:
            raise NotChatMemberException(chat_id=str(query.chat_id), user_id=requester_id)

        limit = min(max(query.limit, 1), 500)
        members = await self.chat_repository.get_chat_members(
            chat_id=query.chat_id,
            limit=limit,
            cursor_user_id=query.cursor_user_id,
        )
        page = members[:limit]
        user_ids = [int(member.user_id) for member in page]

        presence: list[MemberPresenceDTO] = []
        if query.include_presence and user_ids:
            online_by_user = await self.presence_service.get_online_status(user_ids)
            presence = [
                MemberPresenceDTO(user_id=user_id, is_online=online_by_user.get(user_id, False))
                for user_id in user_ids
            ]

        return ListMembers(
            members=[MemberChatDTO.model_validate(member.to_dict()) for member in page],
            has_next=len(members) > limit,
            next_user_id=page[-1].user_id if len(members) > limit and page else None,
            presence=presence,
        )
