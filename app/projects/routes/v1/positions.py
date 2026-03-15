from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.projects.commands.applications.create import CreateApplicationCommand
from app.projects.commands.positions.update import UpdatePositionCommand
from app.projects.commands.positions.delete import DeletePositionCommand
from app.projects.dtos.positions import PositionDTO
from app.projects.queries.positions.get_by_id import GetPositionByIdQuery
from app.projects.queries.positions.get_list import GetProjectPositionsQuery
from app.projects.schemas.applications.requests import ApplicationCreateRequest
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
    request: PositionUpdateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        UpdatePositionCommand(
            position_id=position_id,
            user_jwt_data=user_jwt_data,
            title=request.title,
            description=request.description,
            responsibilities=request.responsibilities,
            required_skills=request.required_skills,
            location_type=request.location_type,
            expected_load=request.expected_load,
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

@router.post(
    "/{position_id}/apply",
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_position(
    position_id: UUID,
    request: ApplicationCreateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        CreateApplicationCommand(
            position_id=position_id,
            message=request.message,
            user_jwt_data=user_jwt_data,
        )
    )
