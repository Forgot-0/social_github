from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from app.core.api.builder import create_response
from app.core.api.schemas import ORJSONResponse
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.projects.dtos.projects import ProjectDTO
from app.projects.exceptions import NotFoundProjectException
from app.projects.queries.projects.get_by_id import GetProjectByIdQuery
from app.projects.schemas.projects.requests import ProjectCreateRequest, ProjectUpdateRequest, InviteMemberRequest
from app.projects.schemas.members.requests import MemberUpdatePermissionsRequest
from app.projects.commands.projects.create import CreateProjectCommand
from app.projects.commands.projects.update import UpdateProjectCommand
from app.projects.commands.projects.invite import InviteMemberCommand
from app.projects.commands.members.accept import AcceptInviteCommand
from app.projects.commands.members.update_permissions import UpdateMemberPermissionsCommand


router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED
)
async def create_project(
    request: ProjectCreateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        CreateProjectCommand(
            owner_id=int(user_jwt_data.id),
            name=request.name,
            slug=request.slug,
            small_description=request.description,
            visibility=request.visibility,
            meta_data=request.meta_data,
            tags=request.tags or set(),
        )
    )

@router.get(
    "/{project_id}", status_code=status.HTTP_200_OK,
    responses={404: create_response(NotFoundProjectException(project_id=123))}
)
async def get_project(
    project_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ProjectDTO:
    return await mediator.handle_query(
        GetProjectByIdQuery(project_id=project_id, user_jwt_data=user_jwt_data)
    )


@router.put("/{project_id}", status_code=status.HTTP_200_OK)
async def update_project(
    project_id: int,
    request: ProjectUpdateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        UpdateProjectCommand(
            user_jwt_data=user_jwt_data,
            project_id=project_id,
            name=request.name,
            description=request.description,
            visibility=request.visibility,
            meta_data=request.meta_data,
            tags=request.tags,
        )
    )


@router.post("/{project_id}/invite", status_code=status.HTTP_200_OK)
async def invite_member(
    project_id: int,
    request: InviteMemberRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ORJSONResponse:
    await mediator.handle_command(
        InviteMemberCommand(
            user_jwt_data=user_jwt_data,
            project_id=project_id,
            user_id=request.user_id,
            role_id=request.role_id,
            permissions_overrides=request.permissions_overrides,
        )
    )
    return ORJSONResponse("OK")


@router.post("/{project_id}/members/accept", status_code=status.HTTP_200_OK)
async def accept_invite(
    project_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ORJSONResponse:
    await mediator.handle_command(
        AcceptInviteCommand(
            user_jwt_data=user_jwt_data,
            project_id=project_id,
        )
    )
    return ORJSONResponse("OK")


@router.put("/{project_id}/members/{user_id}/permissions", status_code=status.HTTP_200_OK)
async def update_member_permissions(
    project_id: int,
    user_id: int,
    request: MemberUpdatePermissionsRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ORJSONResponse:
    await mediator.handle_command(
        UpdateMemberPermissionsCommand(
            user_jwt_data=user_jwt_data,
            project_id=project_id,
            target_user_id=user_id,
            permissions_overrides=request.permissions_overrides,
        )
    )
    return ORJSONResponse("OK")

