from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from app.core.mediators.base import BaseMediator
from app.rooms.dtos.rooms import RoleDTO
from app.rooms.queries.roles.get_list import GetRolesQuery

router = APIRouter(route_class=DishkaRoute)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List all available roles",
)
async def list_roles(
    mediator: FromDishka[BaseMediator],
) -> list[RoleDTO]:
    return await mediator.handle_query(GetRolesQuery())
