from dataclasses import dataclass
from typing import Any

from app.core.exceptions import ApplicationException


@dataclass(kw_only=True)
class RoomNotFoundException(ApplicationException):
    slug: str
    code: str = "ROOM_NOT_FOUND"
    status: int = 404

    @property
    def message(self) -> str:
        return "Room not found"

    @property
    def detail(self) -> dict[str, Any]:
        return {"slug": self.slug}


@dataclass(kw_only=True)
class RoomAlreadyExistsException(ApplicationException):
    slug: str
    code: str = "ROOM_ALREADY_EXISTS"
    status: int = 409

    @property
    def message(self) -> str:
        return "Room with this slug already exists"

    @property
    def detail(self) -> dict[str, Any]:
        return {"slug": self.slug}


@dataclass(kw_only=True)
class AlreadyRoomMemberException(ApplicationException):
    user_id: int
    slug: str
    code: str = "ALREADY_ROOM_MEMBER"
    status: int = 409

    @property
    def message(self) -> str:
        return "User is already a member of this room"

    @property
    def detail(self) -> dict[str, Any]:
        return {"user_id": self.user_id, "slug": self.slug}


@dataclass(kw_only=True)
class NotRoomMemberException(ApplicationException):
    user_id: int
    slug: str
    code: str = "NOT_ROOM_MEMBER"
    status: int = 404

    @property
    def message(self) -> str:
        return "User is not a member of this room"

    @property
    def detail(self) -> dict[str, Any]:
        return {"user_id": self.user_id, "slug": self.slug}


@dataclass(kw_only=True)
class UserBannedException(ApplicationException):
    user_id: int
    slug: str
    code: str = "USER_BANNED"
    status: int = 403

    @property
    def message(self) -> str:
        return "User is banned from this room"

    @property
    def detail(self) -> dict[str, Any]:
        return {"user_id": self.user_id, "slug": self.slug}


@dataclass(kw_only=True)
class InsufficientRoomPermissionException(ApplicationException):
    required: str
    code: str = "INSUFFICIENT_ROOM_PERMISSION"
    status: int = 403

    @property
    def message(self) -> str:
        return f"Insufficient room permission: {self.required}"

    @property
    def detail(self) -> dict[str, Any]:
        return {"required_permission": self.required}


@dataclass(kw_only=True)
class RoomRoleNotFoundException(ApplicationException):
    role_id: int
    code: str = "ROOM_ROLE_NOT_FOUND"
    status: int = 404

    @property
    def message(self) -> str:
        return "Room role not found"

    @property
    def detail(self) -> dict[str, Any]:
        return {"role_id": self.role_id}


@dataclass(kw_only=True)
class CannotKickOwnerException(ApplicationException):
    code: str = "CANNOT_KICK_OWNER"
    status: int = 403

    @property
    def message(self) -> str:
        return "Cannot kick the room owner"

    @property
    def detail(self) -> dict[str, Any]:
        return {}


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
