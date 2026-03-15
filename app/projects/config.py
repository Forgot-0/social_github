from app.core.configs.base import BaseConfig


class ProjectConfig(BaseConfig):
    MAX_LEN_TAG: int = 50
    MAX_LEN_NAME: int = 200
    MAX_LEN_SLUG: int = 210
    MAX_LEN_ROLE_NAME: int = 80

    # Business limits (can be overridden via env/config)
    MAX_PROJECTS_PER_USER: int = 3
    MAX_POSITIONS_PER_PROJECT: int = 5


project_config = ProjectConfig()

