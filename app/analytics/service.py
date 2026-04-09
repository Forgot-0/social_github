from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from clickhouse_connect.driver import AsyncClient


@dataclass
class AnalyticsClickHouseService:
    client: AsyncClient

    # def __post_init__(self) -> None:
        # self.client = await clickhouse_connect.get_async_client(
        #     host=self.host,
        #     port=self.port,
        #     username=self.user,
        #     password=self.password,
        #     database=self.database,
        # )

    def normalize_event(self, message: dict[str, Any]) -> dict[str, Any]:
        payload = message.get("payload", {})
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
            "actor_id": payload.get("sender_id") or payload.get("user_id") or 0,
            "entity_id": payload.get("chat_id") or payload.get("project_id") or payload.get("message_id") or 0,
            "payload": payload,
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
