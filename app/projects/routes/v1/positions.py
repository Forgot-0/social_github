from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from app.core.api.schemas import ORJSONResponse
from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.projects.commands.positions.create import CreatePositionCommand
from app.projects.commands.positions.update import UpdatePositionCommand
from app.projects.commands.positions.delete import DeletePositionCommand
from app.projects.dtos.positions import PositionDTO
from app.projects.queries.positions.get_by_id import GetPositionByIdQuery
from app.projects.queries.positions.get_list import GetProjectPositionsQuery
from app.projects.schemas.positions.requests import PositionCreateRequest, PositionUpdateRequest
from app.projects.filters.projects import ProjectFilter


router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/projects/{project_id}/positions",
    status_code=status.HTTP_201_CREATED,
)
async def create_position(
    project_id: int,
    request: PositionCreateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
)  -> None:
    required_skills = request.required_skills or set()

    await mediator.handle_command(
        CreatePositionCommand(
            project_id=project_id,
            title=request.title,
            description=request.description,
            required_skills=required_skills,
            responsibilities=request.responsibilities,
            location_type=request.location_type,
            expected_load=request.expected_load,
            user_jwt_data=user_jwt_data,
        )
    )


@router.get(
    "/projects/{project_id}/positions",
    status_code=status.HTTP_200_OK,
)
async def list_positions(
    project_id: int,
    mediator: FromDishka[BaseMediator],
) -> PageResult[PositionDTO]:
    # Пока используем ProjectFilter только для пагинации/сортировки
    filter_ = ProjectFilter()
    return await mediator.handle_query(
        GetProjectPositionsQuery(
            project_id=project_id,
            filter=filter_,
        )
    )


@router.get(
    "/positions/{position_id}",
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
    "/positions/{position_id}",
    status_code=status.HTTP_200_OK,
)
async def update_position(
    position_id: UUID,
    request: PositionUpdateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ORJSONResponse:
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
    return ORJSONResponse("OK")


@router.delete(
    "/positions/{position_id}",
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


