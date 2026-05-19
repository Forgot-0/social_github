import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from typing import overload

from redis.asyncio import Redis

from app.chats.config import chat_config
from app.chats.dtos.attachments import AttachmentDTO
from app.chats.dtos.messages import MessageDTO
from app.chats.exceptions import SlowModeLimitException
from app.chats.models.chat import Chat
from app.chats.models.chat_members import ChatMember
from app.chats.services.access import ChatAccessService
from app.core.services.storage.service import StorageService


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
class MessageService:
    redis: Redis
    access_service: ChatAccessService
    storage_service: StorageService

    async def is_slow(self, chat: Chat, user_id: int, member: ChatMember | None) -> None:
        if chat.slow_mode_seconds <= 0 or self.access_service.can_bypass_slow_mode(member):
            return

        key = f"chat:slowmode:{chat.id}:{user_id}"
        script = self.redis.register_script(SCRIPT_SLOW_MODE)
        allowed, ttl = await script(keys=[key], args=[chat.slow_mode_seconds])

        if allowed:
            return
        raise SlowModeLimitException(chat_id=str(chat.id), retry_after=max(1, int(ttl)))

    @overload
    async def attach_download_urls(
        self, messages: MessageDTO,
    ) -> MessageDTO:
        ...

    @overload
    async def attach_download_urls(
        self, messages: Iterable[MessageDTO],
    ) -> list[MessageDTO]:
        ...

    async def attach_download_urls(self, messages: MessageDTO | Iterable[MessageDTO]) -> MessageDTO | list[MessageDTO]:
        message_list = [messages] if isinstance(messages, MessageDTO) else list(messages)

        attachments_by_key: dict[str, AttachmentDTO] = {}
        for message in message_list:
            for attachment in message.attachments:
                attachments_by_key[attachment.s3_key] = attachment

        if not attachments_by_key:
            return message_list[0] if isinstance(messages, MessageDTO) else message_list

        keys = tuple(attachments_by_key)
        urls = await asyncio.gather(
            *(
                self.get_attachmnent_url_by_key(s3_key=s3_key,)
                for s3_key in keys
            )
        )

        for s3_key, url in zip(keys, urls, strict=True):
            attachments_by_key[s3_key].url = url
            attachments_by_key[s3_key].url_expires_in = chat_config.DOWNLOAD_URL_TTL

        return message_list[0] if isinstance(messages, MessageDTO) else message_list


    async def get_attachmnent_url_by_key(self, s3_key: str) -> str:
        key = f"attachment:{s3_key}"
        url = await self.redis.get(key)
        if url is None:
            url = await self.storage_service.generate_presigned_url(
                bucket_name=chat_config.ATTACHMENT_BUCKET,
                file_key=s3_key,
                expires=chat_config.DOWNLOAD_URL_TTL,
            )
            await self.redis.set(key, url, ex=chat_config.DOWNLOAD_URL_TTL-30)

        return url

