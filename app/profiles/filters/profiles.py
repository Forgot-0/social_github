from dataclasses import dataclass

from app.core.filters.base import BaseFilter
from app.core.filters.condition import FilterOperator


@dataclass
class ProfileFilter(BaseFilter):
    user_id: int | None = None
    display_name: str | None = None
    skills: list[str] | None = None

    def __post_init__(self):
        self._build_conditions()

    def _build_conditions(self) -> None:
        self.add_condition("user_id", FilterOperator.EQ, self.user_id)
        self.add_condition("display_name", FilterOperator.CONTAINS, self.display_name)

        self.add_condition("skills", FilterOperator.ALL, self.skills)

        self.add_relation("contacts")
