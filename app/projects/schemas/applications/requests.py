from uuid import UUID

from pydantic import BaseModel, Field

from app.core.api.filter_mapper import FilterMapper
from app.core.filters.pagination import Pagination
from app.projects.filters.applications import ApplicationFilter
from app.projects.models.application import ApplicationStatus


class ApplicationCreateRequest(BaseModel):
    message: str | None = None


class ApplicationDecisionRequest(BaseModel):
    application_id: UUID


class GetApplicationsRequest(BaseModel):
    project_id: int | None = None
    position_id: UUID | None = None
    candidate_id: int | None = None

    status: ApplicationStatus = ApplicationStatus.pending

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    sort: str | None = Field(default=None, examples=["created_at:desc,username:asc"])

    def to_application_filter(self) -> ApplicationFilter:
        application_filter = ApplicationFilter(
            project_id=self.project_id,
            position_id=self.position_id,
            candidate_id=self.candidate_id,
            status=self.status
        )

        pagination = Pagination(page=self.page, page_size=self.page_size)
        application_filter.set_pagination(pagination)

        sort_fields = FilterMapper.parse_sort_string(self.sort)
        for sort_field in sort_fields:
            application_filter.add_sort(sort_field.field, sort_field.direction)

        return application_filter
