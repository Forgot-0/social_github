from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import orjson
from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.chats.config import chat_config
from app.core.utils import now_utc


def _utc_ts() -> str:
    return now_utc().isoformat()


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
    last_seq_by_chat: dict[str, int] = field(default_factory=dict)
    send_queue: asyncio.Queue[bytes] = field(
        default_factory=lambda: asyncio.Queue(maxsize=chat_config.WS_SEND_QUEUE_SIZE)
    )
    writer_task: asyncio.Task[None] | None = None
    heartbeat_task: asyncio.Task[None] | None = None
    closed: bool = False

    async def start(self) -> None:
        await self.start_writer()
        await self.start_heartbeat()

    async def start_writer(self) -> None:
        if self.writer_task and not self.writer_task.done():
            return
        self.writer_task = asyncio.create_task(
            self._writer_loop(),
            name=f"ws:writer:{self.connection_id}",
        )

    async def start_heartbeat(self) -> None:
        if self.heartbeat_task and not self.heartbeat_task.done():
            return
        self.heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(),
            name=f"ws:heartbeat:{self.connection_id}",
        )

    async def _writer_loop(self) -> None:
        try:
            while self.websocket.application_state == WebSocketState.CONNECTED:
                payload = await self.send_queue.get()
                await self.websocket.send_text(payload.decode("utf-8"))
        except asyncio.CancelledError:
            raise
        except Exception:
            await self.close(code=1011, reason="writer failed")

    async def _heartbeat_loop(self) -> None:
        try:
            while self.websocket.application_state == WebSocketState.CONNECTED:
                await asyncio.sleep(chat_config.WS_HEARTBEAT_INTERVAL)
                idle_for = (now_utc() - self.last_seen_at).total_seconds()
                if idle_for > chat_config.WS_HEARTBEAT_TIMEOUT:
                    await self.close(code=1001, reason="heartbeat timeout")
                    return

                if not self.try_send({
                    "type": "ws.ping",
                    "connection_id": self.connection_id,
                    "ts": _utc_ts(),
                }):
                    await self.close(code=1013, reason="slow consumer")
                    return
        except asyncio.CancelledError:
            raise

    def touch(self) -> None:
        self.last_seen_at = now_utc()

    def try_send(self, event: dict[str, Any]) -> bool:
        if self.closed:
            return False

        payload = orjson.dumps(event)
        try:
            self.send_queue.put_nowait(payload)
            return True
        except asyncio.QueueFull:
            return False

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = True
        current_task = asyncio.current_task()

        for task in (self.writer_task, self.heartbeat_task):
            if task and task is not current_task and not task.done():
                task.cancel()

        if self.websocket.application_state == WebSocketState.CONNECTED:
            with contextlib.suppress(RuntimeError):
                await self.websocket.close(code=code, reason=reason[:120])

        for task in (self.writer_task, self.heartbeat_task):
            if task and task is not current_task:
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task
