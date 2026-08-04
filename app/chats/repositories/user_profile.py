from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert

from app.chats.models.profile import ChatUserProfile
from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter
from app.core.utils import now_utc


@dataclass
class ChatUserProfileRepository(IRepository[ChatUserProfile], CacheRepository):

    async def get_by_ids(self, user_ids: list[int]) -> list[ChatUserProfile]:

        stmt = select(ChatUserProfile).where(ChatUserProfile.user_id.in_(user_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: int) -> ChatUserProfile | None:
        stmt = select(ChatUserProfile).where(ChatUserProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def upsert(
        self,
        user_id: int,
        username: str,
        display_name: str | None,
        avatars: dict[str, Any] | None,
        revision: datetime,
    ) -> bool:
        now = now_utc()
        stmt = (
            insert(ChatUserProfile)
            .values(
                user_id=user_id,
                username=username,
                display_name=display_name,
                avatars=avatars or {},
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=[ChatUserProfile.user_id],
                set_={
                    "username": username,
                    "display_name": display_name,
                    "avatars": avatars or {},
                    "updated_at": now,
                },
                where=(
                    (ChatUserProfile.updated_at < revision)
                ),
            )
            .returning(ChatUserProfile.user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() is not None

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
