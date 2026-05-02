from app.core.configs.base import BaseConfig


class ChatConfig(BaseConfig):
    MAX_MEMBERS: int = 1_000
    MAX_GROUP_MEMBERS: int = 500
    MAX_SUPERGROUP_MEMBERS: int = 1_000_000
    MAX_CHANNEL_SUBSCRIBERS: int = 10_000_000
    MAX_MESSAGE_LENGTH: int = 4_096
    MAX_EDIT_WINDOW_HOURS: int = 48
    MAX_EDIT_HISTORY: int = 20
    MAX_REACTIONS_PER_MESSAGE: int = 20
    MAX_SEARCH_RESULTS: int = 50
    MAX_BULK_ADD_MEMBERS: int = 100
    FAN_OUT_WRITE_THRESHOLD: int = 500
    MAX_SLOW_MODE_SECONDS: int = 86_400
    CHAT_STAFF_MIN_ROLE_LEVEL: int = 80
    CHAT_EDITOR_MIN_ROLE_LEVEL: int = 80

    WS_HEARTBEAT_INTERVAL: int = 30
    WS_HEARTBEAT_TIMEOUT: int = 75
    WS_SEND_QUEUE_SIZE: int = 256
    WS_MAX_CONNECTIONS_PER_USER: int = 2
    WS_REDIS_CONNECTION_TTL: int = 90
    WS_ACTIVE_SUBSCRIPTION_TTL: int = 120
    WS_ACTIVE_SUBSCRIBER_SCAN_COUNT: int = 1_000
    WS_REPLAY_BATCH_SIZE: int = 500
    WS_MAX_CLIENT_FRAME_BYTES: int = 65536
    RATE_LIMIT_MESSAGES_PER_SECOND: int = 10

    CHAT_TOPIC: str = "chat-events"

    DELIVERY_ROUTER_GROUP_ID: str = "delivery-router"
    DELIVERY_ROUTER_CLIENT_ID: str = "delivery-router"
    DELIVERY_ROUTER_MEMBER_BATCH_SIZE: int = 2_000
    DELIVERY_ROUTER_ROUTE_LOOKUP_BATCH_SIZE: int = 500
    DELIVERY_ROUTER_ACTIVE_SUBSCRIBER_SCAN_BATCH_SIZE: int = 1_000
    DELIVERY_ROUTER_MAX_POLL_RECORDS: int = 500
    DELIVERY_ROUTER_POLL_TIMEOUT_MS: int = 1_000

    WS_GATEWAY_STREAM_MAXLEN: int = 200_000
    WS_GATEWAY_STREAM_READ_COUNT: int = 200
    WS_GATEWAY_STREAM_BLOCK_MS: int = 5_000
    WS_GATEWAY_STREAM_USERS_PER_ENTRY: int = 1_000

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
    DOWNLOAD_URL_TTL: int = 300

    ATTACHMENT_BUCKET: str = "chat-attachments"
    ATTACHMENT_UPLOAD_TOKEN_TTL: int = 3600



chat_config = ChatConfig()

