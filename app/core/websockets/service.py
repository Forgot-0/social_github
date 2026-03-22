import asyncio
from dataclasses import dataclass, field
import logging
from typing import Any

from fastapi import WebSocket
import orjson
from redis.asyncio import Redis

from app.core.utils import now_utc
from app.core.websockets.base import BaseConnectionManager


logger = logging.getLogger(__name__)


@dataclass
class ConnectionManager(BaseConnectionManager):
    redis: Redis
    lock_map: dict[str, asyncio.Lock] = field(default_factory=dict)

    async def _heartbeat_loop(self, client_id: str):
        while client_id in self.connections_map:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self.send_json_all(client_id, {"type": "ping", "ts": now_utc().isoformat()})
            except Exception as e:
                logger.warning(f"Heartbeat failed for {client_id}: {e}")
                break

    def _ensure_heartbeat(self, key: str) -> None:
        existing = self.heartbeat_tasks.get(key)

        if existing and not existing.done():
            return

        task = asyncio.create_task(
            self._heartbeat_loop(key), name=f"ws:heartbeat:{key}"
        )

        self.heartbeat_tasks[key] = task

    async def accept_connection(self, websocket: WebSocket, key: str, subprotocol: str | None=None) -> None:
        await websocket.accept(subprotocol=subprotocol)

        if key not in self.lock_map:
            self.lock_map[key] = asyncio.Lock()

        async with self.lock_map[key]:
            self.connections_map[key].add(websocket)

        self._ensure_heartbeat(key)

    async def remove_connection(self, websocket: WebSocket, key: str) -> None:
        async with self.lock_map[key]:
            self.connections_map[key].discard(websocket)
            if not self.connections_map[key]:
                del self.connections_map[key]
                del self.lock_map[key]
                task_heartbeat = self.heartbeat_tasks.get(key)
                if task_heartbeat is not None:
                    task_heartbeat.cancel()
                    del self.heartbeat_tasks[key]

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
        pipe = self.redis.pipeline(transaction=False)
        for key in keys:
            pipe.publish(f"ws:{key}", orjson.dumps(payload))
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
        if self.redis:
            await self.redis.aclose()

        logger.info("ConnectionManager stopped")
