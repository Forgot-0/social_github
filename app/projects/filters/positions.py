from dataclasses import dataclass

from app.core.filters.base import BaseFilter
from app.core.filters.condition import FilterOperator
from app.projects.models.position import PositionLoad, PositionLocationType


@dataclass
class PositionFilter(BaseFilter):
    project_id: int | None = None
    title: str | None = None

    required_skills: set[str] | None = None
    is_open: bool = True
    location_type: PositionLocationType | None = None
    expected_load: PositionLoad | None = None

    def __post_init__(self):
        self._build_conditions()

    def _build_conditions(self) -> None:
        self.add_condition("project_id", FilterOperator.EQ, self.project_id)
        self.add_condition("title", FilterOperator.CONTAINS, self.title)

        if self.required_skills:
            self.required_skills = {skill.lower() for skill in self.required_skills}

        self.add_condition("required_skills", FilterOperator.ALL, self.required_skills)
        self.add_condition("is_open", FilterOperator.EQ, self.is_open)
        if self.location_type:
            self.add_condition("location_type", FilterOperator.EQ, self.location_type.value)
        if self.expected_load:
            self.add_condition("expected_load", FilterOperator.EQ, self.expected_load.value)

