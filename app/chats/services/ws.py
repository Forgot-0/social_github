import asyncio
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import orjson
from redis.asyncio import Redis

from app.chats.dtos.websocket import WSConnection



@dataclass
class ChatConnectionManager:
    redis: Redis
    gateway_id: str = field(default_factory=lambda: os.getenv("HOSTNAME", "local-gateway"))

    connections_by_id: dict[str, WSConnection] = field(default_factory=dict)
    connections_by_user: dict[int, set[str]] = field(default_factory=lambda: defaultdict(set))
    subscriptions_by_chat: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    async def register(self, conn: WSConnection) -> None:
        self.connections_by_id[conn.connection_id] = conn
        self.connections_by_user[conn.user_id].add(conn.connection_id)

        await self.redis.sadd(
            f"ws:route:user:{conn.user_id}",
            f"{self.gateway_id}:{conn.connection_id}",
        ) # type: ignore
        await self.redis.setex(
            f"ws:conn:{conn.connection_id}",
            60,
            orjson.dumps({
                "user_id": conn.user_id,
                "gateway_id": self.gateway_id,
                "device_id": conn.device_id,
            }),
        )

        await conn.start_writer()

    async def unregister(self, conn: WSConnection) -> None:
        self.connections_by_id.pop(conn.connection_id, None)
        self.connections_by_user[conn.user_id].discard(conn.connection_id)

        for chat_id in list(conn.subscriptions):
            await self.unsubscribe_chat(conn, chat_id)

        await self.redis.srem(
            f"ws:route:user:{conn.user_id}",
            f"{self.gateway_id}:{conn.connection_id}",
        ) # type: ignore
        await self.redis.delete(f"ws:conn:{conn.connection_id}")

        await conn.close()

    async def subscribe_chat(self, conn: WSConnection, chat_id: str) -> None:
        conn.subscriptions.add(chat_id)
        self.subscriptions_by_chat[chat_id].add(conn.connection_id)

    async def unsubscribe_chat(self, conn: WSConnection, chat_id: str) -> None:
        conn.subscriptions.discard(chat_id)
        self.subscriptions_by_chat[chat_id].discard(conn.connection_id)

        if not self.subscriptions_by_chat[chat_id]:
            self.subscriptions_by_chat.pop(chat_id, None)

    async def send_to_user_local(self, user_id: int, event: dict[str, Any]) -> None:
        conn_ids = tuple(self.connections_by_user.get(user_id, ()))

        for conn_id in conn_ids:
            conn = self.connections_by_id.get(conn_id)
            if conn is None:
                continue

            ok = conn.try_send(event)
            if not ok:
                await conn.close(code=1013, reason="slow consumer")

    async def send_to_chat_local(self, chat_id: str, event: dict[str, Any]) -> None:
        conn_ids = tuple(self.subscriptions_by_chat.get(chat_id, ()))

        for conn_id in conn_ids:
            conn = self.connections_by_id.get(conn_id)
            if conn is None:
                continue

            ok = conn.try_send(event)
            if not ok:
                await conn.close(code=1013, reason="slow consumer")
