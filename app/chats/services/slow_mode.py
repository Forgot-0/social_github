from dataclasses import dataclass, field

from redis.asyncio import Redis

from app.chats.exceptions import SlowModeLimitException
from app.chats.models.chat import Chat
from app.chats.models.chat_members import ChatMember
from app.chats.services.access import ChatAccessService


SCRIPT_SLOW_MODE = """
local key = KEYS[1]
local ttl = tonumber(ARGV[1])
local result = redis.call('SET', key, '1', 'EX', ttl, 'NX')
if result then
    return {1, ttl}
else
    return {0, redis.call('TTL', key)}
end
"""

@dataclass
class SlowModeService:
    redis: Redis
    access_service: ChatAccessService

    async def is_slow(self, chat: Chat, user_id: int, member: ChatMember | None) -> None:
        if chat.slow_mode_seconds <= 0 or self.access_service.can_bypass_slow_mode(member):
            return

        key = f"chat:slowmode:{chat.id}:{user_id}"
        script = self.redis.register_script(SCRIPT_SLOW_MODE)
        allowed, ttl = await script(keys=[key], args=[chat.slow_mode_seconds])

        if allowed:
            return
        raise SlowModeLimitException(chat_id=str(chat.id), retry_after=max(1, int(ttl)))
