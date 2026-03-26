from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from app.core.api.builder import create_response
from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.rooms.commands.rooms.add_member import AddMemberRoomCommand
from app.rooms.commands.rooms.ban import BanMemberCommand
from app.rooms.commands.rooms.create import CreateRoomCommand
from app.rooms.commands.rooms.delete import DeleteRoomCommand
from app.rooms.commands.rooms.join import JoinRoomCommand
from app.rooms.commands.rooms.kick import KickMemberCommand
from app.rooms.commands.rooms.leave import LeaveRoomCommand
from app.rooms.commands.rooms.mute import MuteMemberCommand
from app.rooms.commands.rooms.unban import UnbanMemberCommand
from app.rooms.commands.rooms.update import UpdateRoomCommand
from app.rooms.dtos.livekit import JoinTokenDTO, LiveKitParticipantsDTO
from app.rooms.dtos.rooms import RoomDetailDTO, RoomDTO
from app.rooms.exceptions import (
    CannotKickOwnerException,
    InsufficientRoomPermissionException,
    RoomNotFoundException,
    UserBannedException,
)
from app.rooms.filters.rooms import RoomFilter
from app.rooms.queries.participants.get_list_by_room import GetParticipantsQuery
from app.rooms.queries.rooms.get import GetRoomQuery
from app.rooms.queries.rooms.get_list import ListRoomsQuery
from app.rooms.schemas.rooms.requests import (
    AddMemberRequest,
    BanMemberRequest,
    CreateRoomRequest,
    MuteMemberRequest,
    UpdateRoomRequest,
)
from app.rooms.schemas.rooms.response import CreateRoomResponse


router = APIRouter(route_class=DishkaRoute)

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List rooms",
)
async def list_rooms(
    mediator: FromDishka[BaseMediator],
    name: str | None = None,
    is_public: bool | None = None,
    created_by: int | None = None,
) -> PageResult[RoomDTO]:
    filters = RoomFilter(name=name, is_public=is_public, created_by=created_by)
    result, *_ = await mediator.handle_query(ListRoomsQuery(filters=filters))
    return result


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a room",
)
async def create_room(
    request: CreateRoomRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> CreateRoomResponse:
    slug, *_ = await mediator.handle_command(
        CreateRoomCommand(
            name=request.name,
            description=request.description,
            is_public=request.is_public,
            user_jwt_data=user_jwt_data,
        )
    )
    return CreateRoomResponse(
        name=request.name,
        slug=slug,
        description=request.description,
        is_public=request.is_public,
    )

@router.get(
    "/{room_slug}",
    status_code=status.HTTP_200_OK,
    summary="Get room details",
    responses={
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def get_room(
    room_slug: str,
    mediator: FromDishka[BaseMediator],
) -> RoomDetailDTO:
    result, *_ = await mediator.handle_query(GetRoomQuery(slug=room_slug))
    return result


@router.put(
    "/{room_slug}",
    status_code=status.HTTP_200_OK,
    summary="Update room name / description / is_public",
    responses={
        403: create_response(InsufficientRoomPermissionException(required="manage_channels")),
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def update_room(
    room_slug: str,
    request: UpdateRoomRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        UpdateRoomCommand(
            slug=room_slug,
            name=request.name,
            description=request.description,
            is_public=request.is_public,
            user_jwt_data=user_jwt_data,
        )
    )


@router.delete(
    "/{room_slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a room (soft-delete)",
    responses={
        403: create_response(AccessDeniedException(need_permissions={"room:delete"})),
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def delete_room(
    room_slug: str,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        DeleteRoomCommand(slug=room_slug, user_jwt_data=user_jwt_data)
    )

@router.post(
    "/{room_slug}/join",
    status_code=status.HTTP_200_OK,
    summary="Join a room and get a LiveKit token",
    responses={
        403: create_response(UserBannedException(user_id=0, slug="example")),
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def join_room(
    room_slug: str,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> JoinTokenDTO:
    result, *_ = await mediator.handle_command(
        JoinRoomCommand(slug=room_slug, user_jwt_data=user_jwt_data)
    )
    return result


@router.post(
    "/{room_slug}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave a room",
    responses={
        403: create_response(CannotKickOwnerException()),
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def leave_room(
    room_slug: str,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        LeaveRoomCommand(slug=room_slug, user_jwt_data=user_jwt_data)
    )

@router.post(
    "/{room_slug}/members",
    status_code=status.HTTP_201_CREATED,
    summary="Add a member to the room",
    responses={
        403: create_response(InsufficientRoomPermissionException(required="manage_roles")),
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def add_member(
    room_slug: str,
    request: AddMemberRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        AddMemberRoomCommand(
            slug=room_slug,
            member_id=request.user_id,
            member_username=request.username,
            role_id=request.role_id,
            user_jwt_data=user_jwt_data,
        )
    )

@router.delete(
    "/{room_slug}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Kick a member from the room",
    responses={
        403: create_response(InsufficientRoomPermissionException(required="kick")),
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def kick_member(
    room_slug: str,
    user_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        KickMemberCommand(
            slug=room_slug,
            target_user_id=user_id,
            user_jwt_data=user_jwt_data,
        )
    )

@router.put(
    "/{room_slug}/members/{user_id}/mute",
    status_code=status.HTTP_200_OK,
    summary="Mute or unmute a member",
    responses={
        403: create_response(InsufficientRoomPermissionException(required="mute")),
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def mute_member(
    room_slug: str,
    user_id: int,
    request: MuteMemberRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        MuteMemberCommand(
            slug=room_slug,
            target_user_id=user_id,
            is_muted=request.is_muted,
            user_jwt_data=user_jwt_data,
        )
    )

@router.post(
    "/{room_slug}/members/{user_id}/ban",
    status_code=status.HTTP_201_CREATED,
    summary="Ban a member from the room",
    responses={
        403: create_response(InsufficientRoomPermissionException(required="ban")),
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def ban_member(
    room_slug: str,
    user_id: int,
    request: BanMemberRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        BanMemberCommand(
            slug=room_slug,
            target_user_id=user_id,
            reason=request.reason,
            user_jwt_data=user_jwt_data,
        )
    )

@router.delete(
    "/{room_slug}/members/{user_id}/ban",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unban a member from the room",
    responses={
        403: create_response(InsufficientRoomPermissionException(required="ban")),
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def unban_member(
    room_slug: str,
    user_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        UnbanMemberCommand(
            slug=room_slug,
            target_user_id=user_id,
            user_jwt_data=user_jwt_data,
        )
    )

@router.get(
    "/{room_slug}/participants",
    status_code=status.HTTP_200_OK,
    summary="List currently connected LiveKit participants",
    responses={
        404: create_response(RoomNotFoundException(slug="example")),
    },
)
async def get_participants(
    room_slug: str,
    mediator: FromDishka[BaseMediator],
) -> list[LiveKitParticipantsDTO]:
    return await mediator.handle_query(GetParticipantsQuery(slug=room_slug))
