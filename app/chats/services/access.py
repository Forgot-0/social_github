from dataclasses import dataclass

from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager
from app.chats.models.chat_members import ChatMember


@dataclass
class ChatAccessService:
    rbac_manager: RBACManager

    def can_update(
        self,
        user_jwt_data: UserJWTData,
        memeber: ChatMember,
        must_permissions: set[str]
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"chat:update"}
        ): return True

        if memeber.is_banned:
            return False

        memeber_permissions = memeber.effective_permissions()
        for perm in must_permissions:
            if not memeber_permissions.get(perm, False):
                return False

        return True

    def update_member(
        self,
        user_jwt_data: UserJWTData,
        requester: ChatMember,
        target: ChatMember,
        must_permissions: set[str] 
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"chat:update"}
        ): return True

        if requester.is_banned:
            return False

        memeber_permissions = requester.effective_permissions()
        for perm in must_permissions:
            if not memeber_permissions.get(perm, False):
                return False

        if requester.role.level < target.role.level:
            return False
        return True
