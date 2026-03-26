from dataclasses import dataclass

from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager
from app.rooms.models.rooms import Room


@dataclass
class RoomAccessService:
    rbac_manager: RBACManager

    async def can_update(
        self,
        user_jwt_data: UserJWTData,
        room: Room,
        must_permissions: set[str]
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"room:update"}
        ): return True

        if int(user_jwt_data.id) == room.created_by:
            return True

        memeber = room.get_member_by_id(int(user_jwt_data.id))
        if memeber is None:
            return False

        memeber_permissions = memeber.effective_permissions()
        for perm in must_permissions:
            if not memeber_permissions.get(perm, False):
                return False

        return True
