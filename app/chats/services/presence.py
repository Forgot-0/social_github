"""
Presence service — tracks online/offline status.

Strategy:
  • SET presence:user:{user_id} "1" EX 90   on WS connect / heartbeat
  • DEL presence:user:{user_id}              on WS disconnect
  • MGET presence:user:{uid} ...             for bulk lookup

TTL of 90 s means user appears offline within 1–2 missed heartbeat cycles
(WS_HEARTBEAT_INTERVAL = 30 s → 3 cycles).
"""

from dataclasses import dataclass

from redis.asyncio import Redis

from app.chats.config import chat_config
from app.chats.keys import ChatKeys


PRESENCE_TTL = chat_config.WS_HEARTBEAT_INTERVAL * 3


@dataclass
class PresenceService:
    redis: Redis

    async def set_online(self, user_id: int) -> None:
        await self.redis.setex(ChatKeys.user_online(user_id), PRESENCE_TTL, "1")

    async def set_offline(self, user_id: int) -> None:
        await self.redis.delete(ChatKeys.user_online(user_id))

    async def refresh(self, user_id: int) -> None:
        await self.redis.expire(ChatKeys.user_online(user_id), PRESENCE_TTL)

    async def is_online(self, user_id: int) -> bool:
        return bool(await self.redis.exists(ChatKeys.user_online(user_id)))

    async def get_online_status(self, user_ids: list[int]) -> dict[int, bool]:
        if not user_ids:
            return {}
        keys = [ChatKeys.user_online(uid) for uid in user_ids]
        values = await self.redis.mget(*keys)
        return {uid: (val is not None) for uid, val in zip(user_ids, values)}