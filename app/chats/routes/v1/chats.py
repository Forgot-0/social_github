from datetime import datetime
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.chats.commands.chats.create import CreateChatCommand
from app.chats.commands.chats.delete import DeleteChatCommand
from app.chats.commands.chats.join import JoinChatCommand
from app.chats.commands.chats.leave import LeaveChatCommand
from app.chats.commands.chats.update import UpdateChatCommand
from app.chats.dtos.chats import ChatDTO, ChatDetaiDTO, ListChats
from app.chats.queries.chats.get_detail import GetChatDetailQuery
from app.chats.queries.chats.get_list import GetListChatUserQuery
from app.chats.schemas.rest import CreateChatRequest, UpdateChatRequest
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter(route_class=DishkaRoute)


@router.get("")
async def list_my_chats(
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
    limit: int = Query(default=50, ge=1, le=100),
    last_chat_id: UUID | None = None,
    last_activity_at: datetime | None = None,
) -> ListChats:
    return await mediator.handle_query(
        GetListChatUserQuery(
            user_jwt_data=user_jwt_data,
            limit=limit,
            last_chat_id=last_chat_id,
            last_activity_at=last_activity_at,
        )
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_chat(
    payload: CreateChatRequest,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> ChatDTO:
    chat, *_ = await mediator.handle_command(
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
    return chat


@router.get("/{chat_id}")
async def get_chat_detail(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> ChatDetaiDTO:
    return await mediator.handle_query(GetChatDetailQuery(user_jwt_data=user_jwt_data, chat_id=chat_id))


@router.patch("/{chat_id}", response_model=ChatDTO)
async def update_chat(
    chat_id: UUID,
    payload: UpdateChatRequest,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> ChatDTO:
    chat, *_ = await mediator.handle_command(
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
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(DeleteChatCommand(user_jwt_data=user_jwt_data, chat_id=chat_id))


@router.post("/{chat_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_public_chat(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(JoinChatCommand(user_jwt_data=user_jwt_data, chat_id=chat_id))


@router.post("/{chat_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_chat(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(LeaveChatCommand(chat_id=chat_id, user_jwt_data=user_jwt_data))
