import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import AccessDeniedException
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager
from app.profiles.commands.profiles.update import UpdateProfileCommand, UpdateProfileCommandHandler
from app.profiles.exceptions import NotFoundProfileException
from app.profiles.models.profile import Profile
from app.profiles.repositories.profiles import ProfileRepository
from tests.profiles.integration.factories import ProfileCommandFactory



@pytest.mark.integration
@pytest.mark.profiles
class TestUpdateProfileHandler:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "payload, expected",
        [
            (
                ProfileCommandFactory.update_command(
                    display_name="new_name", bio="new bio", skills={"A", "b"}
                ),
                {"display_name": "new_name", "bio": "new bio", "skills": {"a", "b"}},
            ),
            (
                ProfileCommandFactory.update_command(display_name="only_name"),
                {"display_name": "only_name", "bio": None, "skills": set()},
            ),
            (
                ProfileCommandFactory.update_command(skills=set()),
                {"display_name": None, "bio": None, "skills": set()},
            ),
        ],
    )
    async def test_owner_can_update_profile(
        self,
        persisted_profile: Profile,
        user_jwt: UserJWTData,
        handler_factory,
        profile_repository: ProfileRepository,
        payload,
        expected,
    ) -> None:
        command = UpdateProfileCommand(
            profile_id=persisted_profile.id,
            user_jwt_data=user_jwt,
            **payload,
        )

        handler = handler_factory()
        await handler.handle(command)

        updated = await profile_repository.get_by_id(persisted_profile.id)
        assert updated is not None
        print(updated.to_dict(), expected)
        assert updated.display_name == expected["display_name"]
        assert updated.bio == expected["bio"]
        assert updated.skills == expected["skills"]

    @pytest.mark.asyncio
    async def test_not_found_raises(self, db_session: AsyncSession, handler_factory, user_jwt):
        command = UpdateProfileCommand(
            profile_id=999999,
            user_jwt_data=user_jwt,
            display_name="x",
            bio=None,
            skills=None
        )
        handler = handler_factory()

        with pytest.raises(NotFoundProfileException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_forbidden_if_not_owner_and_no_permission(
        self,
        persisted_profile: Profile,
        make_user_jwt,
        handler_factory,
    ) -> None:

        command = UpdateProfileCommand(
            profile_id=persisted_profile.id,
            user_jwt_data=make_user_jwt(id="3", username="other_user"),
            **ProfileCommandFactory.update_command(display_name="bad"),
        )

        handler = handler_factory()

        with pytest.raises(AccessDeniedException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_allowed_if_not_owner_but_has_permission(
        self,
        persisted_profile: Profile,
        admin_user_jwt: UserJWTData,
        handler_factory,
        profile_repository: ProfileRepository,
    ) -> None:

        command = UpdateProfileCommand(
            profile_id=persisted_profile.id,
            user_jwt_data=admin_user_jwt,
            **ProfileCommandFactory.update_command(display_name="admin_updated", bio="ok", skills={"x"}),
        )

        handler = handler_factory()
        await handler.handle(command)

        updated = await profile_repository.get_by_id(persisted_profile.id)
        assert updated
        assert updated.display_name == "admin_updated"
        assert updated.bio == "ok"
        assert updated.skills == {"x"}