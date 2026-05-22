from dataclasses import dataclass

from app.core.exceptions import ApplicationError


@dataclass(kw_only=True)
class NotFoundProfileException(ApplicationError):
    profile_id: int

    code: str = "NOT_FOUND_PROFILE"
    status: int = 404

    @property
    def message(self) -> str:
        return "Profile not found"

    @property
    def detail(self) -> dict:
        return {"profile_id": self.profile_id}


@dataclass(kw_only=True)
class AlreadeExistProfileException(ApplicationError):
    code: str = "ALREADE_EXIST_PROFILE"
    status: int = 409

    @property
    def message(self) -> str:
        return "Profile already exist"

    @property
    def detail(self) -> dict:
        return {}


@dataclass(kw_only=True)
class TooLongSkillNameException(ApplicationError):
    name: str
    code: str = "TOO_LONG_SKILL_NAME"
    status: int = 400

    @property
    def message(self) -> str:
        return f"Too long skill name {self.name}"

    @property
    def detail(self) -> dict:
        return {
            "skill_name": self.name
        }


@dataclass(kw_only=True)
class TooLongDisplayNameException(ApplicationError):
    name: str
    code: str = "TOO_LONG_DISPLAY_NAME"
    status: int = 400

    @property
    def message(self) -> str:
        return f"Too long display name {self.name}"

    @property
    def detail(self) -> dict:
        return {
            "display_name": self.name
        }


@dataclass(kw_only=True)
class TooLongBioException(ApplicationError):
    bio: str
    code: str = "TOO_LONG_BIO"
    status: int = 400

    @property
    def message(self) -> str:
        return f"Too long bio {self.bio}"

    @property
    def detail(self) -> dict:
        return {
            "bio": self.bio
        }


@dataclass(kw_only=True)
class AvatarNotImageType(ApplicationError):
    type_avatar: str

    code: str = "AVATAR_NOT_TYPE_IMAGE"
    status: int = 400

    @property
    def message(self) -> str:
        return "Avatar must be image type(jpg, png, ...)"

    @property
    def detail(self) -> dict:
        return {
            "type": self.type_avatar
        }
