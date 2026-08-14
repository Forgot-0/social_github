"""Load test configuration.

Everything is driven by environment variables so the same code runs from the
host (``localhost``) and from inside ``app-network`` (service names). No
hardcoded ``localhost`` defaults for infrastructure: the compose service names
are the defaults, and ``loadtests/.env.local.example`` shows the host override.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw else default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw else default


@dataclass(slots=True)
class LoadTestConfig:
    # Target under test.
    api_base_url: str = field(default_factory=lambda: _env("LT_API_BASE_URL", "http://app:8000"))
    ws_base_url: str = field(default_factory=lambda: _env("LT_WS_BASE_URL", "ws://app:8000"))
    api_prefix: str = field(default_factory=lambda: _env("LT_API_PREFIX", "/api/v1"))

    # Where the seeded dataset lives (shared volume between seed and locust).
    dataset_path: str = field(
        default_factory=lambda: _env("LT_DATASET_PATH", "/loadtests/data/dataset.json")
    )

    # Token minting. Must match the app's JWT settings or every request 401s.
    jwt_secret_key: str = field(default_factory=lambda: _env("JWT_SECRET_KEY", ""))
    jwt_algorithm: str = field(default_factory=lambda: _env("JWT_ALGORITHM", "HS256"))
    token_ttl_seconds: int = field(default_factory=lambda: _env_int("LT_TOKEN_TTL_SECONDS", 7_200))

    # Scenario shaping.
    ws_readers_per_chat: int = field(default_factory=lambda: _env_int("LT_WS_READERS_PER_CHAT", 50))
    ws_resume_interval_seconds: float = field(
        default_factory=lambda: _env_float("LT_WS_RESUME_INTERVAL_SECONDS", 1.0)
    )
    ws_churn_hold_seconds: float = field(
        default_factory=lambda: _env_float("LT_WS_CHURN_HOLD_SECONDS", 5.0)
    )
    send_wait_min_seconds: float = field(
        default_factory=lambda: _env_float("LT_SEND_WAIT_MIN_SECONDS", 0.1)
    )
    send_wait_max_seconds: float = field(
        default_factory=lambda: _env_float("LT_SEND_WAIT_MAX_SECONDS", 0.5)
    )
    message_size_bytes: int = field(default_factory=lambda: _env_int("LT_MESSAGE_SIZE_BYTES", 64))

    # Which seeded chat cohort a scenario targets.
    target_cohort: str = field(default_factory=lambda: _env("LT_TARGET_COHORT", "group"))

    @property
    def db_dsn(self) -> str:
        explicit = os.getenv("LT_DB_DSN")
        if explicit:
            return explicit
        user = _env("POSTGRES_USER", "postgres")
        password = _env("POSTGRES_PASSWORD", "postgres")
        host = _env("POSTGRES_SERVER", "db")
        port = _env_int("POSTGRES_PORT", 5432)
        db = _env("POSTGRES_DB", "postgres")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    @property
    def redis_url(self) -> str:
        explicit = os.getenv("LT_REDIS_URL")
        if explicit:
            return explicit
        host = _env("REDIS_HOST", "redis")
        port = _env_int("REDIS_PORT", 6379)
        return f"redis://{host}:{port}"

    def messages_url(self, chat_id: str) -> str:
        return f"{self.api_prefix}/chats/{chat_id}/messages/"

    def ws_url(self, token: str) -> str:
        return f"{self.ws_base_url}{self.api_prefix}/chats/ws/?token={token}"


config = LoadTestConfig()
