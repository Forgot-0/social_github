from dataclasses import dataclass
from uuid import uuid4

from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.storage.dtos import ContentTypeFilter, UploadFilePost
from app.core.services.storage.service import StorageService
from app.profiles.config import profile_config
from app.profiles.dtos.profiles import AvatarPresignResponse


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

    async def handle(self, query: GetAvatrProfileUrlQuery) -> AvatarPresignResponse:
        key_base = f"avatars/{query.user_id}/{uuid4()}"

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

