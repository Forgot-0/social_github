from app.core.configs.base import BaseConfig


class RoomConfig(BaseConfig):
    LIVEKIT_URL: str = "ws://localhost:7880"
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    ROOM_TOKEN_TTL: int = 3600
    ROOM_MAX_PARTICIPANTS: int = 50
    ROOM_SLUG_MAX_LEN: int = 64


room_config = RoomConfig()
