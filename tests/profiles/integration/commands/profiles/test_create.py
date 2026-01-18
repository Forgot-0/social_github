import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.profiles.commands.profiles.create import CreateProfileCommand, CreateProfileCommandHanler
from app.profiles.exceptions import (
    AlreadeExistProfileException,
    TooLongBioException,
    TooLongDisplayNameException,
    TooLongSkillNameException
)
from app.profiles.repositories.profiles import ProfileRepository
from tests.profiles.integration.factories import ProfileCommandFactory


@pytest.mark.integration
@pytest.mark.profiles
class TestCreateCommand:
    @pytest.mark.asyncio
    async def test_create_success(
        self,
        db_session: AsyncSession,
        profile_repository: ProfileRepository
    ) -> None:
        handler = CreateProfileCommandHanler(
            session=db_session,
            profile_repository=profile_repository
        )
        cmd_data = ProfileCommandFactory.create_command(
            1, "test"
        )
        command = CreateProfileCommand(**cmd_data)
        await handler.handle(command)

        created_profile = await profile_repository.get_by_user_id(user_id=1)
        assert created_profile is not None
        assert created_profile.username == "test"
        assert created_profile.bio is None
        assert created_profile.display_name is None
        assert isinstance(created_profile.skills, set)
        assert created_profile.skills == set()

    @pytest.mark.asyncio
    async def test_create_duplicated(
        self,
        db_session: AsyncSession,
        profile_repository: ProfileRepository
    ) -> None:
        handler = CreateProfileCommandHanler(
            session=db_session,
            profile_repository=profile_repository
        )
        cmd_data = ProfileCommandFactory.create_command(
            1, "test"
        )
        command = CreateProfileCommand(**cmd_data)
        await handler.handle(command)

        with pytest.raises(AlreadeExistProfileException) as exc_info:
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_create_long_skill_name(
        self,
        db_session: AsyncSession,
        profile_repository: ProfileRepository
    ) -> None:
        handler = CreateProfileCommandHanler(
            session=db_session,
            profile_repository=profile_repository
        )
        cmd_data = ProfileCommandFactory.create_command(
            1, "test", skills={"1"*1024}
        )
        command = CreateProfileCommand(**cmd_data)
        with pytest.raises(TooLongSkillNameException) as exc_info:
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_create_long_display_name(
        self,
        db_session: AsyncSession,
        profile_repository: ProfileRepository
    ) -> None:
        handler = CreateProfileCommandHanler(
            session=db_session,
            profile_repository=profile_repository
        )
        cmd_data = ProfileCommandFactory.create_command(
            1, "test", display_name="ab"*1024
        )
        command = CreateProfileCommand(**cmd_data)
        with pytest.raises(TooLongDisplayNameException) as exc_info:
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_create_long_bio(
        self,
        db_session: AsyncSession,
        profile_repository: ProfileRepository
    ) -> None:
        handler = CreateProfileCommandHanler(
            session=db_session,
            profile_repository=profile_repository
        )
        cmd_data = ProfileCommandFactory.create_command(
            1, "test", bio="ab"*1024
        )
        command = CreateProfileCommand(**cmd_data)
        with pytest.raises(TooLongBioException) as exc_info:
            await handler.handle(command)
