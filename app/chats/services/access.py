from dataclasses import dataclass

from app.chats.models.chat_members import ChatMember
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager


@dataclass
class ChatAccessService:
    rbac_manager: RBACManager

    async def has_permissions(
        self,
        user_jwt_data: UserJWTData,
        member: ChatMember | None,
        must_permissions: set[str]
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"chat:update"}
        ): 
            return True

        if member is None:
            return False

        member_permissions = member.effective_permissions()
        for perm in must_permissions:
            if not member_permissions.get(perm, False):
                return False

        return True

    async def update_member(
        self,
        user_jwt_data: UserJWTData,
        requester: ChatMember | None,
        target: ChatMember,
        must_permissions: set[str]
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"chat:update"}
        ): 
            return True

        if requester is None or requester.is_banned or requester.id == target.id:
            return False

        member_permissions = requester.effective_permissions()
        for perm in must_permissions:
            if not member_permissions.get(perm, False):
                return False

        return requester.role.level >= target.role.level