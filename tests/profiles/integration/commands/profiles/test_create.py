import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.profiles.commands.profiles.create import CreateProfileCommand, CreateProfileCommandHanler
from app.profiles.exceptions import (
    AlreadeExistProfileException,
    TooLongBioException,
    TooLongDisplayNameException,
    TooLongSkillNameException,
)
from app.profiles.repositories.profiles import ProfileRepository
from tests.profiles.integration.factories import ProfileCommandFactory


@pytest.mark.integration
@pytest.mark.profiles
@pytest.mark.asyncio
class TestCreateCommand:
    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        profile_repository: ProfileRepository,
    ) -> CreateProfileCommandHanler:
        return CreateProfileCommandHanler(
            session=db_session,
            profile_repository=profile_repository,
        )

    async def test_create_success(
        self,
        profile_repository: ProfileRepository,
        handler: CreateProfileCommandHanler,
    ) -> None:
        cmd_data = ProfileCommandFactory.create_command(
            1, "test"
        )
        command = CreateProfileCommand(**cmd_data)
        await handler.handle(command)

        created_profile = await profile_repository.get_by_id(profile_id=1)

        assert created_profile is not None
        assert created_profile.username == "test"
        assert created_profile.bio is None
        assert created_profile.display_name is None
        assert isinstance(created_profile.skills, list)
        assert created_profile.skills == list()

    async def test_create_duplicated(
        self,
        handler: CreateProfileCommandHanler,
    ) -> None:
        cmd_data = ProfileCommandFactory.create_command(
            1, "test"
        )
        command = CreateProfileCommand(**cmd_data)
        await handler.handle(command)

        with pytest.raises(AlreadeExistProfileException):
            await handler.handle(command)

    async def test_create_long_skill_name(
        self,
        handler: CreateProfileCommandHanler,
    ) -> None:
        cmd_data = ProfileCommandFactory.create_command(
            1, "test", skills={"1" * 1024}
        )
        command = CreateProfileCommand(**cmd_data)
        with pytest.raises(TooLongSkillNameException):
            await handler.handle(command)

    async def test_create_long_display_name(
        self,
        handler: CreateProfileCommandHanler,
    ) -> None:
        cmd_data = ProfileCommandFactory.create_command(
            1, "test", display_name="ab" * 1024
        )
        command = CreateProfileCommand(**cmd_data)
        with pytest.raises(TooLongDisplayNameException):
            await handler.handle(command)

    async def test_create_long_bio(
        self,
        handler: CreateProfileCommandHanler,
    ) -> None:
        cmd_data = ProfileCommandFactory.create_command(
            1, "test", bio="ab" * 1024
        )
        command = CreateProfileCommand(**cmd_data)
        with pytest.raises(TooLongBioException):
            await handler.handle(command)
