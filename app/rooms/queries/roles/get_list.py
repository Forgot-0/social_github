from dataclasses import dataclass

from app.core.queries import BaseQuery, BaseQueryHandler
from app.rooms.dtos.rooms import RoleDTO
from app.rooms.repositories.roles import RoomRoleRepository


@dataclass(frozen=True)
class GetRolesQuery(BaseQuery):
    pass


@dataclass(frozen=True)
class GetRolesQueryHandler(BaseQueryHandler[GetRolesQuery, list[RoleDTO]]):
    room_role_repository: RoomRoleRepository

    async def handle(self, query: GetRolesQuery) -> list[RoleDTO]:
        roles = await self.room_role_repository.get_all()
        return [RoleDTO.model_validate(**r.to_dict()) for r in roles]
