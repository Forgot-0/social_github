from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import orjson

from app.core.services.cache.base import CacheServiceInterface


@dataclass(frozen=True)
class BaseQuery(ABC):
    ...


QT = TypeVar("QT", bound=BaseQuery)
QR = TypeVar("QR", bound=Any)


@dataclass(frozen=True)
class BaseQueryHandler(ABC, Generic[QT, QR]):

    @abstractmethod
    async def handle(self, query: QT) -> QR: ...
