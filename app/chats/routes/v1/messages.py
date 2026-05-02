from __future__ import annotations

from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Header, Query, status
from redis.asyncio import Redis

from app.chats.commands.messages.delete import DeleteMessageCommand, DeleteMessageCommandHandler
from app.chats.commands.messages.forward import ForwardMessageCommand, ForwardMessageCommandHandler
from app.chats.commands.messages.mark_read import MarkAsReadCommand, MarkAsReadCommandHandler
from app.chats.commands.messages.modify import EditMessageCommand, EditMessageCommandHandler
from app.chats.commands.messages.send import SendMessageCommand, SendMessageCommandHandler
from app.chats.config import chat_config
from app.chats.exceptions import IdempotencyConflictException
from app.chats.dtos.messages import MessageDTO, MessagesDTO
from app.chats.queries.messages.get_context import GetMessageContextQuery, GetMessageContextQueryHandler
from app.chats.queries.messages.get_detail import GetMessageDetailQuery, GetMessageDetailQueryHandler
from app.chats.queries.messages.get_list import GetMessagesQuery, GetMessagesQueryHandler
from app.chats.schemas.rest import EditMessageRequest, ForwardMessageRequest, MarkReadRequest, SendMessageRequest
from app.core.api.rate_limiter import ConfigurableRateLimiter
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter()

message_write_limiter = ConfigurableRateLimiter(
    times=chat_config.RATE_LIMIT_MESSAGES_PER_SECOND,
    seconds=1,
)


@router.get("", response_model=MessagesDTO)
@inject
async def list_messages(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[GetMessagesQueryHandler],
    limit: int = Query(default=30, ge=1, le=100),
    cursor_message_seq: int | None = Query(default=None, ge=0),
) -> MessagesDTO:
    return await handler.handle(
        GetMessagesQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            limit=limit,
            cursor_message_seq=cursor_message_seq,
        )
    )


@router.get("/context", response_model=MessagesDTO)
@inject
async def get_message_context(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[GetMessageContextQueryHandler],
    target_seq: int = Query(ge=0),
    limit: int = Query(default=40, ge=1, le=100),
) -> MessagesDTO:
    return await handler.handle(
        GetMessageContextQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_seq=target_seq,
            limit=limit,
        )
    )


@router.post("", response_model=MessageDTO, status_code=status.HTTP_201_CREATED, dependencies=[Depends(message_write_limiter)])
@inject
async def send_message(
    chat_id: UUID,
    payload: SendMessageRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[SendMessageCommandHandler],
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
        result = await handler.handle(
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


@router.get("/{message_id}", response_model=MessageDTO)
@inject
async def get_message_detail(
    chat_id: UUID,
    message_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[GetMessageDetailQueryHandler],
) -> MessageDTO:
    return await handler.handle(
        GetMessageDetailQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
        )
    )


@router.patch("/{message_id}", response_model=MessageDTO)
@inject
async def edit_message(
    chat_id: UUID,
    message_id: UUID,
    payload: EditMessageRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[EditMessageCommandHandler],
) -> MessageDTO:
    return await handler.handle(
        EditMessageCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
            new_content=payload.content,
        )
    )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_message(
    chat_id: UUID,
    message_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[DeleteMessageCommandHandler],
) -> None:
    await handler.handle(
        DeleteMessageCommand(
            chat_id=chat_id,
            message_id=message_id,
            user_jwt_data=user_jwt_data,
        )
    )


@router.post("/forward", response_model=MessageDTO, status_code=status.HTTP_201_CREATED, dependencies=[Depends(message_write_limiter)])
@inject
async def forward_message(
    chat_id: UUID,
    payload: ForwardMessageRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[ForwardMessageCommandHandler],
) -> MessageDTO:
    return await handler.handle(
        ForwardMessageCommand(
            user_jwt_data=user_jwt_data,
            source_chat_id=payload.source_chat_id,
            source_message_id=payload.source_message_id,
            target_chat_id=chat_id,
            comment=payload.comment,
        )
    )


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def mark_read(
    chat_id: UUID,
    payload: MarkReadRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[MarkAsReadCommandHandler],
) -> None:
    await handler.handle(
        MarkAsReadCommand(
            chat_id=chat_id,
            message_seq=payload.message_seq,
            user_jwt_data=user_jwt_data,
        )
    )
