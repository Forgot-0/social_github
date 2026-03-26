from dataclasses import dataclass

from sqlalchemy import Select, select

from app.core.db.repository import IRepository, CacheRepository
from app.rooms.models.role_chat import RoomRole


@dataclass
class RoomRoleRepository(IRepository[RoomRole], CacheRepository):
    _LIST_VERSION_KEY = "room_roles:list"

    async def create(self, role: RoomRole) -> None:
        self.session.add(role)

    async def get_by_id(self, role_id: int) -> RoomRole | None:
        stmt = select(RoomRole).where(RoomRole.id == role_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> RoomRole | None:
        stmt = select(RoomRole).where(RoomRole.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[RoomRole]:
        result = await self.session.execute(select(RoomRole))
        return list(result.scalars().all())

    def apply_relationship_filters(self, stmt: Select, filters) -> Select:
        return stmt
