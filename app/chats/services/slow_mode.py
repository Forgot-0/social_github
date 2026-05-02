from dataclasses import dataclass

from redis.asyncio import Redis

from app.chats.exceptions import SlowModeLimitException
from app.chats.models.chat import Chat
from app.chats.models.chat_members import ChatMember
from app.chats.services.access import ChatAccessService


@dataclass
class SlowModeService:
    redis: Redis
    access_service: ChatAccessService


    async def is_slow(self, chat: Chat, user_id: int, member: ChatMember | None) -> None:
        if chat.slow_mode_seconds <= 0 or self.access_service.can_bypass_slow_mode(member):
            return

        key = f"chat:slowmode:{chat.id}:{user_id}"
        allowed = await self.redis.set(
            key,
            "1",
            ex=chat.slow_mode_seconds,
            nx=True,
        )
        if allowed:
            return

        ttl = await self.redis.ttl(key)
        retry_after = max(1, int(ttl if ttl and ttl > 0 else chat.slow_mode_seconds))
        raise SlowModeLimitException(chat_id=str(chat.id), retry_after=retry_after)

