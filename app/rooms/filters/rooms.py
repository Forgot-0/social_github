from dataclasses import dataclass

from app.core.filters.base import BaseFilter
from app.core.filters.condition import FilterOperator
from app.core.filters.loading_strategy import LoadingStrategyType


@dataclass
class RoomFilter(BaseFilter):
    name: str | None = None
    is_public: bool | None = None
    created_by: int | None = None

    def __post_init__(self) -> None:
        self._build_conditions()

    def _build_conditions(self) -> None:
        self.add_condition("name", FilterOperator.CONTAINS, self.name)
        self.add_condition("is_public", FilterOperator.EQ, self.is_public)
        self.add_condition("created_by", FilterOperator.EQ, self.created_by)
        self.add_condition("deleted_at", FilterOperator.IS_NULL, None)

        self.add_relation("members", LoadingStrategyType.SELECTIN, "role")
