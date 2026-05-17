from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Header, Query, status
from redis.asyncio import Redis

from app.chats.commands.messages.delete import DeleteMessageCommand
from app.chats.commands.messages.forward import ForwardMessageCommand
from app.chats.commands.messages.mark_read import MarkAsReadCommand
from app.chats.commands.messages.modify import EditMessageCommand
from app.chats.commands.messages.send import SendMessageCommand
from app.chats.config import chat_config
from app.chats.dtos.messages import MessageDTO, MessagesDTO
from app.chats.exceptions import IdempotencyConflictException
from app.chats.queries.messages.get_context import GetMessageContextQuery
from app.chats.queries.messages.get_detail import GetMessageDetailQuery
from app.chats.queries.messages.get_list import GetMessagesQuery
from app.chats.schemas.rest import EditMessageRequest, ForwardMessageRequest, MarkReadRequest, SendMessageRequest
from app.core.api.rate_limiter import ConfigurableRateLimiter
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter(route_class=DishkaRoute)

message_write_limiter = ConfigurableRateLimiter(
    times=chat_config.RATE_LIMIT_MESSAGES_PER_SECOND,
    seconds=1,
)


@router.get("")
async def list_messages(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
    limit: int = Query(default=30, ge=1, le=100),
    cursor_message_seq: int | None = Query(default=None, ge=0),
) -> MessagesDTO:
    return await mediator.handle_query(
        GetMessagesQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            limit=limit,
            cursor_message_seq=cursor_message_seq,
        )
    )


@router.get("/context")
async def get_message_context(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
    target_seq: int = Query(ge=0),
    limit: int = Query(default=40, ge=1, le=100),
) -> MessagesDTO:
    return await mediator.handle_query(
        GetMessageContextQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_seq=target_seq,
            limit=limit,
        )
    )


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(message_write_limiter)])
async def send_message(
    chat_id: UUID,
    payload: SendMessageRequest,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
    redis: FromDishka[Redis],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> MessageDTO:
    cache_key = None
    lock_key = None
    if idempotency_key:
        cache_key = f"chat:idempotency:send:{user_jwt_data.id}:{chat_id}:{idempotency_key}"
        lock_key = f"{cache_key}:lock"
        cached = await redis.get(cache_key)
        if cached:
            return MessageDTO.model_validate_json(cached)
        locked = await redis.set(lock_key, "1", ex=30, nx=True)
        if not locked:
            raise IdempotencyConflictException(key=idempotency_key)

    try:
        result, *_ = await mediator.handle_command(
            SendMessageCommand(
                chat_id=chat_id,
                content=payload.content,
                reply_to_id=payload.reply_to_id,
                message_type=payload.message_type,
                upload_tokens=payload.upload_tokens,
                user_jwt_data=user_jwt_data,
            )
        )
        if cache_key:
            await redis.setex(cache_key, 86_400, result.model_dump_json())
        return result
    finally:
        if lock_key:
            await redis.delete(lock_key)


@router.get("/{message_id}")
async def get_message_detail(
    chat_id: UUID,
    message_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> MessageDTO:
    return await mediator.handle_query(
        GetMessageDetailQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
        )
    )


@router.patch("/{message_id}")
async def edit_message(
    chat_id: UUID,
    message_id: UUID,
    payload: EditMessageRequest,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> MessageDTO:
    msg, *_ = await mediator.handle_command(
        EditMessageCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
            new_content=payload.content,
        )
    )
    return msg


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    chat_id: UUID,
    message_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(
        DeleteMessageCommand(
            chat_id=chat_id,
            message_id=message_id,
            user_jwt_data=user_jwt_data,
        )
    )


@router.post("/forward", status_code=status.HTTP_201_CREATED, dependencies=[Depends(message_write_limiter)])
async def forward_message(
    chat_id: UUID,
    payload: ForwardMessageRequest,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> MessageDTO:
    msg, *_ = await mediator.handle_command(
        ForwardMessageCommand(
            user_jwt_data=user_jwt_data,
            source_chat_id=payload.source_chat_id,
            source_message_id=payload.source_message_id,
            target_chat_id=chat_id,
            comment=payload.comment,
        )
    )
    return msg


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    chat_id: UUID,
    payload: MarkReadRequest,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(
        MarkAsReadCommand(
            chat_id=chat_id,
            message_seq=payload.message_seq,
            user_jwt_data=user_jwt_data,
        )
    )
