import logging

from dishka import AsyncContainer
from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi_limiter.depends import WebSocketRateLimiter

from app.chats.commands.messages.send_message import SendMessageCommand
from app.chats.commands.reads.mark_read import MarkReadCommand
from app.chats.dtos.chats import ChatDTO
from app.chats.dtos.messages import MessageCursorPage
from app.chats.queries.messages.get_list_by_chat import GetMessagesQuery
from app.chats.repositories.chats import ChatRepository
from app.chats.schemas.messages.requests import GetMessagesRequest, SendMessageRequests
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.jwt_manager import JWTManager
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(route_class=DishkaRoute)



@router.get("/", status_code=status.HTTP_200_OK)
async def get_my_chats(
    user_jwt: CurrentUserJWTData,
    chat_repository: FromDishka[ChatRepository],
) -> list[ChatDTO]:
    chats = await chat_repository.get_user_chats(int(user_jwt.id))
    return [ChatDTO.model_validate(c.to_dict()) for c in chats]

@router.post(
    "/{recipient_id}/messages",
    status_code=status.HTTP_201_CREATED
)
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


@router.websocket("/ws/{chat_id}")
@inject
async def chat_websocket(
    chat_id: int,
    websocket: WebSocket,
    container: FromDishka[AsyncContainer],
)  -> None:

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
    ratelimit = WebSocketRateLimiter(times=1, seconds=5)

    try:
        while True:
            data = await websocket.receive_json()
            await ratelimit(websocket)

            event = data.get("event")
            async with container() as scope:
                mediator = await scope.get(BaseMediator)

                # if event == "typing":
                #     await connection_manager.publish(
                #         connection_id=connection_key,
                #         payload={"event": "typing", "user_id": token_data.sub, "chat_id": chat_id},
                #     )

                if event == "read":
                    message_id = data.get("message_id")
                    if isinstance(message_id, int):
                        await mediator.handle_command(
                            MarkReadCommand(
                                user_jwt=UserJWTData.create_from_token(token_data),
                                chat_id=chat_id,
                                message_id=message_id,
                            )
                        )

    except WebSocketDisconnect:
        await connection_manager.remove_connection(websocket, connection_key)
        logger.info("WS disconnected", extra={"chat_id": chat_id, "user": token_data.sub})
