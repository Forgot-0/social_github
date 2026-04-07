from dataclasses import dataclass

from app.core.exceptions import ApplicationException


@dataclass(kw_only=True)
class NotFoundProjectException(ApplicationException):
    project_id: int

    code: str = "NOT_FOUND_PROJECT"
    status: int = 404

    @property
    def message(self) -> str:
        return "Project not found"

    @property
    def detail(self) -> dict[str, int]:
        return {"project_id": self.project_id}


@dataclass(kw_only=True)
class NotFoundPositionException(ApplicationException):
    position_id: str

    code: str = "NOT_FOUND_POSTION"
    status: int = 404

    @property
    def message(self) -> str:
        return "Position not found"

    @property
    def detail(self) -> dict[str, str]:
        return {"position_id": self.position_id}


@dataclass(kw_only=True)
class NotFoundMemberException(ApplicationException):
    memebr_id: int

    code: str = "NOT_FOUND_MEMBER"
    status: int = 404

    @property
    def message(self) -> str:
        return "Member not found"

    @property
    def detail(self) -> dict[str, int]:
        return {"memebr_id": self.memebr_id}


@dataclass(kw_only=True)
class AlreadyMemberException(ApplicationException):
    code: str = "ALREADY_MEMBER"
    status: int = 409

    @property
    def message(self) -> str:
        return "Already member"

    @property
    def detail(self) -> dict:
        return {}


@dataclass(kw_only=True)
class TooLongTagNameException(ApplicationException):
    name: str
    code: str = "TOO_LONG_TAG_NAME"
    status: int = 400

    @property
    def message(self) -> str:
        return f"Too long tag name {self.name}"

    @property
    def detail(self) -> dict[str, str]:
        return {
            "tag_name": self.name
        }


@dataclass(kw_only=True)
class TooLongNameException(ApplicationException):
    name: str
    code: str = "TOO_LONG_NAME"
    status: int = 400

    @property
    def message(self) -> str:
        return f"Too long name {self.name}"

    @property
    def detail(self) -> dict[str, str]:
        return {
            "name": self.name
        }


@dataclass(kw_only=True)
class NotValidMemberStatusException(ApplicationException):
    member_status: str
    action: str

    code: str = "NOT_VALID_MEMBER_STATUS"
    status: int = 404

    @property
    def message(self) -> str:
        return "Not valid member status"

    @property
    def detail(self) -> dict[str, str]:
        return {"status": self.member_status, "action": self.action}


@dataclass(kw_only=True)
class NotFoundProjectRoleException(ApplicationException):
    role_id: int

    code: str = "NOT_FOUND_PROJECT_ROLE"
    status: int = 404

    @property
    def message(self) -> str:
        return "Project role not found"

    @property
    def detail(self) -> dict[str, int]:
        return {"role_id": self.role_id}


@dataclass(kw_only=True)
class RoleAlreadyExsistsException(ApplicationException):
    role_name: str

    code: str = "ROLE_ALREADY_EXISTS"
    status: int = 409

    @property
    def message(self) -> str:
        return "Role alredy exisist"

    @property
    def detail(self) -> dict[str, str]:
        return {"name": self.role_name}


@dataclass(kw_only=True)
class MaxProjectsLimitExceededException(ApplicationException):
    owner_id: int
    limit: int

    code: str = "MAX_PROJECTS_LIMIT_EXCEEDED"
    status: int = 400

    @property
    def message(self) -> str:
        return "Maximum number of projects reached"

    @property
    def detail(self) -> dict[str, int]:
        return {
            "owner_id": self.owner_id,
            "limit": self.limit,
        }


@dataclass(kw_only=True)
class MaxPositionsPerProjectLimitExceededException(ApplicationException):
    project_id: int
    limit: int

    code: str = "MAX_POSITIONS_PER_PROJECT_LIMIT_EXCEEDED"
    status: int = 400

    @property
    def message(self) -> str:
        return "Maximum number of positions for project reached"

    @property
    def detail(self) -> dict[str, int]:
        return {
            "project_id": self.project_id,
            "limit": self.limit,
        }

@dataclass(kw_only=True)
class AlreadySlugProjectExistsException(ApplicationException):
    slug: str
    code: str = "ALREADY_EXISTS"
    status: int = 409

    @property
    def message(self) -> str:
        return "This slug already exists"

    @property
    def detail(self) -> dict[str, str]:
        return {
            "slug": self.slug,
        }
