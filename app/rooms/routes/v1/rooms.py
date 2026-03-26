from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from app.core.api.builder import create_response
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.rooms.commands.rooms.create import CreateRoomCommand
from app.rooms.commands.rooms.delete import DeleteRoomCommand
from app.rooms.commands.rooms.update import UpdateRoomCommand
from app.rooms.exceptions import InsufficientRoomPermissionException, RoomNotFoundException
from app.rooms.schemas.rooms.requests import CreateRoomRequest, UpdateRoomRequest
from app.rooms.schemas.rooms.response import CreateRoomResponse


router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a room"
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
            user_jwt_data=user_jwt_data
        )
    )
    return CreateRoomResponse(
        name=request.name,
        slug=slug,
        description=request.description,
        is_public=request.is_public,
    )

@router.delete(
    "/{room_slug}",
    summary="Delete a room (soft-delete)",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: create_response(AccessDeniedException(need_permissions={"room:delete",})),
        404: create_response(RoomNotFoundException(slug="zalupa"))
    }
)
async def delete_room(
    room_slug: str,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        DeleteRoomCommand(
            slug=room_slug,
            user_jwt_data=user_jwt_data
        )
    )

@router.put(
    "/{room_slug}",
    summary="Update room name / description / is_public",
    status_code=status.HTTP_200_OK,
    responses={
        403: create_response(InsufficientRoomPermissionException(required="manage_channels")),
        404: create_response(RoomNotFoundException(slug="zalupa"))
    }
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
            user_jwt_data=user_jwt_data
        )
    )

