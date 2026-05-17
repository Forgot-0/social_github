import asyncio
from collections.abc import Iterable
from typing import overload

from app.chats.config import chat_config
from app.chats.dtos.attachments import AttachmentDTO
from app.chats.dtos.messages import MessageDTO
from app.core.services.storage.service import StorageService


@overload
async def attach_download_urls(
    messages: MessageDTO,
    storage_service: StorageService,
) -> MessageDTO:
    ...


@overload
async def attach_download_urls(
    messages: Iterable[MessageDTO],
    storage_service: StorageService,
) -> list[MessageDTO]:
    ...


async def attach_download_urls(
    messages: MessageDTO | Iterable[MessageDTO],
    storage_service: StorageService,
) -> MessageDTO | list[MessageDTO]:
    message_list = [messages] if isinstance(messages, MessageDTO) else list(messages)

    attachments_by_key: dict[str, list[AttachmentDTO]] = {}
    for message in message_list:
        for attachment in message.attachments:
            attachments_by_key.setdefault(attachment.s3_key, []).append(attachment)

    if not attachments_by_key:
        return message_list[0] if isinstance(messages, MessageDTO) else message_list

    keys = tuple(attachments_by_key)
    urls = await asyncio.gather(
        *(
            storage_service.generate_presigned_url(
                bucket_name=chat_config.ATTACHMENT_BUCKET,
                file_key=s3_key,
                expires=chat_config.DOWNLOAD_URL_TTL,
            )
            for s3_key in keys
        )
    )

    for s3_key, url in zip(keys, urls, strict=True):
        for attachment in attachments_by_key[s3_key]:
            attachment.url = url
            attachment.url_expires_in = chat_config.DOWNLOAD_URL_TTL

    return message_list[0] if isinstance(messages, MessageDTO) else message_list
