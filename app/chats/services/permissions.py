from dataclasses import dataclass

from app.chats.models.chat_members import ChatMember, MemberRole
from app.chats.models.permission import ROLE_PERMISSIONS, Permission
from app.chats.repositories.chat_members import ChatMembersRepository
from app.core.services.auth.exceptions import AccessDeniedException
from app.core.services.auth.rbac import RBACManager


@dataclass
class ChatPermissionService:
    rbac_manager: RBACManager
    chat_memeber_repository: ChatMembersRepository

    def has_permission(self, role: MemberRole, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(role, set())

    async def require_membership(
        self,
        user_id: int,
        chat_id: int,
    ) -> ChatMember:
        member = await self.chat_memeber_repository.get_memeber_by_chat(user_id, chat_id, with_role=True)
        if member is None or member.is_banned:
            raise AccessDeniedException(need_permissions={""})
        return member

    async def require_permission(
        self,
        user_id: int,
        chat_id: int,
        permission: Permission,
    ) -> ChatMember:
        member = await self.require_membership(user_id, chat_id)
        if not self.has_permission(member.role, permission):
            raise AccessDeniedException(need_permissions={"permission.name"})
        return member

    def can_change_role(self, actor_role: MemberRole, target_role: MemberRole, new_role: MemberRole) -> bool:
        hierarchy = {MemberRole.VIEWER: 0, MemberRole.MEMBER: 1, MemberRole.ADMIN: 2, MemberRole.OWNER: 3}
        actor_level  = hierarchy[actor_role]
        target_level = hierarchy[target_role]
        new_level    = hierarchy[new_role]
    
        if target_level >= actor_level:
            return False

        if new_level >= actor_level:
            return False
        return True

    def can_remove_member(self, actor_role: MemberRole, target_role: MemberRole) -> bool:
        hierarchy = {MemberRole.VIEWER: 0, MemberRole.MEMBER: 1, MemberRole.ADMIN: 2, MemberRole.OWNER: 3}
        return hierarchy[actor_role] > hierarchy[target_role]
    
