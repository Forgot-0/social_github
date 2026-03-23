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
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData


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

    async def handle(self, command: AddMemberCommand) -> None:
        requester_id = int(command.user_jwt_data.id)

        requester = await self.chat_repository.get_member(command.chat_id, requester_id)
        if not requester:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=requester_id)

        if not self.chat_access_servise.can_update(
            user_jwt_data=command.user_jwt_data,
            memeber=requester,
            must_permissions={"member:invite",}
        ): raise AccessDeniedChatException()

        existing = await self.chat_repository.get_member(command.chat_id, command.target_user_id)
        if existing:
            raise AlreadyMemberException(user_id=command.target_user_id, chat_id=command.chat_id)

        count = await self.chat_repository.get_member_count(command.chat_id)
        if count >= chat_config.MAX_MEMBERS:
            raise MemberLimitExceededException(limit=chat_config.MAX_MEMBERS)

        await self.chat_repository.add_member(
            chat_id=command.chat_id,
            user_id=command.target_user_id,
            role_id=command.role_id,
        )
        await self.session.commit()

        logger.info(
            "Member added to chat",
            extra={"chat_id": command.chat_id, "user_id": command.target_user_id},
        )
