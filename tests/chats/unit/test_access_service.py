import pytest

from app.chats.models.chat import Chat, ChatType
from app.chats.models.chat_members import ChatMember
from app.chats.models.chat_roles import ChatRole
from app.chats.models.permission import (
    OWNER_PERMISSIONS,
    ChatRolesEnum,
)
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager


def make_member(role: ChatRole, is_banned=False, is_muted=False) -> ChatMember:
    m = ChatMember()
    m.user_id = 1
    m.role_id = role.id
    m.is_banned = is_banned
    m.is_muted = is_muted
    m.is_muted = is_muted
    m.permissions_overrides = {}
    m.role = role
    return m


def make_jwt(permissions: list[str] | None = None, role: str = "user") -> UserJWTData:
    return UserJWTData(
        id="1", username="u", roles=[role],
        permissions=permissions or [], security_level=1,
    )


def make_chat(admin_only=False, slow_mode=0, permissions=None) -> Chat:
    chat = Chat.__new__(Chat)
    chat.type = ChatType.GROUP
    chat.admin_only = admin_only
    chat.slow_mode_seconds = slow_mode
    chat.permissions = permissions or {}
    chat.member_count = 3
    chat.name = "test"
    chat.description = None
    chat.is_public = False
    return chat


OWNER = ChatRolesEnum.OWNER.value
ADMIN = ChatRolesEnum.ADMIN.value
MEMBER_ROLE = ChatRolesEnum.MEMBER.value
VIEWER_ROLE = ChatRolesEnum.VIEWER.value


@pytest.mark.unit
@pytest.mark.chats
class TestChatAccessService:

    @pytest.fixture
    def service(self) -> ChatAccessService:
        return ChatAccessService(rbac_manager=RBACManager())

    @pytest.fixture
    def global_admin_jwt(self) -> UserJWTData:
        return UserJWTData(
            id="99", username="admin", roles=["system_admin"],
            permissions=[], security_level=9,
        )

    async def test_owner_has_all_permissions(self, service: ChatAccessService) -> None:
        member = make_member(OWNER)
        jwt = make_jwt()
        for perm in OWNER_PERMISSIONS:
            result = await service.has_permissions(jwt, member, {perm})
            assert result is True, f"owner should have permission: {perm}"

    async def test_banned_member_has_no_permissions(self, service: ChatAccessService) -> None:
        member = make_member(OWNER, is_banned=True)
        result = await service.has_permissions(make_jwt(), member, {"chat:get"})
        assert result is False

    async def test_muted_member_cannot_send(self, service: ChatAccessService) -> None:
        member = make_member(MEMBER_ROLE, is_muted=True)
        result = await service.has_permissions(make_jwt(), member, {"message:send"})
        assert result is False

    async def test_muted_member_can_still_read(self, service: ChatAccessService) -> None:
        member = make_member(MEMBER_ROLE, is_muted=True)
        result = await service.has_permissions(make_jwt(), member, {"message:read"})
        assert result is True

    async def test_global_admin_bypasses_all_checks(
        self, service: ChatAccessService, global_admin_jwt: UserJWTData
    ) -> None:
        banned_member = make_member(VIEWER_ROLE, is_banned=True)
        result = await service.has_permissions(global_admin_jwt, banned_member, {"chat:delete"})
        assert result is True

    async def test_permission_override_grants_extra_access(self, service: ChatAccessService) -> None:
        member = make_member(MEMBER_ROLE)
        member.permissions_overrides = {"message:delete": True}
        result = await service.has_permissions(make_jwt(), member, {"message:delete"})
        assert result is True

    async def test_permission_override_revokes_access(self, service: ChatAccessService) -> None:
        member = make_member(ADMIN)
        member.permissions_overrides = {"chat:update": False}
        result = await service.has_permissions(make_jwt(), member, {"chat:update"})
        assert result is False

    async def test_none_member_has_no_permissions(self, service: ChatAccessService) -> None:
        result = await service.has_permissions(make_jwt(), None, {"chat:get"})
        assert result is False

    async def test_member_can_send_in_normal_chat(self, service: ChatAccessService) -> None:
        member = make_member(MEMBER_ROLE)
        chat = make_chat()
        result = await service.can_send_message(make_jwt(), chat, member)
        assert result is True

    async def test_viewer_cannot_send(self, service: ChatAccessService) -> None:
        member = make_member(VIEWER_ROLE)
        chat = make_chat()
        result = await service.can_send_message(make_jwt(), chat, member)
        assert result is False

    async def test_admin_only_chat_blocks_regular_member(self, service: ChatAccessService) -> None:
        member = make_member(MEMBER_ROLE)
        chat = make_chat(admin_only=True)
        result = await service.can_send_message(make_jwt(), chat, member)
        assert result is False

    async def test_admin_only_chat_allows_staff(self, service: ChatAccessService) -> None:
        member = make_member(OWNER)
        chat = make_chat(admin_only=True)
        result = await service.can_send_message(make_jwt(), chat, member)
        assert result is True

    async def test_chat_level_send_disabled_blocks_non_staff(self, service: ChatAccessService) -> None:
        member = make_member(MEMBER_ROLE)
        chat = make_chat(permissions={"message:send": False})
        result = await service.can_send_message(make_jwt(), chat, member)
        assert result is False

    async def test_chat_level_send_disabled_allows_staff(self, service: ChatAccessService) -> None:
        member = make_member(OWNER)
        chat = make_chat(permissions={"message:send": False})
        result = await service.can_send_message(make_jwt(), chat, member)
        assert result is True

    async def test_owner_can_update_member(self, service: ChatAccessService) -> None:
        requester = make_member(OWNER)
        requester.id = 1
        target = make_member(MEMBER_ROLE)
        target.id = 2
        result = await service.update_member(make_jwt(), requester, target, {"member:kick"})
        assert result is True

    async def test_member_cannot_update_owner(self, service: ChatAccessService) -> None:
        requester = make_member(MEMBER_ROLE)
        requester.id = 2
        target = make_member(OWNER)
        target.id = 1
        result = await service.update_member(make_jwt(), requester, target, {"member:kick"})
        assert result is False

    async def test_cannot_update_self(self, service: ChatAccessService) -> None:
        member = make_member(OWNER)
        member.id = 1
        result = await service.update_member(make_jwt(), member, member, {"member:kick"})
        assert result is False
