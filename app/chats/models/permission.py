from enum import Enum

from app.chats.models.chat_roles import ChatRole


OWNER_PERMISSIONS = {
    "chat:delete": True, "chat:update": True, "chat:get": True,
    "member:invite": True, "member:kick": True, "member:ban": True, "member:mute": True,
    "role:change": True, "permission:update": True,
    "message:read": True,
    "message:delete": True, "message:send": True, "message:pin": True,
    "message:send_admin_only": True,
    "settings:update": True, "settings:get": True,
    "channel:publish": True, "channel:edit": True, "channel:manage_subscribers": True,
    "slowmode:bypass": True,
    "call:join": True, "call:mute_member": True, "call:end": True,
}

ADMIN_PERMISSIONS = {
    **OWNER_PERMISSIONS,
    "chat:delete": False,
}

EDITOR_PERMISSIONS = {
    "chat:delete": False, "chat:update": False, "chat:get": True,
    "member:invite": False, "member:kick": False, "member:ban": False, "member:mute": False,
    "role:change": False, "permission:update": False,
    "message:read": True,
    "message:delete": True, "message:send": True, "message:pin": True,
    "message:send_admin_only": True,
    "settings:update": False, "settings:get": True,
    "channel:publish": True, "channel:edit": True, "channel:manage_subscribers": False,
    "slowmode:bypass": True,
    "call:join": True, "call:mute_member": False, "call:end": False,
}

DIRECT_MEMBER_PERMISSIONS = {
    "chat:delete": False, "chat:update": True, "chat:get": True,
    "member:invite": False, "member:kick": False, "member:ban": False, "member:mute": False,
    "role:change": False, "permission:update": False,
    "message:read": True,
    "message:delete": False, "message:send": True, "message:pin": True,
    "message:send_admin_only": False,
    "settings:update": False, "settings:get": True,
    "channel:publish": False, "channel:edit": False, "channel:manage_subscribers": False,
    "slowmode:bypass": False,
    "call:join": True, "call:mute_member": False, "call:end": False,
}

MEMBER_PERMISSIONS = {
    "chat:delete": False, "chat:update": False, "chat:get": True,
    "member:invite": False, "member:kick": False, "member:ban": False, "member:mute": False,
    "role:change": False, "permission:update": False,
    "message:read": True,
    "message:delete": False, "message:send": True, "message:pin": False,
    "message:send_admin_only": False,
    "settings:update": False, "settings:get": True,
    "channel:publish": False, "channel:edit": False, "channel:manage_subscribers": False,
    "slowmode:bypass": False,
    "call:join": True, "call:mute_member": False, "call:end": False,
}

VIEWER_PERMISSIONS = {
    "chat:delete": False, "chat:update": False, "chat:get": True,
    "member:invite": False, "member:kick": False, "member:ban": False, "member:mute": False,
    "role:change": False, "permission:update": False,
    "message:read": True,
    "message:delete": False, "message:send": False, "message:pin": False,
    "message:send_admin_only": False,
    "settings:update": False, "settings:get": True,
    "channel:publish": False, "channel:edit": False, "channel:manage_subscribers": False,
    "slowmode:bypass": False,
    "call:join": True, "call:mute_member": False, "call:end": False,
}


class ChatRolesEnum(Enum):
    OWNER = ChatRole(
        id=1,
        name="owner",
        level=100,
        permissions=OWNER_PERMISSIONS,
    )

    ADMIN = ChatRole(
        id=2,
        name="admin",
        level=90,
        permissions=ADMIN_PERMISSIONS,
    )

    EDITOR = ChatRole(
        id=3,
        name="editor",
        level=80,
        permissions=EDITOR_PERMISSIONS,
    )

    DIRECT_MEMBER = ChatRole(
        id=4,
        name="direct",
        level=70,
        permissions=DIRECT_MEMBER_PERMISSIONS,
    )

    MEMBER = ChatRole(
        id=5,
        name="member",
        level=10,
        permissions=MEMBER_PERMISSIONS,
    )

    VIEWER = ChatRole(
        id=6,
        name="viewer",
        level=1,
        permissions=VIEWER_PERMISSIONS,
    )

    @classmethod
    def get_all_chat_roles(cls) -> list[ChatRole]:
        return [role.value for role in cls]

    @classmethod
    def channel_staff_role_ids(cls) -> set[int]:
        return {cls.OWNER.value.id, cls.ADMIN.value.id, cls.EDITOR.value.id}

    @classmethod
    def channel_subscriber_role_ids(cls) -> set[int]:
        return {cls.VIEWER.value.id}
