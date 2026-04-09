from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Any

from clickhouse_connect.driver import AsyncClient

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsClickHouseService:
    client: AsyncClient

    def normalize_event(self, message: dict[str, Any]) -> dict[str, Any]:
        event_name = message.get("event_name", "unknown")

        ts_raw = message.get("created_at")
        if isinstance(ts_raw, str):
            event_time = datetime.fromisoformat(ts_raw)
        else:
            event_time = datetime.now(timezone.utc)

        return {
            "event_time": event_time,
            "event_name": event_name,
            "event_id": message.get("event_id", ""),
            "actor_id": message.get("sender_id") or message.get("user_id") or 0,
            "entity_id": message.get("message_id") or message.get("chat_id") or message.get("project_id") or 0,
            "payload": message,
            "source": "social_api",
        }

    async def insert_event(self, message: dict[str, Any]) -> None:
        normalized = self.normalize_event(message)

        await self.client.insert(
            table="analytics_events",
            data=[[
                normalized["event_time"],
                normalized["event_name"],
                normalized["event_id"],
                int(normalized["actor_id"]),
                int(normalized["entity_id"]),
                normalized["source"],
                normalized["payload"],
            ]],
            column_names=[
                "event_time",
                "event_name",
                "event_id",
                "actor_id",
                "entity_id",
                "source",
                "payload",
            ],
        )
        logger.info(
            "Insert event", extra={
                "event_id": str(normalized["event_id"]),
                "event_name": normalized["event_name"],
            }
        )
