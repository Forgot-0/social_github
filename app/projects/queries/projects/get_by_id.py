from dataclasses import dataclass

from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.repositories.projects import ProjectRepository
from app.projects.dtos.projects import ProjectDTO
from app.projects.exceptions import NotFoundProjectException
from app.projects.services.permission_service import ProjectPermissionService


@dataclass(frozen=True)
class GetProjectByIdQuery(BaseQuery):
    project_id: int
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class GetProjectByIdQueryHandler(BaseQueryHandler[GetProjectByIdQuery, ProjectDTO]):
    project_repository: ProjectRepository
    project_permission_servise: ProjectPermissionService

    async def handle(self, query: GetProjectByIdQuery) -> ProjectDTO:
        project = await self.project_repository.get_by_id(query.project_id, with_member=True, with_positon=True)
        if not project:
            raise NotFoundProjectException(project_id=query.project_id)

        if not self.project_permission_servise.can_view(
            user_jwt_data=query.user_jwt_data,
            project=project
        ): raise

        return ProjectDTO.model_validate(project.to_dict())
