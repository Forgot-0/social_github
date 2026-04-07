from app.core.configs.base import BaseConfig


class ProfileConfig(BaseConfig):
    AVATAR_BUCKET: str = "profiles"
    AVATAR_MAX_SIZE: int = 5*1024*1024

    MAX_LEN_SKILL_NAME: int = 30
    MAX_LEN_BIO: int = 1024
    MAX_LEN_DISPLAY_NAME: int = 100

    USER_TOPIC: str = "users"


profile_config = ProfileConfig()
