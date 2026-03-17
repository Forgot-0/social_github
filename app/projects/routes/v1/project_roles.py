from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.projects.dtos.roles import ProjectRoleDTO
from app.projects.queries.roles.get_list import GetProjectRolesQuery
from app.projects.schemas.roles.requests import GetProjectRolesRequest


router = APIRouter(route_class=DishkaRoute)


@router.get(
    "/",
    summary="Get project roles",
    description="Get project roles",
    status_code=status.HTTP_200_OK
)
async def get_project_roles(
    mediator: FromDishka[BaseMediator],
    role_filter: GetProjectRolesRequest = Query(...)
) -> PageResult[ProjectRoleDTO]:
    return await mediator.handle_query(
        GetProjectRolesQuery(
            filter=role_filter.to_roles_filter()
        )
    )
