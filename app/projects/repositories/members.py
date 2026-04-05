
from dataclasses import dataclass

from sqlalchemy import Select

from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter
from app.projects.models.member import ProjectMembership


@dataclass
class MemberProjectRepository(IRepository[ProjectMembership], CacheRepository):
    _LIST_VERSION_KEY = "member:list"

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
