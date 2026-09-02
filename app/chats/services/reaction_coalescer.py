import asyncio
import json
import logging
import time
from dataclasses import dataclass

from redis.asyncio import Redis

from app.chats.config import chat_config
from app.chats.metrics import CHAT_REACTION_COALESCE_COLLAPSED
from app.chats.schemas.ws import ChatEventPayload

logger = logging.getLogger(__name__)

_PENDING_HASH = "reactions:coalesce:pending"
_DUE_ZSET = "reactions:coalesce:due"

# Atomically pop every field whose deadline has passed together with its latest
# snapshot. Redis is single-threaded so an ``enqueue`` (HSET + ZADD) can never
# interleave with this — no lost updates.
_CLAIM_DUE_LUA = """
local due = redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', ARGV[1], 'LIMIT', 0, tonumber(ARGV[2]))
local out = {}
for _, field in ipairs(due) do
    local snapshot = redis.call('HGET', KEYS[2], field)
    redis.call('ZREM', KEYS[1], field)
    redis.call('HDEL', KEYS[2], field)
    if snapshot then
        out[#out + 1] = snapshot
    end
end
return out
"""


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class ReactionCoalesceQueue:
    """Redis-backed debounce buffer for reaction fan-out. A viral message that
    receives hundreds of reactions a second produces at most one fan-out per
    ``REACTIONS_COALESCE_WINDOW_MS`` — the snapshot is overwritten in place, so
    the fan-out always carries the final counts."""

    redis: Redis

    def _key(self, payload: dict) -> str:
        return f"{payload['chat_id']}:{payload['message_id']}"

    async def enqueue(self, payload: dict) -> None:
        field = self._key(payload)
        deadline = _now_ms() + chat_config.REACTIONS_COALESCE_WINDOW_MS
        pipe = self.redis.pipeline(transaction=True)
        pipe.hset(_PENDING_HASH, field, json.dumps(payload))
        pipe.zadd(_DUE_ZSET, {field: deadline}, nx=True)
        await pipe.execute()

    async def claim_due(self) -> list[dict]:
        raw = await self.redis.eval(
            _CLAIM_DUE_LUA,
            2,
            _DUE_ZSET,
            _PENDING_HASH,
            str(_now_ms()),
            str(chat_config.REACTIONS_COALESCE_MAX_KEYS_PER_TICK),
        )
        return [json.loads(item) for item in raw or []]


def reaction_ws_payload_from_event(event_payload: ChatEventPayload) -> dict:
    extra = dict(event_payload.model_extra or {})
    return {
        "chat_id": str(event_payload.chat_id),
        "message_id": str(event_payload.message_id),
        "actor_id": extra.get("actor_id", 0),
        "action": extra.get("action", "update"),
        "groups": extra.get("groups", []),
        "recent_by_emoji": extra.get("recent_by_emoji", {}),
    }


async def run_reaction_coalescer(container, queue: ReactionCoalesceQueue) -> None:
    """Long-lived flush loop. One instance per delivery worker — ``claim_due``
    hands each pending message to exactly one worker."""
    from app.chats.services.delivery_router import ChatDeliveryRouter

    tick = chat_config.REACTIONS_COALESCE_TICK_MS / 1000
    logger.info("Reaction coalescer started (tick=%.3fs)", tick)

    while True:
        try:
            snapshots = await queue.claim_due()
            if snapshots:
                CHAT_REACTION_COALESCE_COLLAPSED.observe(len(snapshots))
                async with container() as request_container:
                    router = await request_container.get(ChatDeliveryRouter)
                    for snapshot in snapshots:
                        try:
                            await router.route_reaction_snapshot(snapshot)
                        except Exception:
                            logger.exception(
                                "Failed to fan out coalesced reaction snapshot",
                                extra={"snapshot": snapshot},
                            )
        except asyncio.CancelledError:
            logger.info("Reaction coalescer stopping")
            raise
        except Exception:
            logger.exception("Reaction coalescer tick failed")

        await asyncio.sleep(tick)
