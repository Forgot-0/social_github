import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
)
from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BanMemberCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    target_user_id: int
    ban: bool = True


@dataclass(frozen=True)
class BanMemberCommandHandler(BaseCommandHandler[BanMemberCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    chat_access_servise: ChatAccessService
    connection_manager: BaseConnectionManager

    async def handle(self, command: BanMemberCommand) -> None:
        requester_id = int(command.user_jwt_data.id)

        requester = await self.chat_repository.get_member(command.chat_id, requester_id, with_role=True)

        target = await self.chat_repository.get_member(command.chat_id, command.target_user_id, with_role=True)
        if not target:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=command.target_user_id)

        if not self.chat_access_servise.update_member(
            user_jwt_data=command.user_jwt_data,
            requester=requester,
            target=target,
            must_permissions={"member:ban"}
        ): raise AccessDeniedChatException()

        target.is_banned = command.ban
        await self.session.commit()

        source_key = ChatKeys.user_channel(command.target_user_id)
        target_key = ChatKeys.chat_channel(command.chat_id)
        if command.ban:
            await self.connection_manager.unbind_key_connections(
                source_key=source_key,
                target_key=target_key,
            )
        else:
            await self.connection_manager.bind_key_connections(
                source_key=source_key,
                target_key=target_key,
            )

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
