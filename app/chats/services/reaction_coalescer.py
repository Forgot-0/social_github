import asyncio
import json
import logging
import time
from dataclasses import dataclass

from redis.asyncio import Redis

from app.chats.config import chat_config
from app.chats.keys import ReactionKeys
from app.chats.metrics import CHAT_REACTION_COALESCE_COLLAPSED
from app.chats.services.delivery_router import ChatDeliveryRouter

logger = logging.getLogger(__name__)



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
    redis: Redis

    def _key(self, payload: dict) -> str:
        return f"{payload['chat_id']}:{payload['message_id']}"

    async def enqueue(self, payload: dict) -> None:
        field = self._key(payload)
        deadline = _now_ms() + chat_config.REACTIONS_COALESCE_WINDOW_MS
        pipe = self.redis.pipeline(transaction=True)
        pipe.hset(ReactionKeys.reaction_coalesce_pending(), field, json.dumps(payload))
        pipe.zadd(ReactionKeys.reaction_coalesce_due(), {field: deadline}, nx=True)
        await pipe.execute()

    async def claim_due(self) -> list[dict]:
        raw = await self.redis.eval(
            _CLAIM_DUE_LUA,
            2,
            ReactionKeys.reaction_coalesce_due(),
            ReactionKeys.reaction_coalesce_pending(),
            str(_now_ms()),
            str(chat_config.REACTIONS_COALESCE_MAX_KEYS_PER_TICK),
        )
        return [json.loads(item) for item in raw or []]


async def run_reaction_coalescer(container, queue: ReactionCoalesceQueue) -> None:
    tick = chat_config.REACTIONS_COALESCE_TICK_MS / 1000

    while True:
        try:
            snapshots = await queue.claim_due()

            if snapshots:
                CHAT_REACTION_COALESCE_COLLAPSED.observe(len(snapshots))

                async with container() as request_container:
                    router: ChatDeliveryRouter = await request_container.get(ChatDeliveryRouter)
                    for snapshot in snapshots:
                        await router.route_reaction_snapshot(snapshot)

        except asyncio.CancelledError:
            logger.info("Reaction coalescer stopping")
            raise
        except Exception:
            logger.exception("Reaction coalescer tick failed")

        await asyncio.sleep(tick)
