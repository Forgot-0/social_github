from app.core.configs.base import BaseConfig


class AnalyticConfig(BaseConfig):
    CLICKHOUSE_HOST: str = ""
    CLICKHOUSE_PORT: int = 8123
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DATABASE: str = "default"


analytic_config = AnalyticConfig()
