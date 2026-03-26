from livekit.protocol.models import ParticipantInfo

from app.core.db.base_model import BaseModel



class JoinTokenDTO(BaseModel):
    token: str
    slug: str
    livekit_url: str


class LiveKitParticipantsDTO(BaseModel):
    identity: str
    name: str
    state: ParticipantInfo.State
    joined_at: int
