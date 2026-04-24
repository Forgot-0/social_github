import re
from dataclasses import asdict, dataclass
from uuid import UUID, uuid4

import orjson
from redis.asyncio import Redis

from app.chats.config import chat_config
from app.chats.exceptions import (
    AttachmentLimitExceededException,
    AttachmentNotFoundException,
    AttachmentValidationException,
    InvalidUploadTokenException,
)
from app.chats.models.attachment import AttachmentStatus, AttachmentType
from app.core.services.storage.service import StorageService


@dataclass(frozen=True)
class UploadSlot:
    upload_token: str
    upload_url: str
    s3_key: str
    attachment_type: AttachmentType
    expires_in: int


@dataclass(frozen=True)
class UploadedAttachment:
    chat_id: int
    user_id: int
    s3_key: str
    upload_token: str
    mime_type: str
    file_size: int
    original_filename: str
    attachment_type: AttachmentType
    status: AttachmentStatus

@dataclass
class AttachmentService:
    redis: Redis
    storage_service: StorageService
    clean_filename = re.compile(r"[^\w.\-]")

    async def create_upload_slot(
        self,
        chat_id: int,
        user_id: int,
        filename: str,
        mime_type: str,
        file_size: int
    ) -> UploadSlot:
        if mime_type not in chat_config.ALL_ALLOWED_MIMES:
            raise AttachmentValidationException(mime_type=mime_type)

        if mime_type in chat_config.ALLOWED_IMAGE_MIMES:
            attachment_type = AttachmentType.IMAGE
            max_size = chat_config.MAX_MEDIA_SIZE
        elif mime_type in chat_config.ALLOWED_VIDEO_MIMES:
            attachment_type = AttachmentType.VIDEO
            max_size = chat_config.MAX_FILE_SIZE
        else:
            attachment_type = AttachmentType.FILE
            max_size = chat_config.MAX_FILE_SIZE

        if file_size <= 0 or file_size > max_size:
            raise AttachmentValidationException(
                mime_type=mime_type
            )

        new_file_name = self.clean_filename.sub("_", filename.strip())[:200]
        s3_key = f"chats/{chat_id}/{uuid4()}/{new_file_name}"

        upload_url = await self.storage_service.upload_put_url(
            bucket_name=chat_config.ATTACHMENT_BUCKET,
            file_key=s3_key,
            expires=chat_config.ATTACHMENT_UPLOAD_TOKEN_TTL,
        )

        token = str(uuid4())
        data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "s3_key": s3_key,
            "upload_token": token,
            "mime_type": mime_type,
            "file_size": file_size,
            "original_filename": filename,
            "attachment_type": attachment_type.value,
            "status": AttachmentStatus.PENDING.value
        }
        key = f"pending_upload:{user_id}:{token}"
        await self.redis.setex(key, chat_config.ATTACHMENT_UPLOAD_TOKEN_TTL, orjson.dumps(data))

        return UploadSlot(
            upload_token=token,
            upload_url=upload_url,
            s3_key=s3_key,
            attachment_type=attachment_type,
            expires_in=chat_config.ATTACHMENT_UPLOAD_TOKEN_TTL,
        )

    async def get_upload_slot(
        self, user_id: int,
        chat_id: int,
        tokens: list[str]
    ) -> list[UploadedAttachment]:
        attachment: list[UploadedAttachment] = []

        for token in tokens:
            key = f"pending_upload:{user_id}:{token}"
            raw = await self.redis.getdel(key)
            if raw is None:
                raise InvalidUploadTokenException(token=token)

            data = orjson.loads(raw)

            if data["user_id"] != user_id or data["chat_id"] != chat_id:
                raise InvalidUploadTokenException(token=token)

            attachment.append(
                UploadedAttachment(
                    chat_id=data["chat_id"],
                    user_id=data["user_id"],
                    s3_key=data["s3_key"],
                    mime_type=data["mime_type"],
                    file_size=data["file_size"],
                    upload_token=data["upload_token"],
                    original_filename=data["original_filename"],
                    attachment_type=AttachmentType(data["attachment_type"]),
                    status=AttachmentStatus(data["status"])
                )
            )

        return attachment

    async def get_success_upload_slot(
        self,
        user_id: int,
        chat_id: int,
        tokens: list[str]
    ) -> list[UploadedAttachment]:
        attachment = await self.get_upload_slot(user_id=user_id, chat_id=chat_id, tokens=tokens)

        media_count = sum(
            1 for a in attachment if a.attachment_type in (AttachmentType.IMAGE, AttachmentType.VIDEO)
        )
        file_count = sum(1 for a in attachment if a.attachment_type == AttachmentType.FILE)

        success = all(True if a.status == AttachmentStatus.SUCCESS else False for a in attachment)

        if media_count > chat_config.MAX_MEDIA_PER_MESSAGE:
            raise AttachmentLimitExceededException(count=media_count)
        if file_count > chat_config.MAX_FILES_PER_MESSAGE:
            raise AttachmentLimitExceededException(count=file_count)

        if success is False:
            raise AttachmentNotFoundException(attachment_id="")

        return attachment

    async def mark_success(self, user_id: int, claimed: UploadedAttachment) -> None:
        data = asdict(claimed)
        key = f"pending_upload:{user_id}:{claimed.upload_token}"
        await self.redis.setex(key, chat_config.ATTACHMENT_UPLOAD_TOKEN_TTL, orjson.dumps(data))


    async def get_attachemnt_url(self, attachment_id: UUID, s3_key: str) -> str:
        url = await self.redis.get(str(attachment_id))
        if url is None:
            url = await self.storage_service.generate_presigned_url(
                chat_config.ATTACHMENT_BUCKET, file_key=s3_key, expires=chat_config.DOWNLOAD_URL_TTL
            )
            await self.redis.setex(name=f"attachment:{str(attachment_id)}", value=url, time=chat_config.DOWNLOAD_URL_TTL)

        return url
