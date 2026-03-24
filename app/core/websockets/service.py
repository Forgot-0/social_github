import asyncio
from dataclasses import dataclass, field
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState
import orjson
from redis.asyncio import Redis

from app.core.utils import now_utc
from app.core.websockets.base import BaseConnectionManager


logger = logging.getLogger(__name__)
_PUBLISH_BATCH_SIZE = 1000


@dataclass
class ConnectionManager(BaseConnectionManager):
    redis: Redis
    lock_map: dict[str, asyncio.Lock] = field(default_factory=dict)

    async def _heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            keys = tuple(self.connections_map.keys())
            if not keys:
                continue

            payload = {"type": "ping", "ts": now_utc().isoformat()}
            await asyncio.gather(
                *(self.send_json_all(key, payload) for key in keys),
                return_exceptions=True,
            )

    def _ensure_heartbeat(self) -> None:
        if self.heartbeat_task and not self.heartbeat_task.done():
            return

        self.heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(), name="ws:heartbeat:sweeper"
        )

    async def accept_connection(self, websocket: WebSocket, key: str, subprotocol: str | None=None) -> None:
        await websocket.accept(subprotocol=subprotocol)
        await self.bind_connection(websocket=websocket, key=key)

    async def bind_connection(self, websocket: WebSocket, key: str) -> None:
        if websocket.client_state == WebSocketState.DISCONNECTED:
            return

        if key not in self.lock_map:
            self.lock_map[key] = asyncio.Lock()

        async with self.lock_map[key]:
            self.connections_map[key].add(websocket)

        self._ensure_heartbeat()

    async def bind_key_connections(self, source_key: str, target_key: str) -> None:
        sockets = tuple(self.connections_map.get(source_key, ()))
        for websocket in sockets:
            await self.bind_connection(websocket, target_key)

    async def unbind_key_connections(self, source_key: str, target_key: str) -> None:
        sockets = tuple(self.connections_map.get(source_key, ()))
        for websocket in sockets:
            await self.remove_connection(websocket, target_key)

    async def remove_connection(self, websocket: WebSocket, key: str) -> None:
        lock = self.lock_map.get(key)
        if lock is None:
            return

        async with lock:
            self.connections_map[key].discard(websocket)
            if not self.connections_map[key]:
                del self.connections_map[key]
                del self.lock_map[key]

    async def send_all(self, key: str, bytes_: bytes) -> None:
        for websocket in self.connections_map[key]:
            try:
                await websocket.send_bytes(bytes_)
            except Exception:
                await self.remove_connection(websocket, key)

    async def send_json_all(self, key: str, data: dict[str, Any]) -> None:
        tasks = [
            websocket.send_json(data)
            for websocket in self.connections_map[key]
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def disconnect_all(self, key: str) -> None:
        async with self.lock_map[key]:
            for websocket in self.connections_map[key]:
                await websocket.send_json({
                    "message": "Abort connection",
                })
                await websocket.close()

    async def publish(self, key: str, payload: dict) -> None:
        if self.redis is None:
            raise RuntimeError("Manager not started")

        await self.redis.publish(
            f"ws:{key}",
            orjson.dumps(payload),
        )

    async def publish_bulk(self, keys: list[str], payload: dict) -> None:
        if not keys:
            return

        serialized_payload = orjson.dumps(payload)
        unique_keys = tuple(dict.fromkeys(keys))
        for idx in range(0, len(unique_keys), _PUBLISH_BATCH_SIZE):
            batch = unique_keys[idx:idx + _PUBLISH_BATCH_SIZE]
            pipe = self.redis.pipeline(transaction=False)
            for key in batch:
                pipe.publish(f"ws:{key}", serialized_payload)
            await pipe.execute()

    async def startup(self) -> None:
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe("ws:*")

        try:
            async for message in pubsub.listen():
                if message["type"] != "pmessage":
                    continue

                asyncio.create_task(self._dispatch(message))
        except:
            raise
        finally:
            await pubsub.unsubscribe()
            await self.redis.aclose()

    async def _dispatch(self, message: dict) -> None:
        channel = message["channel"].decode().removeprefix("ws:")
        try:
            payload = orjson.loads(message["data"])
            await self.send_json_all(channel, payload)
        except Exception:
            logger.exception("Dispatch error for channel %s", channel)

    async def shutdown(self) -> None:
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()

        if self.redis:
            await self.redis.aclose()

        logger.info("ConnectionManager stopped")
