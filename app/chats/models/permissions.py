from enum import Enum

from app.chats.models.chat_roles import ChatRole


[
    "chat:delete", "chat:update", "chat:get",
    "member:invite", "member:kick", "member:ban", "member:mute",
    "role:change", "permission:update",
    "message:delete", "message:send", "message:pin"
    "settings:update", "settings:get"
]


class ProjectRolesEnum(Enum):
    OWNER = ChatRole(
        id=1,
        name="owner",
        level=9,
        permissions={
            
        }
    )

    ADMIN = ChatRole(
        id=2,
        name="admin",
        level=8,
        permissions={
            
        }
    )

    MEMBER = ChatRole(
        id=4,
        name="member",
        level=7,
        permissions={
        }
    )

    VIEWER = ChatRole(
        id=5,
        name="viewer",
        level=1,
        permissions={

        }
    )

    @classmethod
    def get_all_chat_roles(cls) -> list[ChatRole]:
        return [role.value for role in cls]

