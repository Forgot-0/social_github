import logging

from dishka import AsyncContainer
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.chats.commands.messages.send_message import SendMessageCommand
from app.chats.dtos.chats import ChatDTO
from app.chats.dtos.messages import MessageCursorPage
from app.chats.queries.messages.get_list_by_chat import GetMessagesQuery
from app.chats.repositories.chats import ChatRepository
from app.chats.schemas.messages.requests import GetMessagesRequest, SendMessageRequests
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.core.services.auth.jwt_manager import JWTManager
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(route_class=DishkaRoute)


@router.post("/{recipient_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    message_request: SendMessageRequests,
    mediator: FromDishka[BaseMediator],
    user_jwt: CurrentUserJWTData,
) -> dict:
    message_id, *_ = await mediator.handle_command(
        SendMessageCommand(
            sender_jwt=user_jwt,
            recipient_id=message_request.recipient_id,
            text=message_request.message,
        )
    )
    return {"message_id": message_id}


@router.get("/{chat_id}/messages", status_code=status.HTTP_200_OK)
async def get_messages(
    chat_id: int,
    message_request: GetMessagesRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt: CurrentUserJWTData,
) -> MessageCursorPage:
    return await mediator.handle_query(
        GetMessagesQuery(
            chat_id=chat_id,
            user_jwt=user_jwt,
            limit=message_request.limit,
            before_id=message_request.before_id,
        )
    )


@router.get("/", status_code=status.HTTP_200_OK)
async def get_my_chats(
    user_jwt: CurrentUserJWTData,
    chat_repository: FromDishka[ChatRepository],
) -> list[ChatDTO]:
    chats = await chat_repository.get_user_chats(int(user_jwt.id))
    return [ChatDTO.model_validate(c.to_dict()) for c in chats]


@router.websocket("/ws/{chat_id}")
async def chat_websocket(
    chat_id: int,
    websocket: WebSocket,
    container: FromDishka[AsyncContainer],
) -> None:

    connection_manager = await container.get(BaseConnectionManager)
    jwt_manager = await container.get(JWTManager)

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    try:
        token_data = await jwt_manager.validate_token(token)
    except Exception:
        await websocket.close(code=4003)
        return

    connection_key = f"chat:{chat_id}"
    await connection_manager.accept_connection(websocket, connection_key)
    logger.info("WS connected", extra={"chat_id": chat_id, "user": token_data.sub})

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")

            if event == "typing":
                await connection_manager.publish(
                    connection_id=connection_key,
                    payload={"event": "typing", "user_id": token_data.sub, "chat_id": chat_id},
                )
            elif event == "read":
                # fire-and-forget без roundtrip в БД
                pass

    except WebSocketDisconnect:
        await connection_manager.remove_connection(websocket, connection_key)
        logger.info("WS disconnected", extra={"chat_id": chat_id, "user": token_data.sub})
