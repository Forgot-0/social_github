from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.utils import now_utc

_DELIVERY_KEY_TTL = 7 * 24 * 3600


@dataclass
class DeliveryTrackingService:
    redis: Redis

    def _key(self, chat_id: int, user_id: int) -> str:
        return f"delivered:{chat_id}:{user_id}"

    async def mark_delivered(
        self, chat_id: int, user_id: int, message_id: int
    ) -> None:
        key = self._key(chat_id, user_id)
        ts = now_utc().timestamp()

        await self.redis.zadd(key, {str(message_id): ts})
        await self.redis.expire(key, _DELIVERY_KEY_TTL)

    async def mark_delivered_bulk(
        self,
        chat_id: int,
        user_id: int,
        message_ids: list[int],
    ) -> None:
        if not message_ids:
            return

        key = self._key(chat_id, user_id)
        ts = now_utc().timestamp()
        mapping = {str(mid): ts for mid in message_ids}

        await self.redis.zadd(key, mapping)
        await self.redis.expire(key, _DELIVERY_KEY_TTL)

    async def is_delivered(
        self, chat_id: int, user_id: int, message_id: int
    ) -> bool:
        key = self._key(chat_id, user_id)
        score = await self.redis.zscore(key, str(message_id))
        return score is not None

    async def get_delivered_ids(
        self, chat_id: int, user_id: int, min_id: int = 0
    ) -> list[int]:
        key = self._key(chat_id, user_id)
        members = await self.redis.zrangebyscore(key, min_id, "+inf")
        return [int(m) for m in members]

    async def get_delivery_status_for_message(
        self,
        chat_id: int,
        user_ids: list[int],
        message_id: int,
    ) -> dict[int, bool]:
        if not user_ids:
            return {}

        pipe = self.redis.pipeline()
        for uid in user_ids:
            pipe.zscore(self._key(chat_id, uid), str(message_id))

        results = await pipe.execute()
        return {uid: (score is not None) for uid, score in zip(user_ids, results, strict=False)}
