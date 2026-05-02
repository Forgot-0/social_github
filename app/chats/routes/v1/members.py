from __future__ import annotations

from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, status

from app.chats.commands.chats.add_member import AddMemberCommand, AddMemberCommandHandler
from app.chats.commands.chats.ban_member import BanMemberCommand, BanMemberCommandHandler
from app.chats.commands.chats.change_role import ChangeMemberRoleCommand, ChangeMemberRoleCommandHandler
from app.chats.commands.chats.kick import KickMemberCommand, KickMemberCommandHandler
from app.chats.dtos.members import ListMembers
from app.chats.queries.chats.get_members import GetChatMembersQuery, GetChatMembersQueryHandler
from app.chats.schemas.rest import (
    AddMemberRequest, BanMemberRequest, BulkResult, ChangeMemberRoleRequest
)
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter()


@router.get("", response_model=ListMembers)
@inject
async def list_chat_members(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[GetChatMembersQueryHandler],
    limit: int = Query(default=100, ge=1, le=500),
    cursor_user_id: int | None = Query(default=None, ge=1),
    include_presence: bool = Query(default=False),
) -> ListMembers:
    return await handler.handle(
        GetChatMembersQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            limit=limit,
            cursor_user_id=cursor_user_id,
            include_presence=include_presence,
        )
    )


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def add_member(
    chat_id: UUID,
    payload: AddMemberRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[AddMemberCommandHandler],
) -> None:
    await handler.handle(
        AddMemberCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=payload.user_id,
            role_id=payload.role_id,
        )
    )


@router.patch("/{user_id}/role", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def change_member_role(
    chat_id: UUID,
    user_id: int,
    payload: ChangeMemberRoleRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[ChangeMemberRoleCommandHandler],
) -> None:
    await handler.handle(
        ChangeMemberRoleCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
            role_id=payload.role_id,
        )
    )


@router.patch("/{user_id}/ban", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def ban_member(
    chat_id: UUID,
    user_id: int,
    payload: BanMemberRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[BanMemberCommandHandler],
) -> None:
    await handler.handle(
        BanMemberCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
            ban=payload.ban,
        )
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def kick_member(
    chat_id: UUID,
    user_id: int,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[KickMemberCommandHandler],
) -> None:
    await handler.handle(
        KickMemberCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
        )
    )
