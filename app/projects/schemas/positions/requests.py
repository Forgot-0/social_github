from pydantic import BaseModel, Field

from app.core.api.filter_mapper import FilterMapper
from app.core.filters.pagination import Pagination
from app.projects.filters.positions import PositionFilter
from app.projects.models.position import PositionLoad, PositionLocationType


class PositionCreateRequest(BaseModel):
    title: str
    description: str
    responsibilities: str | None = None

    required_skills: set[str] | None = None

    location_type: str | None = None
    expected_load: str | None = None


class PositionUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    responsibilities: str | None = None

    required_skills: set[str] | None = None

    location_type: str | None = None
    expected_load: str | None = None


class GetPositionsRequest(BaseModel):
    project_id: int | None = None
    title: str | None = None
    required_skills: set[str] | None = None
    is_open: bool = True
    location_type: PositionLocationType = PositionLocationType.remote
    expected_load: PositionLoad = PositionLoad.low

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    sort: str | None = Field(default=None, examples=["created_at:desc,username:asc"])

    def to_position_filter(self) -> PositionFilter:
        position_filter = PositionFilter(
            project_id=self.project_id,
            title=self.title,
            required_skills=self.required_skills,
            is_open=self.is_open,
            location_type=self.location_type,
            expected_load=self.expected_load
        )

        pagination = Pagination(page=self.page, page_size=self.page_size)
        position_filter.set_pagination(pagination)

        sort_fields = FilterMapper.parse_sort_string(self.sort)
        for sort_field in sort_fields:
            position_filter.add_sort(sort_field.field, sort_field.direction)

        return position_filter
