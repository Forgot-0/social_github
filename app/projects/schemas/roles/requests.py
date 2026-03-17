from pydantic import BaseModel, Field

from app.core.api.filter_mapper import FilterMapper
from app.core.filters.pagination import Pagination
from app.projects.filters.roles import ProjectRoleFilter


class RoleCreateRequest(BaseModel):
    name: str
    permissions: dict


class RoleUpdateRequest(BaseModel):
    permissions: dict


class GetProjectRolesRequest(BaseModel):
    name: str | None = None

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    sort: str | None = Field(default=None, examples=["created_at:desc,username:asc"])

    def to_roles_filter(self) -> ProjectRoleFilter:
        projeect_filter = ProjectRoleFilter(
            name=self.name,
        )

        pagination = Pagination(page=self.page, page_size=self.page_size)
        projeect_filter.set_pagination(pagination)

        sort_fields = FilterMapper.parse_sort_string(self.sort)
        for sort_field in sort_fields:
            projeect_filter.add_sort(sort_field.field, sort_field.direction)

        return projeect_filter
