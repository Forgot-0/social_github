from dataclasses import dataclass

from app.core.filters.base import BaseFilter
from app.core.filters.condition import FilterOperator


@dataclass
class NotificationFilter(BaseFilter):
    user_id: int | None = None
    is_read: bool | None = None

    def __post_init__(self) -> None:
        self._build_conditions()

    def _build_conditions(self) -> None:
        self.add_condition("user_id", FilterOperator.EQ, self.user_id)
        self.add_condition("is_read", FilterOperator.EQ, self.is_read)
