from dataclasses import asdict
import json
from typing import Any

from app.core.api.schemas import additionally_serialize
from app.core.events.event import BaseEvent



def event_to_payload(event: BaseEvent) -> dict[str, Any]:
    data = asdict(event)
    data["event_name"] = event.get_name()
    return json.loads(
        json.dumps(data, default=additionally_serialize)
    )
