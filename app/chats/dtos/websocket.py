import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import orjson
from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.core.utils import now_utc


@dataclass(slots=True)
class WSConnection:
    websocket: WebSocket
    user_id: int
    device_id: str
    gateway_id: str
    connection_id: str = field(default_factory=lambda: str(uuid4()))
    connected_at: datetime = field(default_factory=now_utc)
    last_seen_at: datetime = field(default_factory=now_utc)
    subscriptions: set[str] = field(default_factory=set)
    send_queue: asyncio.Queue[bytes] = field(default_factory=lambda: asyncio.Queue(maxsize=256))
    writer_task: asyncio.Task | None = None

    async def start_writer(self) -> None:
        self.writer_task = asyncio.create_task(
            self._writer_loop(),
            name=f"ws:writer:{self.connection_id}",
        )

    async def _writer_loop(self) -> None:
        while self.websocket.application_state == WebSocketState.CONNECTED:
            payload = await self.send_queue.get()
            await self.websocket.send_bytes(payload)

    def try_send(self, event: dict[str, Any]) -> bool:
        payload = orjson.dumps(event)

        try:
            self.send_queue.put_nowait(payload)
            return True
        except asyncio.QueueFull:
            return False

    async def close(self, code: int = 1000, reason: str = "") -> None:
        if self.writer_task and not self.writer_task.done():
            self.writer_task.cancel()

        if self.websocket.application_state == WebSocketState.CONNECTED:
            await self.websocket.close(code=code, reason=reason)
