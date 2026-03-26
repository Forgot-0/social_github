from dataclasses import dataclass

from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager
from app.rooms.models.role_chat import RoomRole
from app.rooms.models.rooms import Room


@dataclass
class RoomAccessService:
    rbac_manager: RBACManager

    def can_update(
        self,
        user_jwt_data: UserJWTData,
        room: Room,
        must_permissions: set[str],
    ) -> bool:
        if self.rbac_manager.check_permission(user_jwt_data, {"room:update"}):
            return True
        if int(user_jwt_data.id) == room.created_by:
            return True
        member = room.get_member_by_id(int(user_jwt_data.id))
        if member is None:
            return False
        member_perms = member.effective_permissions()
        return all(member_perms.get(perm, False) for perm in must_permissions)

    def can_member(
        self,
        user_jwt_data: UserJWTData,
        room: Room,
        must_permissions: set[str],
        role: RoomRole,
    ) -> bool:
        if self.rbac_manager.check_permission(user_jwt_data, {"room:update"}):
            return True

        if int(user_jwt_data.id) == room.created_by:
            return True

        member = room.get_member_by_id(int(user_jwt_data.id))

        if member is None:
            return False

        member_perms = member.effective_permissions()
        if not all(member_perms.get(perm, False) for perm in must_permissions):
            return False

        return member.role.level > role.level

    def can_manage_member(
        self,
        user_jwt_data: UserJWTData,
        room: Room,
        must_permissions: set[str],
        target_role: RoomRole,
    ) -> bool:
        if self.rbac_manager.check_permission(user_jwt_data, {"room:admin"}):
            return True

        if int(user_jwt_data.id) == room.created_by:
            return True

        member = room.get_member_by_id(int(user_jwt_data.id))
        if member is None:
            return False

        member_perms = member.effective_permissions()
        if not all(member_perms.get(perm, False) for perm in must_permissions):
            return False

        return member.role.level > target_role.level

    def is_member(self, user_jwt_data: UserJWTData, room: Room) -> bool:
        return room.get_member_by_id(int(user_jwt_data.id)) is not None