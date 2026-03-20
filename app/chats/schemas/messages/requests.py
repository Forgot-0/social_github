from pydantic import BaseModel, Field


class SendMessageRequests(BaseModel):
    recipient_id: int
    message: str


class GetMessagesRequest(BaseModel):
    limit: int = Field(default=30, ge=30, le=100)
    before_id: int | None = Field(default=None)
