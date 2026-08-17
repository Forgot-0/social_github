from dataclasses import dataclass

from app.core.db.repository import CacheRepository, IRepository
from app.projects.models.member import ProjectMembership


@dataclass
class MemberProjectRepository(IRepository[ProjectMembership], CacheRepository):
    _LIST_VERSION_KEY = "member:list"
