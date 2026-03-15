from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from app.core.api.schemas import ORJSONResponse
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.projects.commands.applications.create import CreateApplicationCommand
from app.projects.commands.applications.decision import DecideApplicationCommand
from app.projects.schemas.applications.requests import ApplicationCreateRequest


router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/positions/{position_id}/apply",
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_position(
    position_id: UUID,
    request: ApplicationCreateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ORJSONResponse:
    await mediator.handle_command(
        CreateApplicationCommand(
            position_id=position_id,
            message=request.message,
            user_jwt_data=user_jwt_data,
        )
    )

    return ORJSONResponse("OK")


@router.post(
    "/applications/{application_id}/approve",
    status_code=status.HTTP_200_OK,
)
async def approve_application(
    application_id: UUID,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ORJSONResponse:
    await mediator.handle_command(
        DecideApplicationCommand(
            application_id=application_id,
            approve=True,
            user_jwt_data=user_jwt_data,
        )
    )
    return ORJSONResponse("OK")


@router.post(
    "/applications/{application_id}/reject",
    status_code=status.HTTP_200_OK,
)
async def reject_application(
    application_id: UUID,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ORJSONResponse:
    await mediator.handle_command(
        DecideApplicationCommand(
            application_id=application_id,
            approve=False,
            user_jwt_data=user_jwt_data,
        )
    )
    return ORJSONResponse("OK")

