from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.projects.commands.applications.decision import DecideApplicationCommand


router = APIRouter(route_class=DishkaRoute)

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

