from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.chats.dtos.livekit import LiveKitParticipantsDTO


class CallStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"



class CallDTO(BaseModel):
    id: int
    chat_id: int
    slug: str
    started_by: int
    status: CallStatus
    started_at: datetime
    ended_at: datetime | None = None
    participants: list[LiveKitParticipantsDTO] = []
    livekit_url: str


class ActiveCallDTO(BaseModel):
    room_id: int
    chat_id: int
    slug: str
    started_by: int
    started_at: datetime
    participant_count: int
    livekit_url: str
