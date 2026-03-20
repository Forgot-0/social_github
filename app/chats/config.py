from app.core.configs.base import BaseConfig


class ChatConfig(BaseConfig):
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200

    MAX_MESSAGE_LENGTH: int = 4096

    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS_PER_USER: int = 5


chat_config = ChatConfig()

