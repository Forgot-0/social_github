import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.config import chat_config
from app.chats.exceptions import (
    AccessDeniedChatException,
    AlreadyMemberException,
    MemberLimitExceededException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddMemberCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    target_user_id: int
    role_id: int


@dataclass(frozen=True)
class AddMemberCommandHandler(BaseCommandHandler[AddMemberCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    chat_access_servise: ChatAccessService
    connection_manager: BaseConnectionManager
    event_bus: BaseEventBus

    async def handle(self, command: AddMemberCommand) -> None:
        requester_id = int(command.user_jwt_data.id)
        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=command.chat_id)

        requester = await self.chat_repository.get_member(command.chat_id, requester_id, with_role=True)
        if not requester:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=requester_id)

        if not self.chat_access_servise.can_update(
            user_jwt_data=command.user_jwt_data,
            memeber=requester,
            must_permissions={"member:invite"}
        ): raise AccessDeniedChatException()

        existing = await self.chat_repository.get_member(command.chat_id, command.target_user_id)
        if existing:
            raise AlreadyMemberException(user_id=command.target_user_id, chat_id=command.chat_id)

        count = await self.chat_repository.get_member_count(command.chat_id)
        if count >= chat_config.MAX_MEMBERS:
            raise MemberLimitExceededException(limit=chat_config.MAX_MEMBERS)

        chat.add_member(
            member_id=command.target_user_id,
            role_id=command.role_id,
        )

        await self.session.commit()
        await self.event_bus.publish(chat.pull_events())
        await self.connection_manager.bind_key_connections(
            source_key=ChatKeys.user_channel(command.target_user_id),
            target_key=ChatKeys.chat_channel(command.chat_id),
        )

        logger.info(
            "Member added to chat",
            extra={"chat_id": command.chat_id, "user_id": command.target_user_id},
        )
