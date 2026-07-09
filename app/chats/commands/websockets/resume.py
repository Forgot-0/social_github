from dataclasses import dataclass
from uuid import UUID

from app.chats.config import chat_config
from app.chats.dtos.messages import MessageDTO
from app.chats.dtos.websocket import WSConnection
from app.chats.exceptions import MaxLimitCursorError
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.schemas.ws import WSClientOp
from app.chats.services.messages import MessageService
from app.chats.services.ws import ChatConnectionManager
from app.core.commands import BaseCommand, BaseCommandHandler
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
    message_service: MessageService

    async def handle(self, command: ResumeCommand) -> None:
        if len(command.cursor) > 20:
            raise MaxLimitCursorError(max_len=20, current_len=len(command.cursor))

        for chat_id, cursor_seq in command.cursor.items():
            member = await self.chat_repository.get_member_chat(
                chat_id=UUID(chat_id),
                member_id=command.conn.user_id,
                with_role=False
            )
            if member is None or member.is_banned:
                event = {
                    "type": "ws.error",
                    "code": "NOT_CHAT_MEMBER",
                    "ts": now_utc().isoformat()
                }
                command.conn.try_send(event)
                return

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
                            for message in await self.message_service.attach_download_urls([
                                MessageDTO.model_validate(item) for item in batch
                            ])
                        ],
                        "has_more": len(messages) > limit,
                        "next_last_seq": next_last_seq,
                    },
                    "ts": now_utc().isoformat()
                },
            )
