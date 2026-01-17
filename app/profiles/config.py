from app.core.configs.base import BaseConfig


class ProfileConfig(BaseConfig):
    AVATAR_BUCKET: str = "profiles"


profile_config = ProfileConfig()
