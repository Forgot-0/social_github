import logging
from dataclasses import dataclass
from uuid import UUID

import magic
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.config import chat_config
from app.chats.keys import ChatKeys
from app.chats.models.attachment import AttachmentStatus
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.schemas.ws import AttachmentSuccessPayload, WSEventType
from app.chats.services.ws import ChatConnectionManager
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.storage.service import StorageService


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProccessAttachmentsCommand(BaseCommand):
    chat_id: str
    user_id: int
    upload_tokens: list[str]


@dataclass(frozen=True)
class ProccessAttachmentsCommandHandler(BaseCommandHandler[ProccessAttachmentsCommand, None]):
    attachment_repository: AttachmentRepository
    storage_service: StorageService
    connection_manager: ChatConnectionManager
    session: AsyncSession

    async def handle(self, command: ProccessAttachmentsCommand) -> None:
        slots = await self.attachment_repository.get_by_ids(
            [UUID(attachment_id) for attachment_id in command.upload_tokens]
        )

        failed_tokens: list[str] = []
        for slot in slots:
            try:
                data = await self.storage_service.download_range(
                    bucket_name=chat_config.ATTACHMENT_BUCKET,
                    file_key=slot.s3_key,
                    offset=0,
                    length=1024,
                )
                mime_type = magic.from_buffer(data, mime=True)

                if mime_type != slot.mime_type:
                    logger.error(
                        "MIME mismatch for attachment",
                        extra={
                            "slot_id": str(slot.id),
                            "declared": slot.mime_type,
                            "detected": mime_type,
                        },
                    )
                    slot.attachment_status = AttachmentStatus.ERROR
                    failed_tokens.append(str(slot.id))
                    continue

                slot.mark_proccesed()

            except Exception:
                logger.exception(
                    "Processing failed for attachment",
                    extra={"slot_id": str(slot.id)},
                )
                slot.attachment_status = AttachmentStatus.ERROR
                failed_tokens.append(str(slot.id))

        await self.session.commit()

        try:
            successful_tokens = [t for t in command.upload_tokens if t not in failed_tokens]
            if successful_tokens:
                payload = AttachmentSuccessPayload(
                    user_id=command.user_id,
                    chat_id=command.chat_id,
                    tokens=successful_tokens,
                )
                await self.connection_manager.publish(
                    ChatKeys.user_channel(command.user_id),
                    payload={
                        "type": WSEventType.ATTACHMENT_SUCCESS,
                        "payload": payload.model_dump(),
                    },
                )
            if failed_tokens:
                logger.warning(
                    "Attachment processing failed for some tokens",
                    extra={"user_id": command.user_id, "chat_id": command.chat_id, "failed": failed_tokens},
                )
        except Exception:
            logger.exception("Failed to notify user of upload results")

