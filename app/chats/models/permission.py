from enum import Enum

from app.chats.models.chat_roles import ChatRole



class ProjectRolesEnum(Enum):
    OWNER = ChatRole(
        id=1,
        name="owner",
        level=9,
        permissions={
            "chat:delete": True, "chat:update": True, "chat:get": True,
            "member:invite": True, "member:kick": True, "member:ban": True, "member:mute": True,
            "role:change": True, "permission:update": True,
            "message:delete": True, "message:send": True, "message:pin": True,
            "settings:update": True, "settings:get": True
        }
    )

    ADMIN = ChatRole(
        id=2,
        name="admin",
        level=8,
        permissions={
            "chat:delete": False, "chat:update": True, "chat:get": True,
            "member:invite": True, "member:kick": True, "member:ban": True, "member:mute": True,
            "role:change": True, "permission:update": True,
            "message:delete": True, "message:send": True, "message:pin": True,
            "settings:update": True, "settings:get": True
        }
    )

    DIRECT_MEMBER = ChatRole(
        id=4,
        name="direct",
        level=7,
        permissions={
            "chat:delete": False, "chat:update": True, "chat:get": True,
            "member:invite": False, "member:kick": False, "member:ban": False, "member:mute": False,
            "role:change": False, "permission:update": False,
            "message:delete": False, "message:send": True, "message:pin": True,
            "settings:update": False, "settings:get": True
        }
    )

    MEMBER = ChatRole(
        id=5,
        name="member",
        level=7,
        permissions={
            "chat:delete": False, "chat:update": False, "chat:get": True,
            "member:invite": False, "member:kick": False, "member:ban": False, "member:mute": False,
            "role:change": False, "permission:update": False,
            "message:delete": False, "message:send": True, "message:pin": False,
            "settings:update": False, "settings:get": True
        }
    )

    VIEWER = ChatRole(
        id=6,
        name="viewer",
        level=1,
        permissions={
            "chat:delete": False, "chat:update": False, "chat:get": True,
            "member:invite": False, "member:kick": False, "member:ban": False, "member:mute": False,
            "role:change": False, "permission:update": False,
            "message:delete": False, "message:send": False, "message:pin": False,
            "settings:update": False, "settings:get": True
        }
    )

    @classmethod
    def get_all_chat_roles(cls) -> list[ChatRole]:
        return [role.value for role in cls]

