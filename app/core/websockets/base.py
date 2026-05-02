from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol


class ConnectionLike(Protocol):
    connection_id: str
    user_id: int
    subscriptions: set[str]


class BaseConnectionManager(ABC):
    @abstractmethod
    async def startup(self) -> None:
        ...

    @abstractmethod
    async def register(self, conn: ConnectionLike) -> None:
        ...

    @abstractmethod
    async def unregister(self, conn: ConnectionLike) -> None:
        ...

    @abstractmethod
    async def subscribe_chat(self, conn: ConnectionLike, chat_id: str) -> None:
        ...

    @abstractmethod
    async def unsubscribe_chat(self, conn: ConnectionLike, chat_id: str) -> None:
        ...

    @abstractmethod
    async def send_to_user_local(self, user_id: int, event: dict[str, Any]) -> None:
        ...

    @abstractmethod
    async def send_to_chat_local(self, chat_id: str, event: dict[str, Any]) -> None:
        ...

    @abstractmethod
    async def publish(self, channel: str, payload: dict[str, Any]) -> None:
        ...