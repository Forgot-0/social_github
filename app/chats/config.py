from app.core.configs.base import BaseConfig


class ChatConfig(BaseConfig):
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200

    MAX_MESSAGE_LENGTH: int = 4096
    MAX_MEMBERS: int = 100

    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS_PER_USER: int = 2
    RATE_LIMIT_MESSAGES_PER_SECOND: int = 10


chat_config = ChatConfig()

