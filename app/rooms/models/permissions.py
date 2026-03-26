from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class RoleBlueprint:
    id: int
    name: str
    level: int
    permissions: dict[str, bool]

    ALL_KEYS: ClassVar[tuple[str, ...]] = (
        "manage_roles",
        "manage_channels",
        "kick",
        "ban",
        "mute",
        "connect_voice",
        "speak",
        "share_screen",
        "send_message",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "permissions": self.permissions,
        }


OWNER_ROLE = RoleBlueprint(
    id=1,
    name="owner",
    level=100,
    permissions={
        "manage_roles": True, "manage_channels": True,
        "kick": True, "ban": True, "mute": True,
        "connect_voice": True, "speak": True,
        "share_screen": True, "send_message": True,
    },
)

ADMIN_ROLE = RoleBlueprint(
    id=2,
    name="admin",
    level=99,
    permissions={
        "manage_roles": False, "manage_channels": True,
        "kick": True, "ban": True, "mute": True,
        "connect_voice": True, "speak": True,
        "share_screen": True, "send_message": True,
    },
)

MODERATOR_ROLE = RoleBlueprint(
    id=3,
    name="moderator",
    level=98,
    permissions={
        "manage_roles": False, "manage_channels": False,
        "kick": True, "ban": False, "mute": True,
        "connect_voice": True, "speak": True,
        "share_screen": True, "send_message": True,
    },
)

MEMBER_ROLE = RoleBlueprint(
    id=4,
    name="member",
    level=1,
    permissions={
        "manage_roles": False, "manage_channels": False,
        "kick": False, "ban": False, "mute": False,
        "connect_voice": True, "speak": True,
        "share_screen": True, "send_message": True,
    },
)

GUEST_ROLE = RoleBlueprint(
    id=5,
    name="guest",
    level=0,
    permissions={
        "manage_roles": False, "manage_channels": False,
        "kick": False, "ban": False, "mute": False,
        "connect_voice": True, "speak": False,
        "share_screen": False, "send_message": False,
    },
)

DEFAULT_ROLES: list[RoleBlueprint] = [
    OWNER_ROLE, ADMIN_ROLE, MODERATOR_ROLE, MEMBER_ROLE, GUEST_ROLE,
]
