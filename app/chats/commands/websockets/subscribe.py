from dataclasses import dataclass
from uuid import UUID

from app.chats.config import chat_config
from app.chats.dtos.messages import MessageDTO
from app.chats.dtos.websocket import WSConnection
from app.chats.exceptions import NotChatMemberException
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.schemas.ws import WSClientOp
from app.chats.services.ws import ChatConnectionManager
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.utils import now_utc


@dataclass(frozen=True)
class SubscribeCommand(BaseCommand):
    conn: WSConnection
    chat_id: str
    user_id: int
    last_seq: int | None = None
    op: WSClientOp = WSClientOp.SUBSCRIBE


@dataclass(frozen=True)
class SubscribeCommandHandler(BaseCommandHandler[SubscribeCommand, None]):
    manager: ChatConnectionManager
    chat_repository: ChatRepository
    message_repository: MessageRepository

    async def handle(self, command: SubscribeCommand) -> None:
        chat_id = UUID(command.chat_id)
        member = await self.chat_repository.get_member_chat(chat_id=chat_id, member_id=command.user_id, with_role=False)
        if member is None or member.is_banned:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=command.user_id)

        await self.manager.subscribe_chat(command.conn, command.chat_id)
        event = {
            "type": "ws.subscribed",
            "chat_id": str(chat_id),
            "payload": {"last_seq": command.last_seq},
            "ts": now_utc().isoformat()
        }
        command.conn.try_send(event)

        if command.last_seq is not None:
            limit = chat_config.WS_REPLAY_BATCH_SIZE
            last_seq = max(0, command.last_seq)
            messages = await self.message_repository.get_chat_messages_after_seq(
                chat_id=chat_id,
                last_seq=last_seq,
                limit=limit,
            )
            batch = messages[:limit]
            next_last_seq = batch[-1].seq if batch else last_seq
            command.conn.last_seq_by_chat[str(chat_id)] = next_last_seq

            command.conn.try_send(
                {
                    "type": "ws.history",
                    "chat_id": str(chat_id),
                    "payload": {
                        "after_seq": last_seq,
                        "messages": [
                            MessageDTO.model_validate(message.to_dict()).model_dump(mode="json")
                            for message in batch
                        ],
                        "has_more": len(messages) > limit,
                        "next_last_seq": next_last_seq,
                    },
                    "ts": now_utc().isoformat()
                },
            )
