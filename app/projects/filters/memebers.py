
from dataclasses import dataclass

from app.core.filters.base import BaseFilter


@dataclass
class MemebrFilter(BaseFilter):
    def __post_init__(self):
        self._build_conditions()

    def _build_conditions(self) -> None:
        ...
