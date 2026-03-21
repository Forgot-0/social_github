import asyncio
import logging

from dishka.integrations.fastapi import DishkaRoute, inject, FromDishka
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.schemas.ws import WSClientEvent, WSEventType
from app.chats.services.delivery import DeliveryTrackingService
from app.chats.services.presence import PresenceService
from app.core.services.auth.jwt_manager import JWTManager
from app.core.services.auth.dto import UserJWTData, Token
from app.core.websockets.base import BaseConnectionManager
from app.core.utils import now_utc

_TYPING_EVENTS = {WSEventType.TYPING_START, WSEventType.TYPING_STOP}


logger = logging.getLogger(__name__)

router = APIRouter(route_class=DishkaRoute)


@router.websocket("/ws")
@inject
async def websocket_endpoint(
    websocket: WebSocket,
    jwt_manager: FromDishka[JWTManager],
    connection_manager: FromDishka[BaseConnectionManager],
    chat_repository: FromDishka[ChatRepository],
    presence_service: FromDishka[PresenceService],
    delivery_service: FromDishka[DeliveryTrackingService],
    token: str = Query(..., description="JWT access token"),
) -> None:
    try:
        token_data: Token = await jwt_manager.validate_token(token)
        user_data = UserJWTData.create_from_token(token_data)
        user_id = int(user_data.id)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    channel_key = ChatKeys.user_channel(user_id)
    await connection_manager.accept_connection(websocket, channel_key)
    await presence_service.set_online(user_id)
    logger.info("WS connected", extra={"user_id": user_id})

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=45.0)
            except asyncio.TimeoutError:
                await presence_service.refresh(user_id)
                continue

            await _handle_client_event(
                data=data,
                user_id=user_id,
                connection_manager=connection_manager,
                chat_repository=chat_repository,
                delivery_service=delivery_service,
            )

    except WebSocketDisconnect:
        logger.info("WS disconnected", extra={"user_id": user_id})
    except Exception as exc:
        logger.exception("WS error", extra={"user_id": user_id, "error": str(exc)})
    finally:
        await presence_service.set_offline(user_id)
        await connection_manager.remove_connection(websocket, channel_key)


async def _handle_client_event(
    data: dict,
    user_id: int,
    connection_manager: BaseConnectionManager,
    chat_repository: ChatRepository,
    delivery_service: DeliveryTrackingService,
) -> None:
    try:
        event = WSClientEvent.model_validate(data)
    except Exception:
        return

    if event.type in _TYPING_EVENTS:
        await _broadcast_typing(
            chat_id=event.chat_id,
            user_id=user_id,
            event_type=event.type,
            connection_manager=connection_manager,
            chat_repository=chat_repository,
        )
    elif event.type == WSEventType.NEW_MESSAGE:
        message_id = event.payload.get("message_id")
        if message_id:
            await delivery_service.mark_delivered(
                chat_id=event.chat_id,
                user_id=user_id,
                message_id=int(message_id),
            )


async def _broadcast_typing(
    chat_id: int,
    user_id: int,
    event_type: WSEventType,
    connection_manager: BaseConnectionManager,
    chat_repository: ChatRepository,
) -> None:
    member = await chat_repository.get_member(chat_id, user_id)
    if not member or member.is_muted:
        return

    member_ids = await chat_repository.get_member_user_ids(chat_id)
    payload = {
        "type": event_type,
        "chat_id": chat_id,
        "payload": {"user_id": user_id, "ts": now_utc().isoformat()},
    }
    for uid in member_ids:
        if uid != user_id:
            await connection_manager.publish(ChatKeys.user_channel(uid), payload)