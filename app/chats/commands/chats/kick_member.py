import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
)
from app.chats.keys import ChatKeys
from app.chats.models.chat import KickedChatMemberEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KickMemberCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    target_user_id: int


@dataclass(frozen=True)
class KickMemberCommandHandler(BaseCommandHandler[KickMemberCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    chat_access_servise: ChatAccessService
    event_bus: BaseEventBus

    async def handle(self, command: KickMemberCommand) -> None:
        requester_id = int(command.user_jwt_data.id)

        requester = await self.chat_repository.get_member(command.chat_id, requester_id, with_role=True)

        target = await self.chat_repository.get_member(command.chat_id, command.target_user_id, with_role=True)
        if not target:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=command.target_user_id)

        if not self.chat_access_servise.update_member(
            user_jwt_data=command.user_jwt_data,
            requester=requester,
            target=target,
            must_permissions={"member:kick"}
        ): raise AccessDeniedChatException()

        await self.session.delete(target)
        await self.chat_repository.invalidate_cache(ChatKeys.chat_member_count(command.chat_id))
        await self.session.commit()
        await self.event_bus.publish(
            [KickedChatMemberEvent(
                chat_id=command.chat_id,
                requester_id=requester_id,
                target_user_id=target.user_id,
            )]
        )

        logger.info(
            "Member removed",
            extra={"chat_id": command.chat_id, "target": command.target_user_id, "by": requester_id},
        )

