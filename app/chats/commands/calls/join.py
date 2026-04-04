from dataclasses import dataclass
import logging
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.dtos.livekit import JoinTokenDTO
from app.chats.exceptions import NotChatMemberException, NotFoundChatException
from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.schemas.ws import WSEventType
from app.chats.services.livekit_service import LiveKitService
from app.chats.services.system_message import SystemMessageService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JoinCallCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int


@dataclass(frozen=True)
class JoinCallCommandHandler(BaseCommandHandler[JoinCallCommand, JoinTokenDTO]):
    session: AsyncSession
    chat_repository: ChatRepository
    livekit_service: LiveKitService
    connection_manager: BaseConnectionManager
    system_message_service: SystemMessageService

    async def handle(self, command: JoinCallCommand) -> JoinTokenDTO:
        user_id = int(command.user_jwt_data.id)
        username = command.user_jwt_data.username

        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=command.chat_id)

        member = await self.chat_repository.get_member(command.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=user_id)

        slug = ChatKeys.chat_call_slug(command.chat_id)

        token = self.livekit_service.generate_join_token(
            slug=slug,
            user_id=str(user_id),
            username=username,
        )

        await self.system_message_service.send(
            chat_id=command.chat_id,
            content=f"📞 {username} joined the call",
        )

        await self.connection_manager.publish(
            ChatKeys.chat_channel(command.chat_id),
            {
                "type": WSEventType.CALL_JOINED,
                "chat_id": command.chat_id,
                "payload": {
                    "user_id": user_id,
                    "username": username,
                },
            },
        )

        logger.info(
            "User joined call",
            extra={"chat_id": command.chat_id, "user_id": user_id, "slug": slug},
        )

        return JoinTokenDTO(
            token=token,
            slug=slug,
            livekit_url=self.livekit_service.url,
        )
