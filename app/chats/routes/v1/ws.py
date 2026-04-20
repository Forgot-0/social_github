import asyncio
import logging

from dishka import AsyncContainer
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi_limiter.depends import WebSocketRateLimiter

from app.chats.config import chat_config
from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.services.presence import PresenceService
from app.chats.services.ws_client_events import ChatWebSocketClientService
from app.core.services.auth.dto import Token, UserJWTData
from app.core.services.auth.jwt_manager import JWTManager
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
@inject
async def websocket_endpoint(
    websocket: WebSocket,
    container: FromDishka[AsyncContainer],
    jwt_manager: FromDishka[JWTManager],
    connection_manager: FromDishka[BaseConnectionManager],
    presence_service: FromDishka[PresenceService],
    token: str = Query(...),
) -> None:
    try:
        token_data: Token = await jwt_manager.validate_token(token)
        user_data = UserJWTData.create_from_token(token_data)
        user_id = int(user_data.id)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    channel_key = ChatKeys.user_channel(user_id)
    existing = connection_manager.connections_map.get(channel_key, set())
    if len(existing) >= chat_config.WS_MAX_CONNECTIONS_PER_USER:
        await websocket.close(code=1008, reason="Too many connections")
        return

    await connection_manager.accept_connection(websocket, channel_key)
    async with container() as request_container:
        chat_repository = await request_container.get(ChatRepository)
        chat_ids = await chat_repository.get_user_chat_ids(user_id)
        for chat_id in chat_ids:
            chat_key = ChatKeys.chat_channel(chat_id)
            await connection_manager.bind_connection(websocket, chat_key)

    await presence_service.set_online(user_id)
    logger.info("WS connected", extra={"user_id": user_id})

    rate_limit = WebSocketRateLimiter(chat_config.RATE_LIMIT_MESSAGES_PER_SECOND, seconds=1)

    try:
        while True:
            await rate_limit(websocket, context_key=str(user_id))

            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=45.0)
            except TimeoutError:
                await presence_service.refresh(user_id)
                continue

            async with container() as request_container:
                ws_client_service = await request_container.get(ChatWebSocketClientService)
                await ws_client_service.handle_client_event(
                    data=data,
                    user_id=user_id,
                )

    except WebSocketDisconnect:
        logger.info("WS disconnected", extra={"user_id": user_id})
    except Exception as exc:
        logger.exception("WS error", extra={"user_id": user_id, "error": str(exc)})
    finally:
        await presence_service.set_offline(user_id)
        await connection_manager.remove_connection(websocket, channel_key)
