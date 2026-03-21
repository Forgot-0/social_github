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


@dataclass(kw_only=True)
class NotChatMemberException(ApplicationException):
    chat_id: int
    user_id: int
    code: str = "NOT_CHAT_MEMBER"
    status: int = 403

    @property
    def message(self) -> str:
        return "You are not a member of this chat"

    @property
    def detail(self):
        return {"chat_id": self.chat_id, "user_id": self.user_id}


@dataclass(kw_only=True)
class NotFoundMessageException(ApplicationException):
    message_id: int
    code: str = "NOT_FOUND_MESSAGE"
    status: int = 404

    @property
    def message(self) -> str:
        return "Message not found"

    @property
    def detail(self):
        return {"message_id": self.message_id}


@dataclass(kw_only=True)
class AccessDeniedChatException(ApplicationException):
    code: str = "CHAT_ACCESS_DENIED"
    status: int = 403

    @property
    def message(self) -> str:
        return "Insufficient chat permissions"

    @property
    def detail(self):
        return {}


@dataclass(kw_only=True)
class AlreadyMemberException(ApplicationException):
    user_id: int
    chat_id: int
    code: str = "ALREADY_CHAT_MEMBER"
    status: int = 409

    @property
    def message(self) -> str:
        return "User is already a member of this chat"

    @property
    def detail(self):
        return {"user_id": self.user_id, "chat_id": self.chat_id}


@dataclass(kw_only=True)
class DirectChatAlreadyExistsException(ApplicationException):
    chat_id: int
    code: str = "DIRECT_CHAT_EXISTS"
    status: int = 409

    @property
    def message(self) -> str:
        return "Direct chat already exists"

    @property
    def detail(self):
        return {"chat_id": self.chat_id}


@dataclass(kw_only=True)
class MemberLimitExceededException(ApplicationException):
    limit: int
    code: str = "MEMBER_LIMIT_EXCEEDED"
    status: int = 400

    @property
    def message(self) -> str:
        return f"Chat member limit reached ({self.limit})"

    @property
    def detail(self):
        return {"limit": self.limit}


@dataclass(kw_only=True)
class MessageTooLongException(ApplicationException):
    length: int
    max_length: int
    code: str = "MESSAGE_TOO_LONG"
    status: int = 400

    @property
    def message(self) -> str:
        return f"Message exceeds max length of {self.max_length}"

    @property
    def detail(self):
        return {"length": self.length, "max_length": self.max_length}