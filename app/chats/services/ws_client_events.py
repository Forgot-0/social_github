from dataclasses import dataclass

from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.schemas.ws import WSClientEvent, WSEventType
from app.chats.services.delivery import DeliveryTrackingService
from app.core.utils import now_utc
from app.core.websockets.base import BaseConnectionManager

_TYPING_EVENTS = frozenset({WSEventType.TYPING_START, WSEventType.TYPING_STOP})


@dataclass
class ChatWebSocketClientService:
    chat_repository: ChatRepository
    connection_manager: BaseConnectionManager
    delivery_service: DeliveryTrackingService

    async def handle_client_event(self, data: dict, user_id: int) -> None:
        try:
            event = WSClientEvent.model_validate(data)
        except Exception:
            return

        if event.type in _TYPING_EVENTS:
            await self._broadcast_typing(
                chat_id=event.chat_id,
                user_id=user_id,
                event_type=event.type,
            )
        elif event.type == WSEventType.NEW_MESSAGE:
            message_id = event.payload.get("message_id")
            if message_id is not None:
                await self.delivery_service.mark_delivered(
                    chat_id=event.chat_id,
                    user_id=user_id,
                    message_id=int(message_id),
                )

    async def _broadcast_typing(
        self,
        chat_id: int,
        user_id: int,
        event_type: WSEventType,
    ) -> None:
        payload = {
            "type": event_type,
            "chat_id": chat_id,
            "payload": {"user_id": user_id, "ts": now_utc().isoformat()},
        }

        await self.connection_manager.publish(
            ChatKeys.chat_channel(chat_id),
            payload,
        )
