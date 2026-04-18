from dataclasses import dataclass

from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.storage.dtos import ContentTypeFilter, UploadFilePost
from app.core.services.storage.service import StorageService
from app.profiles.config import profile_config
from app.profiles.dtos.profiles import AvatarPresignResponse
from app.profiles.repositories.profiles import ProfileRepository


@dataclass(frozen=True)
class GetAvatrProfileUrlQuery(BaseQuery):
    file_name: str
    size: int
    content_type: str
    user_id: int
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class GetAvatrProfileUrlQueryHandler(BaseQueryHandler[GetAvatrProfileUrlQuery, AvatarPresignResponse]):
    storage_service: StorageService
    profile_repository: ProfileRepository

    async def handle(self, query: GetAvatrProfileUrlQuery) -> AvatarPresignResponse:
        return await self.profile_repository.cache(
            AvatarPresignResponse, self._handle, ttl=90,
            query=query
        )

    async def _handle(self, query: GetAvatrProfileUrlQuery) -> AvatarPresignResponse:
        key_base = f"avatars/{query.user_id}"

        result = await self.storage_service.upload_post_file(
            UploadFilePost(
                bucket_name=profile_config.AVATAR_BUCKET,
                file_key=f"{key_base}/original",
                expires=100,
                size_upper_limit=profile_config.AVATAR_MAX_SIZE,
                content_type=ContentTypeFilter(text="image/", equals=False)
            )
        )
        return AvatarPresignResponse(
            url=result.url,
            fields=result.fields,
            key_base=key_base
        )
