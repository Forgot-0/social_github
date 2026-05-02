from __future__ import annotations

from datetime import datetime
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Query, status

from app.chats.commands.chats.create import CreateChatCommand, CreateChatCommandHandler
from app.chats.commands.chats.delete import DeleteChatCommand, DeleteChatCommandHandler
from app.chats.commands.chats.join import JoinChatCommand, JoinChatCommandHandler
from app.chats.commands.chats.leave import LeaveChatCommand, LeaveChatCommandHandler
from app.chats.commands.chats.update import UpdateChatCommand, UpdateChatCommandHandler
from app.chats.dtos.chats import ChatDTO, ChatDetaiDTO, ListChats
from app.chats.queries.chats.get_detail import GetChatDetailQuery, GetChatDetailQueryHandler
from app.chats.queries.chats.get_list import GetListChatUserQuery, GetListChatUserQueryHandler
from app.chats.schemas.rest import CreateChatRequest, UpdateChatRequest
from app.core.services.auth.depends import CurrentUserJWTData
from app.core.services.auth.dto import UserJWTData

router = APIRouter()


@router.get("", response_model=ListChats)
@inject
async def list_my_chats(
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[GetListChatUserQueryHandler],
    limit: int = Query(default=50, ge=1, le=100),
    last_chat_id: UUID | None = None,
    last_activity_at: datetime | None = None,
) -> ListChats:
    return await handler.handle(
        GetListChatUserQuery(
            user_jwt_data=user_jwt_data,
            limit=limit,
            last_chat_id=last_chat_id,
            last_activity_at=last_activity_at,
        )
    )


@router.post("", response_model=ChatDTO, status_code=status.HTTP_201_CREATED)
@inject
async def create_chat(
    payload: CreateChatRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[CreateChatCommandHandler],
) -> ChatDTO:
    return await handler.handle(
        CreateChatCommand(
            name=payload.name,
            description=payload.description,
            chat_type=payload.chat_type,
            member_ids=payload.member_ids,
            is_public=payload.is_public,
            admin_only=payload.admin_only,
            slow_mode_seconds=payload.slow_mode_seconds,
            permissions=payload.permissions,
            user_jwt_data=user_jwt_data,
        )
    )


@router.get("/{chat_id}", response_model=ChatDetaiDTO)
@inject
async def get_chat_detail(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[GetChatDetailQueryHandler],
) -> ChatDetaiDTO:
    return await handler.handle(GetChatDetailQuery(user_jwt_data=user_jwt_data, chat_id=chat_id))


@router.patch("/{chat_id}", response_model=ChatDTO)
@inject
async def update_chat(
    chat_id: UUID,
    payload: UpdateChatRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[UpdateChatCommandHandler],
) -> ChatDTO:
    return await handler.handle(
        UpdateChatCommand(
            chat_id=chat_id,
            name=payload.name,
            description=payload.description,
            is_public=payload.is_public,
            admin_only=payload.admin_only,
            slow_mode_seconds=payload.slow_mode_seconds,
            permissions=payload.permissions,
            user_jwt_data=user_jwt_data,
        )
    )


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_chat(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[DeleteChatCommandHandler],
) -> None:
    await handler.handle(DeleteChatCommand(user_jwt_data=user_jwt_data, chat_id=chat_id))


@router.post("/{chat_id}/join", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def join_public_chat(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[JoinChatCommandHandler],
) -> None:
    await handler.handle(JoinChatCommand(user_jwt_data=user_jwt_data, chat_id=chat_id))


@router.post("/{chat_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def leave_chat(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[LeaveChatCommandHandler],
) -> None:
    await handler.handle(LeaveChatCommand(chat_id=chat_id, user_jwt_data=user_jwt_data))
