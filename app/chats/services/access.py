from dataclasses import dataclass

from app.chats.models.chat import Chat
from app.chats.models.chat_members import ChatMember
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager


@dataclass
class ChatAccessService:
    rbac_manager: RBACManager

    def _has_global_chat_admin(self, user_jwt_data: UserJWTData) -> bool:
        return self.rbac_manager.check_permission(user_jwt_data, {"chat:update"})

    async def has_permissions(
        self,
        user_jwt_data: UserJWTData,
        member: ChatMember | None,
        must_permissions: set[str]
    ) -> bool:
        if self._has_global_chat_admin(user_jwt_data):
            return True

        if member is None or member.is_banned:
            return False

        if "message:send" in must_permissions and member.is_muted:
            return False

        member_permissions = member.effective_permissions()
        for perm in must_permissions:
            if not member_permissions.get(perm, False):
                return False

        return True

    async def can_send_message(
        self,
        user_jwt_data: UserJWTData,
        chat: Chat,
        member: ChatMember | None,
    ) -> bool:
        if self._has_global_chat_admin(user_jwt_data):
            return True

        if member is None or member.is_banned or member.is_muted:
            return False

        member_permissions = member.effective_permissions()
        if not member_permissions.get("message:send", False):
            return False

        if chat.admin_only and not (
            member.is_staff or member_permissions.get("message:send_admin_only", False)
        ):
            return False

        if (
            chat.permissions
            and chat.permissions.get("message:send") is False
            and not member.is_staff
        ):
            return False

        return True

    def can_bypass_slow_mode(self, member: ChatMember | None) -> bool:
        if member is None or member.is_banned:
            return False
        return member.can_bypass_slow_mode()

    async def update_member(
        self,
        user_jwt_data: UserJWTData,
        requester: ChatMember | None,
        target: ChatMember,
        must_permissions: set[str]
    ) -> bool:
        if self._has_global_chat_admin(user_jwt_data):
            return True

        if requester is None or requester.is_banned or requester.id == target.id:
            return False

        member_permissions = requester.effective_permissions()
        for perm in must_permissions:
            if not member_permissions.get(perm, False):
                return False

        return requester.role.level >= target.role.level
