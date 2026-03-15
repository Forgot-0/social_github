import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Callable

from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.core.services.auth.rbac import RBACManager
from app.profiles.commands.profiles.remove_contact import (
    RemoveContactToProfileCommand,
    RemoveContactToProfileCommandHandler
)
from app.profiles.exceptions import NotFoundProfileException
from app.profiles.models.profile import Profile
from app.profiles.repositories.profiles import ProfileRepository


@pytest.mark.integration
@pytest.mark.profiles
class TestRemoveContactFromProfileCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        profile_repository: ProfileRepository,
        rbac_manager: RBACManager,
    ) -> RemoveContactToProfileCommandHandler:
        return RemoveContactToProfileCommandHandler(
            session=db_session,
            profile_repository=profile_repository,
            rbac_manager=rbac_manager,
        )


    @pytest.mark.asyncio
    async def test_owner_can_remove_contact_success(
        self,
        persisted_profile_contact,
        user_jwt: UserJWTData,
        handler,
        profile_repository: ProfileRepository,
    ) -> None:
        profile = await persisted_profile_contact([("github", "https://github.com/testuser")])

        command = RemoveContactToProfileCommand(
            profile_id=profile.id,
            provider="github",
            user_jwt_data=user_jwt,
        )

        await handler.handle(command)

        updated = await profile_repository.get_by_id(profile.id)
        assert updated is not None
        assert all(
            contact.provider != "github"
            for contact in updated.contacts
        )

    @pytest.mark.asyncio
    async def test_remove_one_contact_keeps_others(
        self,
        persisted_profile_contact,
        user_jwt: UserJWTData,
        handler,
        profile_repository: ProfileRepository,
    ) -> None:
        profile = await persisted_profile_contact([
            ("github", "https://github.com/testuser"),
            ("linkedin", "https://linkedin.com/in/testuser"),
            ("twitter", "https://twitter.com/testuser")
        ])

        command = RemoveContactToProfileCommand(
            profile_id=profile.id,
            provider="github",
            user_jwt_data=user_jwt,
        )

        await handler.handle(command)

        updated = await profile_repository.get_by_id(profile.id)
        assert updated is not None
        assert all(
            contact.provider != "github"
            for contact in updated.contacts
        )
        assert any(
            contact.provider == "linkedin"
            for contact in updated.contacts
        )
        assert any(
            contact.provider != "twitter"
            for contact in updated.contacts
        )

    @pytest.mark.asyncio
    async def test_not_found_raises(
        self,
        user_jwt: UserJWTData,
        handler,
    ) -> None:
        command = RemoveContactToProfileCommand(
            profile_id=999999,
            provider="github",
            user_jwt_data=user_jwt,
        )

        with pytest.raises(NotFoundProfileException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_forbidden_if_not_owner_and_no_permission(
        self,
        persisted_profile_contact,
        make_user_jwt,
        handler,
    ) -> None:
        profile = await persisted_profile_contact([
            ("github", "https://github.com/testuser")
        ])

        command = RemoveContactToProfileCommand(
            profile_id=profile.id,
            provider="github",
            user_jwt_data=make_user_jwt(id="3", username="other_user"),
        )

        with pytest.raises(AccessDeniedException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_allowed_if_not_owner_but_has_permission(
        self,
        persisted_profile_contact,
        super_admin_user_jwt: UserJWTData,
        handler,
        profile_repository: ProfileRepository,
    ) -> None:
        profile = await persisted_profile_contact([
            ("twitter", "https://twitter.com/testuser")
        ])

        command = RemoveContactToProfileCommand(
            profile_id=profile.id,
            provider="twitter",
            user_jwt_data=super_admin_user_jwt,
        )

        await handler.handle(command)

        updated = await profile_repository.get_by_id(profile.id)
        assert updated is not None
        assert all(
            contact.provider != "twitter"
            for contact in updated.contacts
        )

    @pytest.mark.asyncio
    async def test_remove_non_existing_contact(
        self,
        persisted_profile: Profile,
        user_jwt: UserJWTData,
        handler,
        profile_repository: ProfileRepository,
    ) -> None:
        command = RemoveContactToProfileCommand(
            profile_id=persisted_profile.id,
            provider="github",
            user_jwt_data=user_jwt,
        )

        await handler.handle(command)

        updated = await profile_repository.get_by_id(persisted_profile.id)
        assert updated is not None
        assert len(updated.contacts) == 0
