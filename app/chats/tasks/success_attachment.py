from dataclasses import dataclass
import logging

from dishka.integrations.taskiq import FromDishka, inject
import magic

from app.chats.config import chat_config
from app.chats.exceptions import AttachmentValidationException, InvalidUploadTokenException
from app.chats.keys import ChatKeys
from app.chats.schemas.ws import AttachmentSuccessPayload, WSEventType
from app.chats.services.attachment_service import AttachmentService
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
        chat_id: int,
        user_id: int,
        upload_tokens: list[str],
        attachment_service: FromDishka[AttachmentService],
        storage_service: FromDishka[StorageService],
        connection_manager: FromDishka[BaseConnectionManager]
    ) -> None:
        claimed = await attachment_service.claim_tokens(
            user_id=user_id, chat_id=chat_id, tokens=upload_tokens
        )

        failed_tokens = []
        for cl in claimed:
            try:
                data = await storage_service.download_range(
                    bucket_name=chat_config.ATTACHMENT_BUCKET,
                    file_key=cl.s3_key,
                    offset=0, length=1024
                )
                mime_type = magic.from_buffer(data, mime=True)

                if mime_type != cl.mime_type:
                    logger.warning(f"MIME mismatch: {mime_type} vs {cl.mime_type}")
                    failed_tokens.append(cl.upload_token)
                    continue

                await attachment_service.mark_success(user_id=user_id, claimed=cl)
            except Exception as e:
                logger.exception(f"Processing failed for token {cl.upload_token}", exc_info=e)
                failed_tokens.append(cl.upload_token)
        
        try:
            successful_tokens = [t for t in upload_tokens if t not in failed_tokens]
            if successful_tokens:
                data = AttachmentSuccessPayload(
                    user_id=user_id, tokens=successful_tokens
                )
                await connection_manager.publish(
                    ChatKeys.user_channel(user_id), payload={
                        "type": WSEventType.ATTACHMENT_SUCCESS,
                        "payload": data.model_dump()
                    }
                )
            if failed_tokens:
                pass
        except Exception as e:
            logger.exception("Failed to notify user of upload results")

