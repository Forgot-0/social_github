from dataclasses import dataclass

from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.dtos.members import MemberDTO
from app.projects.filters.memebers import MemebrFilter
from app.projects.models.member import MembershipStatus, ProjectMembership
from app.projects.repositories.members import MemberProjectRepository
from app.core.db.repository import PageResult


@dataclass(frozen=True)
class GetProfileInvitesQuery(BaseQuery):
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class GetProfileInvitesQueryHandler(BaseQueryHandler[GetProfileInvitesQuery, PageResult[MemberDTO]]):
    memebr_repository: MemberProjectRepository

    async def handle(self, query: GetProfileInvitesQuery) -> PageResult[MemberDTO]:
        return await self.memebr_repository.cache_paginated(
            MemberDTO, self._handle, ttl=400,
            query=query
        )

    async def _handle(self, query: GetProfileInvitesQuery) -> PageResult[MemberDTO]:
        filters = MemebrFilter(
            member_id=int(query.user_jwt_data.id),
            status=MembershipStatus.invited
        )
        page = await self.memebr_repository.find_by_filter(ProjectMembership, filters=filters)
        return PageResult(
            items=[MemberDTO.model_validate(project.to_dict()) for project in page.items],
            total=page.total,
            page=page.page,
            page_size=page.page_size
        )
