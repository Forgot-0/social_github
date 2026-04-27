import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
)
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChangeMemberRoleCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: UUID
    target_user_id: int
    role_id: int


@dataclass(frozen=True)
class ChangeMemberRoleCommandHandler(BaseCommandHandler[ChangeMemberRoleCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    chat_access_service: ChatAccessService

    async def handle(self, command: ChangeMemberRoleCommand) -> None:
        requester_id = int(command.user_jwt_data.id)
        requester = await self.chat_repository.get_member_chat(command.chat_id, requester_id, with_role=True)

        target = await self.chat_repository.get_member_chat(command.chat_id, command.target_user_id, with_role=True)
        if not target:
            raise NotChatMemberException(chat_id=str(command.chat_id), user_id=command.target_user_id)

        if not self.chat_access_service.update_member(
            user_jwt_data=command.user_jwt_data,
            requester=requester,
            target=target,
            must_permissions={"role:change" }
        ): raise AccessDeniedChatException(chat_id=str(command.chat_id), requester_id=requester_id)

        target.role_id = command.role_id
        await self.session.commit()

        logger.info(
            "Change role",
            extra={
                "chat_id": command.chat_id,
                "target": command.target_user_id,
                "by": requester_id,
                "role_id": command.role_id
            },
        )

