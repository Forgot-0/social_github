from dataclasses import dataclass

from app.core.exceptions import ApplicationException


@dataclass(kw_only=True)
class NotFoundChatException(ApplicationException):
    chat_id: int

    code: str = "NOT_FOUND_CHAT"
    status: int = 404

    @property
    def message(self) -> str:
        return "Chat not found"

    @property
    def detail(self):
        return {"chat_id": self.chat_id}

