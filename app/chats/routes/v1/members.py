from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.chats.commands.chats.add_member import AddMemberCommand
from app.chats.commands.chats.ban_member import BanMemberCommand
from app.chats.commands.chats.change_role import ChangeMemberRoleCommand
from app.chats.commands.chats.kick import KickMemberCommand
from app.chats.dtos.members import ListMembers
from app.chats.queries.chats.get_members import GetChatMembersQuery
from app.chats.schemas.rest import AddMemberRequest, BanMemberRequest, ChangeMemberRoleRequest
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter(route_class=DishkaRoute)


@router.get("")
async def list_chat_members(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
    limit: Annotated[int, Query(default=100, ge=1, le=500)],
    cursor_user_id: Annotated[int | None, Query(default=None, ge=1)],
    include_presence: Annotated[bool, Query(default=False)],
) -> ListMembers:
    return await mediator.handle_query(
        GetChatMembersQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            limit=limit,
            cursor_user_id=cursor_user_id,
            include_presence=include_presence,
        )
    )

@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def add_member(
    chat_id: UUID,
    add_member_request: AddMemberRequest,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(
        AddMemberCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=add_member_request.user_id,
            role_id=add_member_request.role_id,
        )
    )


@router.patch("/{user_id}/role", status_code=status.HTTP_204_NO_CONTENT)
async def change_member_role(
    chat_id: UUID,
    user_id: int,
    change_role_request: ChangeMemberRoleRequest,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(
        ChangeMemberRoleCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
            role_id=change_role_request.role_id,
        )
    )


@router.patch("/{user_id}/ban", status_code=status.HTTP_204_NO_CONTENT)
async def ban_member(
    chat_id: UUID,
    user_id: int,
    ban_member_request: BanMemberRequest,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(
        BanMemberCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
            reason=ban_member_request.reason,
            bannet_to=ban_member_request.bannet_to
        )
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def kick_member(
    chat_id: UUID,
    user_id: int,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(
        KickMemberCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
        )
    )
