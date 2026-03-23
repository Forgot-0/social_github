from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.chats.commands.messages.delete import DeleteMessageCommand
from app.chats.commands.messages.mark_read import MarkAsReadCommand
from app.chats.commands.messages.modify import EditMessageCommand
from app.chats.commands.messages.send import SendMessageCommand, SendMessageResult
from app.chats.dtos.messages import MessageCursorPage
from app.chats.queries.messages.get_list import GetMessagesQuery
from app.chats.schemas.messages.requests import (
    EditMessageRequest,
    GetMessagesRequest,
    MarkAsReadRequest,
    SendMessageRequest
)
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter(route_class=DishkaRoute)



@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to a chat",
)
async def send_message(
    chat_id: int,
    request: SendMessageRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> SendMessageResult:
    results = await mediator.handle_command(
        SendMessageCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            content=request.content,
            reply_to_id=request.reply_to_id,
            message_type=request.message_type,
        )
    )
    return next(iter(results))


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Get paginated messages (cursor-based)",
)
async def get_messages(
    chat_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
    params: GetMessagesRequest = Query(...),
) -> MessageCursorPage:
    return await mediator.handle_query(
        GetMessagesQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            limit=params.limit,
            before_id=params.before_id,
        )
    )


@router.put(
    "/{message_id}",
    status_code=status.HTTP_200_OK,
    summary="Edit own message content",
)
async def edit_message(
    chat_id: int,
    message_id: int,
    request: EditMessageRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        EditMessageCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
            new_content=request.content,
        )
    )


@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a message (soft-delete)",
)
async def delete_message(
    chat_id: int,
    message_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        DeleteMessageCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
        )
    )


@router.post(
    "/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark messages as read up to a given message_id",
)
async def mark_as_read(
    chat_id: int,
    request: MarkAsReadRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        MarkAsReadCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=request.message_id,
        )
    )

