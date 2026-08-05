from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis


_PROCESSED_KEY_TEMPLATE = "consumers:processed:{group}:{event_id}"


def extract_event_id(payload: dict[str, Any], headers: dict[str, Any] | None = None) -> str | None:
    event_id = payload.get("event_id")
    if event_id:
        return str(event_id)

    if headers:
        header_value = headers.get("eventId") or headers.get("event_id")
        if header_value is not None:
            if isinstance(header_value, bytes):
                return header_value.decode("utf-8", errors="replace")
            return str(header_value)

    return None


@dataclass(slots=True)
class EventIdempotencyGuard:
    redis: Redis
    ttl_seconds: int = 7 * 24 * 3600

    async def try_acquire(self, group: str, event_id: str) -> bool:
        key = _PROCESSED_KEY_TEMPLATE.format(group=group, event_id=event_id)
        acquired = await self.redis.set(key, "1", ex=self.ttl_seconds, nx=True)
        return bool(acquired)

    async def release(self, group: str, event_id: str) -> None:
        key = _PROCESSED_KEY_TEMPLATE.format(group=group, event_id=event_id)
        await self.redis.delete(key)
