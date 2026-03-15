from dataclasses import dataclass
from uuid import UUID

from app.core.filters.base import BaseFilter
from app.core.filters.condition import FilterOperator
from app.projects.models.application import ApplicationStatus
from app.projects.models.position import PositionLoad, PositionLocationType


@dataclass
class ApplicationFilter(BaseFilter):
    project_id: int | None = None
    position_id: UUID | None = None
    candidate_id: int | None = None

    status: ApplicationStatus = ApplicationStatus.pending

    def __post_init__(self):
        self._build_conditions()

    def _build_conditions(self) -> None:
        self.add_condition("project_id", FilterOperator.EQ, self.project_id)
        self.add_condition("position_id", FilterOperator.EQ, self.position_id)
        self.add_condition("candidate_id", FilterOperator.EQ, self.candidate_id)

        self.add_condition("status", FilterOperator.EQ, self.status.value)
