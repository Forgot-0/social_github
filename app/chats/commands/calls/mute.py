from dataclasses import dataclass
import logging

from app.chats.exceptions import (
    AccessDeniedChatException,
    NoActiveCallException,
    NotChatMemberException,
)
from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.livekit_service import LiveKitService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MuteParticipantCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    target_user_id: int
    muted: bool = True


@dataclass(frozen=True)
class MuteParticipantCommandHandler(BaseCommandHandler[MuteParticipantCommand, None]):
    chat_repository: ChatRepository
    chat_access_servise: ChatAccessService
    livekit_service: LiveKitService

    async def handle(self, command: MuteParticipantCommand) -> None:
        requester_id = int(command.user_jwt_data.id)

        requester = await self.chat_repository.get_member(
            command.chat_id, requester_id, with_role=True
        )
        if not requester:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=requester_id)

        target = await self.chat_repository.get_member(
            command.chat_id, command.target_user_id, with_role=True
        )
        if not target:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=command.target_user_id)

        has_perm = self.chat_access_servise.update_member(
            user_jwt_data=command.user_jwt_data,
            requester=requester,
            target=target,
            must_permissions={"call:mute_member"},
        )
        if not has_perm:
            raise AccessDeniedChatException()

        slug = ChatKeys.chat_call_slug(command.chat_id)

        await self.livekit_service.mute_participant(
            slug=slug,
            identity=str(command.target_user_id),
            muted=command.muted,
        )

        action = "muted" if command.muted else "unmuted"
        logger.info(
            "Call participant %s",
            action,
            extra={
                "chat_id": command.chat_id,
                "target": command.target_user_id,
                "by": requester_id,
            },
        )
