import logging
import re
from dataclasses import asdict, dataclass
from uuid import uuid4

import magic
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

logger = logging.getLogger(__name__)


_UPLOAD_TOKEN_TTL = 3600
_DOWNLOAD_URL_TTL = 300
_DOWNLOAD_CACHE_TTL = 240

MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_MEDIA_SIZE = 50 * 1024 * 1024

MAX_MEDIA_PER_MESSAGE = 10
MAX_FILES_PER_MESSAGE = 1

ALLOWED_IMAGE_MIMES = frozenset({
    "image/jpeg", "image/png", "image/gif",
    "image/webp", "image/heic", "image/heif",
})
ALLOWED_VIDEO_MIMES = frozenset({
    "video/mp4", "video/webm",
    "video/quicktime", "video/x-msvideo",
})
ALLOWED_FILE_MIMES = frozenset({
    "application/pdf",
    "application/zip", "application/x-zip-compressed",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain", "text/csv",
    "application/octet-stream",
})
ALL_ALLOWED_MIMES = ALLOWED_IMAGE_MIMES | ALLOWED_VIDEO_MIMES | ALLOWED_FILE_MIMES

_SAFE_FILENAME_RE = re.compile(r"[^\w.\-]")

def resolve_attachment_type(mime_type: str) -> AttachmentType:
    if mime_type in ALLOWED_IMAGE_MIMES:
        return AttachmentType.IMAGE
    if mime_type in ALLOWED_VIDEO_MIMES:
        return AttachmentType.VIDEO
    return AttachmentType.FILE


def sanitize_filename(filename: str) -> str:
    name = _SAFE_FILENAME_RE.sub("_", filename.strip())
    return name[:200] or "file"


@dataclass(frozen=True)
class UploadSlot:
    upload_token: str
    upload_url: str
    s3_key: str
    attachment_type: AttachmentType
    expires_in: int


@dataclass(frozen=True)
class ClaimedAttachment:
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
class UploadTokenManager:
    redis: Redis

    async def create_pending_data(self, data: dict) -> None:
        upload_token = data["upload_token"]
        key = f"pending_upload:{data['user_id']}:{upload_token}"
        await self.redis.setex(key, _UPLOAD_TOKEN_TTL, orjson.dumps(data))

    async def get_pending_data(self, user_id: int, token: str) -> dict | None:
        key = f"pending_upload:{user_id}:{token}"
        raw = await self.redis.get(key)
        if raw:
            return orjson.loads(raw)
        return None

    async def claim_pending_data(self, user_id: int, token: str) -> dict | None:
        key = f"pending_upload:{user_id}:{token}"
        raw = await self.redis.getdel(key)
        if raw:
            return orjson.loads(raw)
        return None

    async def mark_success(self, user_id: int, token: str, data: dict) -> None:
        key = f"pending_upload:{user_id}:{token}"
        await self.redis.setex(key, _UPLOAD_TOKEN_TTL, orjson.dumps(data))


@dataclass
class MimeValidator:
    def validate(self, mime_type: str, file_size: int) -> AttachmentType:
        if mime_type not in ALL_ALLOWED_MIMES:
            raise AttachmentValidationException(mime_type=f"MIME type not allowed: {mime_type}")

        attachment_type = resolve_attachment_type(mime_type)
        max_size = MAX_MEDIA_SIZE if attachment_type != AttachmentType.FILE else MAX_FILE_SIZE

        if file_size <= 0 or file_size > max_size:
            raise AttachmentValidationException(
                mime_type=f"Invalid file size {file_size}. Max: {max_size} bytes"
            )

        return attachment_type


@dataclass
class UploadSlotFactory:
    token_manager: UploadTokenManager
    storage_service: StorageService
    mime_validator: MimeValidator

    async def create(
        self,
        chat_id: int,
        user_id: int,
        filename: str,
        mime_type: str,
        file_size: int,
    ) -> UploadSlot:
        attachment_type = self.mime_validator.validate(mime_type, file_size)

        safe_name = sanitize_filename(filename)
        s3_key = f"chats/{chat_id}/{uuid4()}/{safe_name}"

        upload_url = await self.storage_service.upload_put_url(
            bucket_name=chat_config.ATTACHMENT_BUCKET,
            file_key=s3_key,
            expires=_UPLOAD_TOKEN_TTL,
        )

        upload_token = str(uuid4())
        pending = {
            "chat_id": chat_id,
            "user_id": user_id,
            "s3_key": s3_key,
            "upload_token": upload_token,
            "mime_type": mime_type,
            "file_size": file_size,
            "original_filename": filename,
            "attachment_type": attachment_type.value,
            "status": AttachmentStatus.PENDING.value
        }

        await self.token_manager.create_pending_data(pending)

        logger.info(
            "Upload slot created",
            extra={"chat_id": chat_id, "user_id": user_id, "s3_key": s3_key},
        )
        return UploadSlot(
            upload_token=upload_token,
            upload_url=upload_url,
            s3_key=s3_key,
            attachment_type=attachment_type,
            expires_in=_UPLOAD_TOKEN_TTL,
        )


