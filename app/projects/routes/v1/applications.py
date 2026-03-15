from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.projects.commands.applications.decision import DecideApplicationCommand
from app.projects.dtos.applications import ApplicationDTO
from app.projects.queries.applications.get_list import GetApplicationsQuery
from app.projects.schemas.applications.requests import GetApplicationsRequest


router = APIRouter(route_class=DishkaRoute)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def list_applications(
    mediator: FromDishka[BaseMediator],
    filters: GetApplicationsRequest = Query(...),
) -> PageResult[ApplicationDTO]:
    return await mediator.handle_query(
        GetApplicationsQuery(
            filter=filters.to_application_filter(),
        )
    )


@router.post(
    "/{application_id}/approve",
    status_code=status.HTTP_200_OK,
)
async def approve_application(
    application_id: UUID,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        DecideApplicationCommand(
            application_id=application_id,
            approve=True,
            user_jwt_data=user_jwt_data,
        )
    )


@router.post(
    "/{application_id}/reject",
    status_code=status.HTTP_200_OK,
)
async def reject_application(
    application_id: UUID,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        DecideApplicationCommand(
            application_id=application_id,
            approve=False,
            user_jwt_data=user_jwt_data,
        )
    )


