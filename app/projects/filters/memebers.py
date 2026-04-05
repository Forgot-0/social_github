
from dataclasses import dataclass

from app.core.filters.base import BaseFilter
from app.core.filters.condition import FilterOperator
from app.core.filters.loading_strategy import LoadingStrategyType
from app.projects.models.member import MembershipStatus


@dataclass
class MemebrFilter(BaseFilter):
    member_id: int | None = None
    invited_by: int | None = None
    status: MembershipStatus = MembershipStatus.active
    project_id: int | None = None

    def __post_init__(self):
        self._build_conditions()

    def _build_conditions(self) -> None:
        self.add_condition("user_id", FilterOperator.EQ, self.member_id)
        self.add_condition("invited_by", FilterOperator.EQ, self.invited_by)
        self.add_condition("project_id", FilterOperator.EQ, self.project_id)

        self.add_condition("status", FilterOperator.EQ, self.status.value)
        self.add_relation("role")
        self.add_relation("project")