@dataclass
class AttachmentDownloadService:
    storage_service: StorageService
    redis: Redis

    def _download_cache_key(self, attachment_id: str) -> str:
        return f"att_url:{attachment_id}"

    async def get_download_url(self, attachment_id: str, s3_key: str) -> str:
        cache_key = self._download_cache_key(attachment_id)
        cached = await self.redis.get(cache_key)
        if cached:
            return cached.decode()

        url = await self.storage_service.generate_presigned_url(
            bucket_name=chat_config.ATTACHMENT_BUCKET,
            file_key=s3_key,
            expires=_DOWNLOAD_URL_TTL,
        )

        await self.redis.setex(cache_key, _DOWNLOAD_CACHE_TTL, url)
        return url

    async def invalidate_download_cache(self, attachment_id: str) -> None:
        await self.redis.delete(self._download_cache_key(attachment_id))


@dataclass
class AttachmentService:
    token_manager: UploadTokenManager
    slot_factory: UploadSlotFactory
    download_service: AttachmentDownloadService

    async def create_upload_slot(
        self,
        chat_id: int,
        user_id: int,
        filename: str,
        mime_type: str,
        file_size: int,
    ) -> UploadSlot:
        return await self.slot_factory.create(chat_id, user_id, filename, mime_type, file_size)

    async def claim_tokens(
        self,
        user_id: int,
        chat_id: int,
        tokens: list[str],
    ) -> list[ClaimedAttachment]:
        claimed: list[ClaimedAttachment] = []

        for token in tokens:
            data = await self.token_manager.claim_pending_data(user_id, token)
            if data is None:
                raise InvalidUploadTokenException(token=token)

            if data["user_id"] != user_id or data["chat_id"] != chat_id:
                raise InvalidUploadTokenException(token=token)

            claimed.append(
                ClaimedAttachment(
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

        return claimed

    async def mark_success(self, user_id: int, claimed: ClaimedAttachment) -> None:
        data = asdict(claimed)
        await self.token_manager.mark_success(user_id, claimed.upload_token, data)

    async def claim_tokens_for_message(
        self,
        user_id: int,
        chat_id: int,
        tokens: list[str],
    ) -> list[ClaimedAttachment]:
        claimed = await self.claim_tokens(user_id=user_id, chat_id=chat_id, tokens=tokens)

        media_count = sum(
            1 for a in claimed if a.attachment_type in (AttachmentType.IMAGE, AttachmentType.VIDEO)
        )
        file_count = sum(1 for a in claimed if a.attachment_type == AttachmentType.FILE)

        success = all(True if a.status == AttachmentStatus.SUCCESS else False for a in claimed)

        if media_count > MAX_MEDIA_PER_MESSAGE:
            raise AttachmentLimitExceededException(count=media_count)
        if file_count > MAX_FILES_PER_MESSAGE:
            raise AttachmentLimitExceededException(count=file_count)

        if success is False:
            raise AttachmentNotFoundException(attachment_id="")

        for cl in claimed:
            data = await self.slot_factory.storage_service.download_range(
                bucket_name=chat_config.ATTACHMENT_BUCKET,
                file_key=cl.s3_key,
                offset=0,
                length=1024
            )
            actual_mime = magic.from_buffer(data, mime=True)
            if actual_mime != cl.mime_type:
                raise AttachmentValidationException(
                    mime_type=f"MIME type mismatch: expected {cl.mime_type}, got {actual_mime}"
                )

        return claimed

    async def get_download_url(self, attachment_id: str, s3_key: str) -> str:
        return await self.download_service.get_download_url(attachment_id, s3_key)

    async def invalidate_download_cache(self, attachment_id: str) -> None:
        await self.download_service.invalidate_download_cache(attachment_id)
