from pydantic import BaseModel


class MuteParticipantRequest(BaseModel):
    muted: bool = True
