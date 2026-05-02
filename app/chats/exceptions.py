from dataclasses import dataclass
from typing import Any

from app.chats.config import chat_config
from app.core.exceptions import ApplicationException


@dataclass(kw_only=True)
class NotFoundChatException(ApplicationException):
    chat_id: str
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
    chat_id: str
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
    message_id: str
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
    chat_id: str
    requester_id: int

    code: str = "CHAT_ACCESS_DENIED"
    status: int = 403

    @property
    def message(self) -> str:
        return "Insufficient chat permissions"

    @property
    def detail(self):
        return {"chat_id": self.chat_id, "requester_id": self.requester_id}


@dataclass(kw_only=True)
class SlowModeOutOfRangeException(ApplicationException):
    seconds: int
    code: str = "SLOW_MODE_OUT_OF_RANGE"
    status: int = 400

    @property
    def message(self) -> str:
        return "slow_mode_seconds is out of allowed range"

    @property
    def detail(self) :
        return {"seconds": self.seconds, "valid_range": [0, chat_config.MAX_SLOW_MODE_SECONDS]}


@dataclass(kw_only=True)
class SlowModeLimitException(ApplicationException):
    chat_id: str
    retry_after: int
    code: str = "SLOW_MODE_LIMIT"
    status: int = 429

    @property
    def message(self) -> str:
        return "Slow mode is enabled for this chat"

    @property
    def detail(self) -> dict[str, Any]:
        return {"chat_id": self.chat_id, "retry_after": self.retry_after}


@dataclass(kw_only=True)
class AlreadyMemberException(ApplicationException):
    user_id: int
    chat_id: str
    code: str = "ALREADY_CHAT_MEMBER"
    status: int = 409

    @property
    def message(self) -> str:
        return "User is already a member of this chat"

    @property
    def detail(self):
        return {"user_id": self.user_id, "chat_id": self.chat_id}


@dataclass(kw_only=True)
class TooLongChatRoleNameException(ApplicationException):
    role_name: str
    code: str = "TOO_LONG_CHAT_ROLE_NAME"
    status: int = 400

    @property
    def message(self) -> str:
        return "Too long chat role name"

    @property
    def detail(self):
        return {"role_name": self.role_name, "max_len": 32}


@dataclass(kw_only=True)
class DirectChatAlreadyExistsException(ApplicationException):
    chat_id: str
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


@dataclass(kw_only=True)
class LiveKitServiceException(ApplicationException):
    reason: str
    code: str = "LIVEKIT_ERROR"
    status: int = 502

    @property
    def message(self) -> str:
        return "LiveKit service error"

    @property
    def detail(self) -> dict[str, Any]:
        return {"reason": self.reason}


@dataclass(kw_only=True)
class LiveKitUnauthorizedException(ApplicationException):
    code: str = "LIVEKIT_UNAUTHORIZED"
    status: int = 502

    @property
    def message(self) -> str:
        return "LiveKit unauthorized"

    @property
    def detail(self) -> dict[str, Any]:
        return {}


@dataclass(kw_only=True)
class NoActiveCallException(ApplicationException):
    chat_id: str
    code: str = "NO_ACTIVE_CALL"
    status: int = 404

    @property
    def message(self) -> str:
        return "There is no active call in this chat"

    @property
    def detail(self) -> dict[str, Any]:
        return {"chat_id": self.chat_id}


@dataclass(kw_only=True)
class ActiveCallExistsException(ApplicationException):
    chat_id: str
    code: str = "ACTIVE_CALL_EXISTS"
    status: int = 409

    @property
    def message(self) -> str:
        return "A call is already active in this chat"

    @property
    def detail(self) -> dict[str, Any]:
        return {"chat_id": self.chat_id}


@dataclass(kw_only=True)
class AttachmentValidationException(ApplicationException):
    mime_type: str
    code: str = "ATTACHMENT_VALIDATION"
    status: int = 400

    @property
    def message(self) -> str:
        return "Attachment validation failed"

    @property
    def detail(self) -> dict[str, Any]:
        return {"mime_type": self.mime_type}


@dataclass(kw_only=True)
class InvalidUploadTokenException(ApplicationException):
    token: str
    code: str = "INVALID_UPLOAD_TOKEN"
    status: int = 400

    @property
    def message(self) -> str:
        return "Upload token is invalid, expired, or does not belong to this chat"

    @property
    def detail(self) -> dict[str, Any]:
        return {"token": self.token}


@dataclass(kw_only=True)
class AttachmentLimitExceededException(ApplicationException):
    count: int
    code: str = "ATTACHMENT_LIMIT_EXCEEDED"
    status: int = 400

    @property
    def message(self) -> str:
        return "Attachment limit exceeded"

    @property
    def detail(self) -> dict[str, Any]:
        return {"count": self.count}


@dataclass(kw_only=True)
class AttachmentNotFoundException(ApplicationException):
    attachment_id: str
    code: str = "ATTACHMENT_NOT_FOUND"
    status: int = 404

    @property
    def message(self) -> str:
        return "Attachment not found"

    @property
    def detail(self) -> dict[str, Any]:
        return {"attachment_id": self.attachment_id}


@dataclass(kw_only=True)
class IdempotencyConflictException(ApplicationException):
    key: str
    code: str = "IDEMPOTENCY_CONFLICT"
    status: int = 409

    @property
    def message(self) -> str:
        return "Request with this idempotency key is already being processed"

    @property
    def detail(self) -> dict[str, Any]:
        return {"key": self.key}


@dataclass(kw_only=True)
class InvalidMessageException(ApplicationException):
    reason: str
    code: str = "INVALID_MESSAGE"
    status: int = 400

    @property
    def message(self) -> str:
        return "Invalid message payload"

    @property
    def detail(self) -> dict[str, Any]:
        return {"reason": self.reason}


@dataclass(kw_only=True)
class EmptyAttachmentUploadRequestException(ApplicationException):
    code: str = "EMPTY_ATTACHMENT_UPLOAD_REQUEST"
    status: int = 400

    @property
    def message(self) -> str:
        return "At least one attachment upload must be requested"

    @property
    def detail(self) -> dict[str, Any]:
        return {}
