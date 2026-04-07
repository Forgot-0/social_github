from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.projects.dtos.members import MemberDTO
from app.projects.queries.profiles.get_my_invites import GetProfileInvitesQuery

router = APIRouter(route_class=DishkaRoute)


@router.get(
    "/invites/my",
    summary="Get invites in project",
    status_code=status.HTTP_200_OK
)
async def get_project_roles(
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData
) -> PageResult[MemberDTO]:
    return await mediator.handle_query(
        GetProfileInvitesQuery(
            user_jwt_data=user_jwt_data
        )
    )
