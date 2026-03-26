from enum import Enum

from app.rooms.models.role_chat import RoomRole

# Здесь существенное отличие от других подобных прав так как это для удобства с livekit

class RoleRoomEnum(str, Enum):
    OWNER = RoomRole(
        name="owner",
        level=100,
        permissions={
            "manage_roles": True, "manage_channels": True,
            "kick": True, "ban": True, "mute": True, "connect_voice": True,
            "speak": True, "share_screen": True
        }
    )

    ADMIN = RoomRole(
        name="admin",
        level=99,
        permissions={
            "manage_roles": False, "manage_channels": True,
            "kick": True, "ban": True, "mute": True, "connect_voice": True,
            "speak": True, "share_screen": True
        }
    )

    MODERATOR = RoomRole(
        name="moderator",
        level=98,
        permissions={
            "manage_roles": False, "manage_channels": False,
            "kick": True, "ban": False, "mute": True, "connect_voice": True,
            "speak": True, "share_screen": True
        }
    )

    MEMBER = RoomRole(
        name="member",
        level=97,
        permissions={
            "manage_roles": False, "manage_channels": False,
            "kick": False, "ban": False, "mute": False, "connect_voice": True,
            "speak": True, "share_screen": True
        }
    )

    GUEST = RoomRole(
        name="guest",
        level=96,
        permissions={
            "manage_roles": False, "manage_channels": False,
            "kick": False, "ban": False, "mute": False, "connect_voice": True,
            "speak": False, "share_screen": False
        }
    )

