import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BanMemberCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: UUID
    target_user_id: int
    ban: bool = True


@dataclass(frozen=True)
class BanMemberCommandHandler(BaseCommandHandler[BanMemberCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    chat_access_service: ChatAccessService
    event_bus: BaseEventBus

    async def handle(self, command: BanMemberCommand) -> None:
        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=str(command.chat_id))

        requester_id = int(command.user_jwt_data.id)
        requester = await self.chat_repository.get_member_chat(command.chat_id, requester_id, with_role=True)

        target = await self.chat_repository.get_member_chat(command.chat_id, command.target_user_id, with_role=True)
        if target is None:
            raise NotChatMemberException(chat_id=str(command.chat_id), user_id=command.target_user_id)

        if not await self.chat_access_service.update_member(
            user_jwt_data=command.user_jwt_data,
            requester=requester,
            target=target,
            must_permissions={"member:ban"}
        ): raise AccessDeniedChatException(chat_id=str(command.chat_id), requester_id=requester_id)

        target.is_banned = command.ban
        chat.ban_member(command.target_user_id, requester_id, command.ban)
        await self.session.commit()
        await self.event_bus.publish(chat.pull_events())

        action = "banned" if command.ban else "unbanned"
        logger.info(
            "Member %s",
            action,
            extra={
                "chat_id": command.chat_id,
                "target": command.target_user_id,
                "by": requester_id,
            },
        )
