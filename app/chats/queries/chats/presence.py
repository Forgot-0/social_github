from dataclasses import dataclass

from app.chats.dtos.chats import ChatPresenceDTO
from app.chats.dtos.members import MemberPresenceDTO
from app.chats.dtos.messages import MessageDeliveryStatusDTO
from app.chats.exceptions import NotChatMemberException
from app.chats.repositories.chat import ChatRepository
from app.chats.services.delivery import DeliveryTrackingService
from app.chats.services.presence import PresenceService
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True)
class GetChatPresenceQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: int


@dataclass(frozen=True)
class GetChatPresenceQueryHandler(
    BaseQueryHandler[GetChatPresenceQuery, ChatPresenceDTO]
):
    chat_repository: ChatRepository
    presence_service: PresenceService

    async def handle(self, query: GetChatPresenceQuery) -> ChatPresenceDTO:
        user_id = int(query.user_jwt_data.id)

        member = await self.chat_repository.get_member(query.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=query.chat_id, user_id=user_id)

        member_ids = await self.chat_repository.get_member_user_ids(query.chat_id)
        online_map = await self.presence_service.get_online_status(member_ids)

        members = [
            MemberPresenceDTO(user_id=uid, is_online=online_map.get(uid, False))
            for uid in member_ids
        ]
        return ChatPresenceDTO(
            chat_id=query.chat_id,
            members=members,
            online_count=sum(1 for m in members if m.is_online),
        )



@dataclass(frozen=True)
class GetMessageDeliveryQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: int
    message_id: int


@dataclass(frozen=True)
class GetMessageDeliveryQueryHandler(
    BaseQueryHandler[GetMessageDeliveryQuery, MessageDeliveryStatusDTO]
):
    chat_repository: ChatRepository
    delivery_service: DeliveryTrackingService

    async def handle(self, query: GetMessageDeliveryQuery) -> MessageDeliveryStatusDTO:
        user_id = int(query.user_jwt_data.id)

        member = await self.chat_repository.get_member(query.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=query.chat_id, user_id=user_id)

        member_ids = await self.chat_repository.get_member_user_ids(query.chat_id)
        delivery_map = await self.delivery_service.get_delivery_status_for_message(
            chat_id=query.chat_id,
            user_ids=member_ids,
            message_id=query.message_id,
        )
        return MessageDeliveryStatusDTO(
            message_id=query.message_id,
            delivered_to=delivery_map,
        )
