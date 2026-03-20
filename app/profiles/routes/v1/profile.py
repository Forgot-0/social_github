from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query, Request, status

from app.core.api.builder import create_response
from app.core.api.rate_limiter import ConfigurableRateLimiter
from app.core.api.schemas import ORJSONResponse
from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData
from app.profiles.commands.profiles.add_contact import AddContactToProfileCommand
from app.profiles.commands.profiles.create import CreateProfileCommand
from app.profiles.commands.profiles.remove_contact import RemoveContactToProfileCommand
from app.profiles.commands.profiles.update import UpdateProfileCommand
from app.profiles.commands.profiles.update_avatar import UpdateProfileAvatrCommand
from app.profiles.dtos.profiles import AvatarPresignResponse, ProfileDTO
from app.profiles.exceptions import NotFoundProfileException
from app.profiles.queries.profiles.get_by_id import GetProfileByIdQuery
from app.profiles.queries.profiles.get_list import GetProfilesQuery
from app.profiles.queries.profiles.get_url import GetAvatrProfileUrlQuery
from app.profiles.schemas.profiles.requests import (
    AddContactProfileRequest,
    AvatarPreSignUrlRequest,
    AvatarUploadCompleteRequest,
    GetProfilesRequest,
    ProfileCreateRequest,
    ProfileUpdateRequest
)


router = APIRouter(route_class=DishkaRoute)

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED
)
async def create_profile(
    profile_request: ProfileCreateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData
) -> None:
    await mediator.handle_command(
        CreateProfileCommand(
            user_id=int(user_jwt_data.id),
            username=user_jwt_data.username,
            display_name=profile_request.display_name,
            bio=profile_request.bio,
            skills=profile_request.skills,
            date_birthday=profile_request.date_birthday,
        )
    )

@router.get(
    "/",
    status_code=status.HTTP_200_OK
)
async def get_profiles(
    mediator: FromDishka[BaseMediator],
    params: GetProfilesRequest = Query()
) -> PageResult[ProfileDTO]:
    return await mediator.handle_query(
        GetProfilesQuery(params.to_profile_filter())
    )

@router.put(
    "/{profile_id}",
    status_code=status.HTTP_200_OK,
    responses={
        404: create_response(NotFoundProfileException(profile_id=123))
    }
)
async def update_profile(
    profile_id: int,
    profile_request: ProfileUpdateRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData
) -> None:
    await mediator.handle_command(
        UpdateProfileCommand(
            profile_id=profile_id,
            specialization=profile_request.specialization,
            display_name=profile_request.display_name,
            bio=profile_request.bio,
            skills=profile_request.skills,
            date_birthday=profile_request.date_birthday,
            user_jwt_data=user_jwt_data
        )
    )

@router.get(
    "/{profile_id}",
    status_code=status.HTTP_200_OK,
    responses={
        404: create_response(NotFoundProfileException(profile_id=123))
    },
)
async def get_profile(
    profile_id: int,
    mediator: FromDishka[BaseMediator],
) -> ProfileDTO:
    return await mediator.handle_query(GetProfileByIdQuery(profile_id))

# Avatar
@router.post(
    "/avatar/presign",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(ConfigurableRateLimiter(times=4, seconds=5*60))]
)
async def get_avatar_presign_url(
    profile_request: AvatarPreSignUrlRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> AvatarPresignResponse:
    return await mediator.handle_query(
        GetAvatrProfileUrlQuery(
            user_id=int(user_jwt_data.id),
            file_name=profile_request.filename,
            content_type=profile_request.content_type,
            size=profile_request.size,
            user_jwt_data=user_jwt_data
        )
    )

@router.post(
    "/avatar/upload_complete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(ConfigurableRateLimiter(times=4, seconds=5*60))]
)
async def upload_avatar_complete(
    profile_request: AvatarUploadCompleteRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData
) -> ORJSONResponse:
    await mediator.handle_command(
        UpdateProfileAvatrCommand(
            key_base=profile_request.key_base,
            user_jwt_data=user_jwt_data
        )
    )
    return ORJSONResponse("OK")

# Contacts
@router.post(
    "/{profile_id}/contacts",
    status_code=status.HTTP_200_OK,
)
async def add_contact_profile(
    profile_id: int,
    profile_request: AddContactProfileRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData
) -> None:
    await mediator.handle_command(
        AddContactToProfileCommand(
            profile_id=profile_id,
            provider=profile_request.provider,
            contact=profile_request.contact,
            user_jwt_data=user_jwt_data
        )
    )

@router.delete(
    "/{profile_id}/{provide_contact}/delete",
    status_code=status.HTTP_200_OK,
)
async def remove_contact_profile(
    profile_id: int,
    provide_contact: str,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData
) -> None:
    await mediator.handle_command(
        RemoveContactToProfileCommand(
            profile_id=profile_id,
            provider=provide_contact,
            user_jwt_data=user_jwt_data
        )
    )

