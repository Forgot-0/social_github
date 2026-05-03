from dataclasses import dataclass
import logging
from uuid import UUID

from dishka.integrations.taskiq import FromDishka, inject
import magic
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.config import chat_config
from app.chats.keys import ChatKeys
from app.chats.models.attachment import AttachmentStatus
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.schemas.ws import AttachmentSuccessPayload, WSEventType
from app.core.services.queues.task import BaseTask
from app.core.services.storage.service import StorageService
from app.core.websockets.base import BaseConnectionManager


logger = logging.getLogger(__name__)


@dataclass
class AttachmentProccessTask(BaseTask):
    __task_name__ = "chats.attachment.proccess"

    @staticmethod
    @inject
    async def run(
        chat_id: str,
        user_id: int,
        upload_tokens: list[str],
        session: FromDishka[AsyncSession],
        attachment_repository: FromDishka[AttachmentRepository],
        storage_service: FromDishka[StorageService],
        connection_manager: FromDishka[BaseConnectionManager],
    ) -> None:
        slots = await attachment_repository.get_by_ids(
            [UUID(attachment_id) for attachment_id in upload_tokens]
        )

        failed_tokens: list[str] = []
        for slot in slots:
            try:
                data = await storage_service.download_range(
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

        await session.commit()

        try:
            successful_tokens = [t for t in upload_tokens if t not in failed_tokens]
            if successful_tokens:
                payload = AttachmentSuccessPayload(
                    user_id=user_id,
                    chat_id=chat_id,
                    tokens=successful_tokens,
                )
                await connection_manager.publish(
                    ChatKeys.user_channel(user_id),
                    payload={
                        "type": WSEventType.ATTACHMENT_SUCCESS,
                        "payload": payload.model_dump(),
                    },
                )
            if failed_tokens:
                logger.warning(
                    "Attachment processing failed for some tokens",
                    extra={"user_id": user_id, "chat_id": chat_id, "failed": failed_tokens},
                )
        except Exception:
            logger.exception("Failed to notify user of upload results")