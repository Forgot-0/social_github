from dataclasses import dataclass

from app.core.filters.base import BaseFilter
from app.core.filters.condition import FilterOperator
from app.core.filters.loading_strategy import LoadingStrategyType


@dataclass
class ProjectFilter(BaseFilter):
    name: str | None = None
    slug: str | None = None
    tags: list[str] | None = None

    def __post_init__(self):
        self._build_conditions()

    def _build_conditions(self) -> None:
        self.add_condition("name", FilterOperator.CONTAINS, self.name)

        self.add_condition("tags", FilterOperator.ALL, self.tags)
        self.add_condition("visibility", FilterOperator.EQ, "public")
        self.add_relation("memberships", LoadingStrategyType.SELECTIN, "role")

