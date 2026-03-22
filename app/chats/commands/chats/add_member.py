from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.config import chat_config
from app.chats.exceptions import (
    AccessDeniedChatException,
    AlreadyMemberException,
    MemberLimitExceededException,
    NotFoundChatException,
    NotChatMemberException,
)
from app.chats.models.chat_members import MemberRole
from app.chats.models.permission import ROLE_PERMISSIONS, Permission
from app.chats.repositories.chat import ChatRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddMemberCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    target_user_id: int
    role: MemberRole = MemberRole.MEMBER


@dataclass(frozen=True)
class AddMemberCommandHandler(BaseCommandHandler[AddMemberCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository

    async def handle(self, command: AddMemberCommand) -> None:
        requester_id = int(command.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(command.chat_id, with_members=True)
        if not chat:
            raise NotFoundChatException(chat_id=command.chat_id)

        requester = await self.chat_repository.get_member(command.chat_id, requester_id)
        if not requester:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=requester_id)

        if Permission.ADD_MEMBERS not in ROLE_PERMISSIONS.get(requester.role, set()):
            raise AccessDeniedChatException()

        existing = await self.chat_repository.get_member(command.chat_id, command.target_user_id)
        if existing:
            raise AlreadyMemberException(user_id=command.target_user_id, chat_id=command.chat_id)

        count = await self.chat_repository.get_member_count(command.chat_id)
        if count >= chat_config.MAX_MEMEBERS:
            raise MemberLimitExceededException(limit=chat_config.MAX_MEMEBERS)

        await self.chat_repository.add_member(
            chat_id=command.chat_id,
            user_id=command.target_user_id,
            role=command.role,
        )
        await self.session.commit()

        logger.info(
            "Member added to chat",
            extra={"chat_id": command.chat_id, "user_id": command.target_user_id},
        )
