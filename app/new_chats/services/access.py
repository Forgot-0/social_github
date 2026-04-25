from dataclasses import dataclass

from app.chats.models.chat_members import ChatMember
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager


@dataclass
class ChatAccessService:
    rbac_manager: RBACManager

    async def can_update(
        self,
        user_jwt_data: UserJWTData,
        memeber: ChatMember | None,
        must_permissions: set[str]
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"chat:update"}
        ): 
            return True

        if memeber is None:
            return False

        memeber_permissions = memeber.effective_permissions()
        for perm in must_permissions:
            if not memeber_permissions.get(perm, False):
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

        if requester is None:
            return False

        if requester.is_banned:
            return False

        memeber_permissions = requester.effective_permissions()
        for perm in must_permissions:
            if not memeber_permissions.get(perm, False):
                return False

        if requester.role.level < target.role.level:
            return False
        return True
