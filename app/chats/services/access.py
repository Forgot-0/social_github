from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

from app.chats.exceptions import NotChatMemberException
from app.chats.models.chat_members import ChatMember
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager


@dataclass
class PermissionContext:
    user_jwt_data: UserJWTData
    member: ChatMember | None
    must_permissions: set[str]


class PermissionPolicy(Protocol):
    async def check(self, context: PermissionContext) -> bool:
        ...


@dataclass
class RBACPolicy:
    rbac_manager: RBACManager

    async def check(self, context: PermissionContext) -> bool:
        if context.member and context.member.role.level <= 1:
            return True
        return self.rbac_manager.check_permission(context.user_jwt_data, {"chat:update"})


@dataclass
class BanPolicy:
    async def check(self, context: PermissionContext) -> bool:
        if context.member and context.member.is_banned:
            return False
        return True


@dataclass
class MemberPermissionPolicy:
    async def check(self, context: PermissionContext) -> bool:
        if not context.member:
            raise NotChatMemberException(chat_id=0, user_id=int(context.user_jwt_data.id))

        member_permissions = context.member.effective_permissions()
        for perm in context.must_permissions:
            if not member_permissions.get(perm, False):
                return False
        return True


@dataclass
class CompositePermissionPolicy:
    policies: list[PermissionPolicy]

    async def check(self, context: PermissionContext) -> bool:
        for policy in self.policies:
            if not await policy.check(context):
                return False
        return True


@dataclass
class ChatAccessService:
    rbac_policy: RBACPolicy
    ban_policy: BanPolicy
    member_permission_policy: MemberPermissionPolicy
    composite_policy: CompositePermissionPolicy

    def __post_init__(self):
        self.composite_policy = CompositePermissionPolicy([
            self.rbac_policy,
            self.ban_policy,
            self.member_permission_policy,
        ])

    async def can_update(
        self,
        user_jwt_data: UserJWTData,
        memeber: ChatMember | None,
        must_permissions: set[str]
    ) -> bool:
        context = PermissionContext(
            user_jwt_data=user_jwt_data,
            member=memeber,
            must_permissions=must_permissions
        )
        return await self.composite_policy.check(context)

    async def update_member(
        self,
        user_jwt_data: UserJWTData,
        requester: ChatMember | None,
        target: ChatMember,
        must_permissions: set[str]
    ) -> bool:
        if self.rbac_policy.rbac_manager.check_permission(
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
