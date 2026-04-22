from app.core.configs.base import BaseConfig


class ChatConfig(BaseConfig):
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200

    MAX_MESSAGE_LENGTH: int = 4096
    MAX_MEMBERS: int = 100

    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS_PER_USER: int = 2
    RATE_LIMIT_MESSAGES_PER_SECOND: int = 10

    ATTACHMENT_BUCKET: str = "chat-attachments"

    CHAT_TOPIC: str = "CHATS"

    LIVEKIT_URL: str = "ws://localhost:7880"
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    ROOM_TOKEN_TTL: int = 3600
    ROOM_MAX_PARTICIPANTS: int = 100

    ALLOWED_IMAGE_MIMES: frozenset[str] = frozenset({
    "image/jpeg", "image/png", "image/gif",
    "image/webp", "image/heic", "image/heif",
})
    ALLOWED_VIDEO_MIMES: frozenset[str] = frozenset({
        "video/mp4", "video/webm",
        "video/quicktime", "video/x-msvideo",
    })
    ALLOWED_FILE_MIMES: frozenset[str] = frozenset({
        "application/pdf",
        "application/zip", "application/x-zip-compressed",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain", "text/csv",
    })
    ALL_ALLOWED_MIMES: frozenset[str] = ALLOWED_IMAGE_MIMES | ALLOWED_VIDEO_MIMES | ALLOWED_FILE_MIMES

    MAX_MEDIA_PER_MESSAGE: int = 10
    MAX_FILES_PER_MESSAGE: int = 1

    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    MAX_MEDIA_SIZE: int = 50 * 1024 * 1024

    ATTACHMENT_UPLOAD_TOKEN_TTL: int = 3600


chat_config = ChatConfig()

