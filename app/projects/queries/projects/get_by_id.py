from dataclasses import dataclass

from app.core.queries import BaseQuery, BaseQueryHandler
from app.projects.repositories.projects import ProjectRepository
from app.projects.dtos.projects import ProjectDTO
from app.projects.exceptions import NotFoundProjectException


@dataclass(frozen=True)
class GetProjectByIdQuery(BaseQuery):
    project_id: int


@dataclass(frozen=True)
class GetProjectByIdQueryHandler(BaseQueryHandler[GetProjectByIdQuery, ProjectDTO]):
    project_repository: ProjectRepository

    async def handle(self, query: GetProjectByIdQuery) -> ProjectDTO:
        project = await self.project_repository.get_by_id(query.project_id)
        if not project:
            raise NotFoundProjectException(project_id=query.project_id)

        data = project.to_dict()
        memberships = []
        for m in project.memberships:
            memberships.append({
                "id": m.id,
                "project_id": m.project_id,
                "user_id": m.user_id,
                "role_id": m.role_id,
                "status": getattr(m.status, "name", str(m.status)),
                "invited_by": m.invited_by,
                "joined_at": m.joined_at,
                "permissions": m.effective_permissions(),
            })
        data["memberships"] = memberships

        return ProjectDTO.model_validate(data)
