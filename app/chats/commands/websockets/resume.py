from dataclasses import dataclass
from uuid import UUID

from app.chats.config import chat_config
from app.chats.dtos.messages import MessageDTO
from app.chats.dtos.websocket import WSConnection
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.schemas.ws import WSClientOp
from app.chats.services.message_attachments import attach_download_urls
from app.chats.services.ws import ChatConnectionManager
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.storage.service import StorageService
from app.core.utils import now_utc


@dataclass(frozen=True)
class ResumeCommand(BaseCommand):
    conn: WSConnection
    cursor: dict[str, int]
    op: WSClientOp = WSClientOp.RESUME


@dataclass(frozen=True)
class ResumeCommandHandler(BaseCommandHandler[ResumeCommand, None]):
    manager: ChatConnectionManager
    chat_repository: ChatRepository
    message_repository: MessageRepository
    storage_service: StorageService

    async def handle(self, command: ResumeCommand) -> None:

        for chat_id, cursor_seq in command.cursor.items():
            await self.manager.subscribe_chat(command.conn, chat_id)
            event = {
                "type": "ws.subscribed",
                "chat_id": chat_id,
                "payload": {"last_seq": cursor_seq},
                "ts": now_utc().isoformat()
            }
            command.conn.try_send(event)
            limit = chat_config.WS_REPLAY_BATCH_SIZE
            cursor_seq = max(0, cursor_seq)
            messages = await self.message_repository.get_chat_messages_after_seq(
                chat_id=UUID(chat_id),
                last_seq=cursor_seq,
                limit=limit,
            )
            batch = messages[:limit]
            next_last_seq = batch[-1].seq if batch else cursor_seq
            command.conn.last_seq_by_chat[chat_id] = next_last_seq

            command.conn.try_send(
                {
                    "type": "ws.history",
                    "chat_id": str(chat_id),
                    "payload": {
                        "after_seq": cursor_seq,
                        "messages": [
                            message.model_dump(mode="json")
                            for message in await attach_download_urls(
                                [MessageDTO.model_validate(item.to_dict()) for item in batch],
                                self.storage_service,
                            )
                        ],
                        "has_more": len(messages) > limit,
                        "next_last_seq": next_last_seq,
                    },
                    "ts": now_utc().isoformat()
                },
            )
