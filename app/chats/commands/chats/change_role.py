from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.keys import ChatKeys
from app.chats.models.chat_members import MemberRole
from app.chats.models.permission import ROLE_PERMISSIONS, Permission
from app.chats.repositories.chat import ChatRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChangeMemberRoleCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    target_user_id: int
    new_role: MemberRole


@dataclass(frozen=True)
class ChangeMemberRoleCommandHandler(BaseCommandHandler[ChangeMemberRoleCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository


    async def handle(self, command: ChangeMemberRoleCommand) -> None:
        requester_id = int(command.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(command.chat_id)
        if not chat:
            raise NotFoundChatException(chat_id=command.chat_id)

        requester = await self.chat_repository.get_member(command.chat_id, requester_id)
        if not requester:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=requester_id)

        perms = ROLE_PERMISSIONS.get(requester.role, set())
        if Permission.CHANGE_ROLES not in perms:
            raise AccessDeniedChatException()

        target = await self.chat_repository.get_member(command.chat_id, command.target_user_id)
        if not target:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=command.target_user_id)

        if len(perms) <= len(ROLE_PERMISSIONS.get(target.role, set())):
            raise AccessDeniedChatException()

        target.role = command.new_role
        await self.chat_repository.invalidate_cache(ChatKeys.chat_member_count(chat.id))
        await self.session.commit()

        logger.info(
            "Member removed",
            extra={"chat_id": command.chat_id, "target": command.target_user_id, "by": requester_id},
        )

