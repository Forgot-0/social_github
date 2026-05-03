import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.dtos.livekit import JoinTokenDTO
from app.chats.exceptions import NotChatMemberException, NotFoundChatException
from app.chats.models.message import Message, MessageType
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.services.livekit_service import LiveKitService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.core.websockets.base import BaseConnectionManager


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JoinCallCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: UUID


@dataclass(frozen=True)
class JoinCallCommandHandler(BaseCommandHandler[JoinCallCommand, JoinTokenDTO]):
    session: AsyncSession
    chat_repository: ChatRepository
    livekit_service: LiveKitService
    connection_manager: BaseConnectionManager
    message_repository: MessageRepository
    event_bus: BaseEventBus

    async def handle(self, command: JoinCallCommand) -> JoinTokenDTO:
        user_id = int(command.user_jwt_data.id)
        username = command.user_jwt_data.username

        member = await self.chat_repository.get_member_chat(command.chat_id, user_id)
        if member is None:
            raise NotChatMemberException(chat_id=str(command.chat_id), user_id=user_id)

        chat = await self.chat_repository.get_by_id(command.chat_id, with_for_update=True)
        if chat is None:
            raise NotFoundChatException(chat_id=str(command.chat_id))

        token = self.livekit_service.generate_join_token(
            slug=str(chat.id),
            user_id=str(user_id),
            username=username,
        )
        chat.seq_counter += 1
        msg = Message.create(
            sender_id=None,
            chat_id=chat.id,
            seq=chat.seq_counter,
            content=f"📞 {username} joined the call",
            message_type=MessageType.SYSTEM
        )
        chat.update_last_activity(msg.created_at)
        await self.message_repository.create(msg)
        await self.session.commit()
        await self.event_bus.publish(msg.pull_events())
        logger.info(
            "User joined call",
            extra={"chat_id": command.chat_id, "user_id": user_id, "slug": str(chat.id)},
        )

        return JoinTokenDTO(
            token=token,
            slug=str(chat.id),
            livekit_url=self.livekit_service.url,
        )
