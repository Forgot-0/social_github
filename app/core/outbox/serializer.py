from dataclasses import asdict
from typing import Any

from app.core.events.event import BaseEvent



def event_to_payload(event: BaseEvent) -> dict[str, Any]:
    data = asdict(event)
    data["event_name"] = event.get_name()
    return data
