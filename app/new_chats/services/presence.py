from dataclasses import dataclass

from redis.asyncio import Redis

from app.chats.config import chat_config
from app.chats.keys import ChatKeys
from app.core.utils import now_utc

PRESENCE_TTL = chat_config.WS_HEARTBEAT_INTERVAL * 3


@dataclass
class PresenceService:
    redis: Redis

    def _is_fresh_score(self, score: float | None, now_ts: float) -> bool:
        if score is None:
            return False
        return (now_ts - score) <= PRESENCE_TTL

    async def set_online(self, user_id: int) -> None:
        ts = now_utc().timestamp()
        await self.redis.zadd(ChatKeys.presence_last_seen_zset(), {str(user_id): ts})

    async def set_offline(self, user_id: int) -> None:
        await self.redis.zrem(ChatKeys.presence_last_seen_zset(), str(user_id))

    async def refresh(self, user_id: int) -> None:
        await self.set_online(user_id)

    async def is_online(self, user_id: int) -> bool:
        score = await self.redis.zscore(ChatKeys.presence_last_seen_zset(), str(user_id))
        return self._is_fresh_score(score, now_utc().timestamp())

    async def get_online_status(self, user_ids: list[int]) -> dict[int, bool]:
        if not user_ids:
            return {}
        now_ts = now_utc().timestamp()
        members = [str(uid) for uid in user_ids]
        scores = await self.redis.zmscore(ChatKeys.presence_last_seen_zset(), members)
        return {
            uid: self._is_fresh_score(score, now_ts)
            for uid, score in zip(user_ids, scores, strict=False)
        }
