from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData


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

    async def handle(self, command: BanMemberCommand) -> None:
        requester_id = int(command.user_jwt_data.id)

        requester = await self.chat_repository.get_member(command.chat_id, requester_id)
        if not requester:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=requester_id)

        target = await self.chat_repository.get_member(command.chat_id, command.target_user_id)
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

        action = "banned" if command.ban else "unbanned"
        logger.info(
            f"Member {action}",
            extra={
                "chat_id": command.chat_id,
                "target": command.target_user_id,
                "by": requester_id,
            },
        )
