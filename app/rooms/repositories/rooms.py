from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from app.core.db.repository import CacheRepository, IRepository
from app.rooms.filters.rooms import RoomFilter
from app.rooms.models.room_member import RoomMember
from app.rooms.models.rooms import Room, RoomBan


@dataclass
class RoomRepository(IRepository[Room], CacheRepository):
    _LIST_VERSION_KEY = "rooms:list"

    async def create(self, room: Room) -> None:
        self.session.add(room)

    async def get_by_slug(self, slug: str) -> Room | None:
        stmt = (
            select(Room)
            .where(Room.slug == slug, Room.deleted_at.is_(None))
            .options(
                selectinload(Room.members).selectinload(RoomMember.role),
                selectinload(Room.bans),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, slug: str) -> bool:
        stmt = select(Room.slug).where(Room.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    def apply_relationship_filters(self, stmt: Select, filters: RoomFilter) -> Select:
        return stmt

    async def get_member(self, slug: str, user_id: int) -> RoomMember | None:
        stmt = (
            select(RoomMember)
            .where(
                RoomMember.room_slug == slug,
                RoomMember.user_id == user_id,
            )
            .options(selectinload(RoomMember.role))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_ban(self, slug: str, user_id: int) -> RoomBan | None:
        stmt = select(RoomBan).where(
            RoomBan.room_slug == slug, RoomBan.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_ban(self, ban: RoomBan) -> None:
        self.session.add(ban)

    async def delete_ban(self, ban: RoomBan) -> None:
        await self.session.delete(ban)
