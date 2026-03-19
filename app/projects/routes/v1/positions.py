from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.projects.commands.applications.create import CreateApplicationCommand
from app.projects.commands.positions.update import UpdatePositionCommand
from app.projects.commands.positions.delete import DeletePositionCommand
from app.projects.dtos.applications import ApplicationDTO
from app.projects.dtos.positions import PositionDTO
from app.projects.queries.applications.get_list import GetApplicationsQuery
from app.projects.queries.positions.get_by_id import GetPositionByIdQuery
from app.projects.queries.positions.get_list import GetProjectPositionsQuery
from app.projects.schemas.applications.requests import ApplicationCreateRequest, GetApplicationsRequest, GetPositionApplicationsRequest
from app.projects.schemas.positions.requests import GetPositionsRequest, PositionUpdateRequest


router = APIRouter(route_class=DishkaRoute)




@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def list_positions(
    mediator: FromDishka[BaseMediator],
    filters: GetPositionsRequest=Query(...),
) -> PageResult[PositionDTO]:
    return await mediator.handle_query(
        GetProjectPositionsQuery(
            filter=filters.to_position_filter(),
        )
    )


@router.get(
    "/{position_id}",
    status_code=status.HTTP_200_OK,
)
async def get_position(
    position_id: UUID,
    mediator: FromDishka[BaseMediator],
) -> PositionDTO:
    return await mediator.handle_query(
        GetPositionByIdQuery(
            position_id=position_id,
        )
    )


@router.put(
    "/{position_id}",
    status_code=status.HTTP_200_OK,
)
async def update_position(
    position_id: UUID,
    update_request: PositionUpdateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        UpdatePositionCommand(
            position_id=position_id,
            user_jwt_data=user_jwt_data,
            title=update_request.title,
            description=update_request.description,
            responsibilities=update_request.responsibilities,
            required_skills=update_request.required_skills,
            location_type=update_request.location_type,
            expected_load=update_request.expected_load,
        )
    )

@router.delete(
    "/{position_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_position(
    position_id: UUID,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        DeletePositionCommand(
            position_id=position_id,
            user_jwt_data=user_jwt_data,
        )
    )


@router.get(
    "/{position_id}/applications",
    status_code=status.HTTP_200_OK,
)
async def get_applications_position(
    position_id: UUID,
    mediator: FromDishka[BaseMediator],
    filters: GetPositionApplicationsRequest = Query(...),
) -> PageResult[ApplicationDTO]:
    return await mediator.handle_query(
        GetApplicationsQuery(
            filter=filters.to_application_filter(position_id),
        )
    )


@router.post(
    "/{position_id}/applications",
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_position(
    position_id: UUID,
    apply_request: ApplicationCreateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        CreateApplicationCommand(
            position_id=position_id,
            message=apply_request.message,
            user_jwt_data=user_jwt_data,
        )
    )
