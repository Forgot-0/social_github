from pydantic import BaseModel, Field

from app.core.api.filter_mapper import FilterMapper
from app.core.filters.pagination import Pagination
from app.projects.filters.projects import ProjectFilter


class ProjectCreateRequest(BaseModel):
    name: str
    slug: str
    small_description: str | None = None
    description: str | None = None
    visibility: str | None = None
    meta_data: dict | None = None
    tags: set[str] | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None
    meta_data: dict | None = None
    tags: set[str] | None = None


class InviteMemberRequest(BaseModel):
    user_id: int
    role_id: int
    permissions_overrides: dict | None = None



class GetProjectsRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    tags: list[str] | None = None

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    sort: str | None = Field(default=None, examples=["created_at:desc,username:asc"])

    def to_projects_filter(self) -> ProjectFilter:
        projeect_filter = ProjectFilter(
            name=self.name,
            slug=self.slug,
            tags=self.tags,
        )

        pagination = Pagination(page=self.page, page_size=self.page_size)
        projeect_filter.set_pagination(pagination)

        sort_fields = FilterMapper.parse_sort_string(self.sort)
        for sort_field in sort_fields:
            projeect_filter.add_sort(sort_field.field, sort_field.direction)

        return projeect_filter
