from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.core.api.builder import create_response
from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.projects.commands.positions.create import CreatePositionCommand
from app.projects.dtos.projects import ProjectDTO
from app.projects.exceptions import NotFoundProjectException
from app.projects.queries.projects.get_by_id import GetProjectByIdQuery
from app.projects.queries.projects.get_list import GetProjectsQuery
from app.projects.queries.projects.get_my import GetMyProjectsQuery
from app.projects.schemas.positions.requests import PositionCreateRequest
from app.projects.schemas.projects.requests import (
    GetMyProjectsRequest,
    GetProjectsRequest,
    InviteMemberRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
)
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
    project_request: ProjectCreateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        CreateProjectCommand(
            owner_id=int(user_jwt_data.id),
            name=project_request.name,
            slug=project_request.slug,
            small_description=project_request.small_description,
            description=project_request.description,
            visibility=project_request.visibility,
            meta_data=project_request.meta_data,
            tags=project_request.tags or set(),
        )
    )

@router.get(
    "/",
    status_code=status.HTTP_200_OK
)
async def get_projects(
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
    project_filter: GetProjectsRequest = Query(...),
) -> PageResult[ProjectDTO]:
    return await mediator.handle_query(
        GetProjectsQuery(
            filter=project_filter.to_projects_filter(),
            user_jwt_data=user_jwt_data
        )
    )

@router.get(
    "/my",
    status_code=status.HTTP_200_OK
)
async def get_my_projects(
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
    request: GetMyProjectsRequest = Query(...),
) -> PageResult[ProjectDTO]:
    return await mediator.handle_query(
        GetMyProjectsQuery(
            user_jwt_data=user_jwt_data,
            page=request.page,
            page_size=request.page_size,
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
    invite_request: InviteMemberRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        InviteMemberCommand(
            user_jwt_data=user_jwt_data,
            project_id=project_id,
            user_id=invite_request.user_id,
            role_id=invite_request.role_id,
            permissions_overrides=invite_request.permissions_overrides,
        )
    )


@router.post("/{project_id}/members/accept", status_code=status.HTTP_200_OK)
async def accept_invite(
    project_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        AcceptInviteCommand(
            user_jwt_data=user_jwt_data,
            project_id=project_id,
        )
    )


@router.put("/{project_id}/members/{user_id}/permissions", status_code=status.HTTP_200_OK)
async def update_member_permissions(
    project_id: int,
    user_id: int,
    member_request: MemberUpdatePermissionsRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        UpdateMemberPermissionsCommand(
            user_jwt_data=user_jwt_data,
            project_id=project_id,
            target_user_id=user_id,
            permissions_overrides=member_request.permissions_overrides,
        )
    )


@router.post(
    "/{project_id}/positions",
    status_code=status.HTTP_201_CREATED,
)
async def create_position(
    project_id: int,
    position_request: PositionCreateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
)  -> None:
    required_skills = position_request.required_skills or set()

    await mediator.handle_command(
        CreatePositionCommand(
            project_id=project_id,
            title=position_request.title,
            description=position_request.description,
            required_skills=required_skills,
            responsibilities=position_request.responsibilities,
            location_type=position_request.location_type,
            expected_load=position_request.expected_load,
            user_jwt_data=user_jwt_data,
        )
    )
