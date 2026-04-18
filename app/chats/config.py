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


chat_config = ChatConfig()

