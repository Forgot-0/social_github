from dataclasses import dataclass

from app.core.exceptions import ApplicationException


@dataclass(kw_only=True)
class NotFoundProfileException(ApplicationException):
    profile_id: int

    code: str = "NOT_FOUND_PROFILE"
    status: int = 404

    @property
    def message(self) -> str:
        return "Profile not found"

    @property
    def detail(self):
        return {"profile_id": self.profile_id}


@dataclass(kw_only=True)
class AlreadeExistProfileException(ApplicationException):
    code: str = "ALREADE_EXIST_PROFILE"
    status: int = 409

    @property
    def message(self) -> str:
        return "Profile already exist"


@dataclass(kw_only=True)
class TooLongSkillNameException(ApplicationException):
    name: str
    code: str = "TOO_LONG_SKILL_NAME"
    status: int = 400

    @property
    def message(self):
        return f"Too long skill name {self.name}"

    @property
    def detail(self):
        return {
            "skill_name": self.name
        }


@dataclass(kw_only=True)
class TooLongDisplayNameException(ApplicationException):
    name: str
    code: str = "TOO_LONG_DISPLAY_NAME"
    status: int = 400

    @property
    def message(self):
        return f"Too long display name {self.name}"

    @property
    def detail(self):
        return {
            "display_name": self.name
        }


@dataclass(kw_only=True)
class TooLongBioException(ApplicationException):
    bio: str
    code: str = "TOO_LONG_BIO"
    status: int = 400

    @property
    def message(self):
        return f"Too long bio {self.bio}"

    @property
    def detail(self):
        return {
            "bio": self.bio
        }


@dataclass(kw_only=True)
class AvatarNotImageType(ApplicationException):
    type_avatar: str

    code: str = "AVATAR_NOT_TYPE_IMAGE"
    status: int = 400

    @property
    def message(self):
        return f"Avatar must be image type(jpg, png, ...)"

    @property
    def detail(self):
        return {
            "type": self.type_avatar
        }
