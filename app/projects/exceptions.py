from dataclasses import dataclass

from app.core.exceptions import ApplicationError


@dataclass(kw_only=True)
class NotFoundProjectError(ApplicationError):
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
class NotFoundPositionError(ApplicationError):
    position_id: str

    code: str = "NOT_FOUND_POSITION"
    status: int = 404

    @property
    def message(self) -> str:
        return "Position not found"

    @property
    def detail(self) -> dict[str, str]:
        return {"position_id": self.position_id}


@dataclass(kw_only=True)
class NotFoundMemberError(ApplicationError):
    member_id: int

    code: str = "NOT_FOUND_MEMBER"
    status: int = 404

    @property
    def message(self) -> str:
        return "Member not found"

    @property
    def detail(self) -> dict[str, int]:
        return {"member_id": self.member_id}


@dataclass(kw_only=True)
class AlreadyMemberError(ApplicationError):
    code: str = "ALREADY_MEMBER"
    status: int = 409

    @property
    def message(self) -> str:
        return "Already member"

    @property
    def detail(self) -> dict:
        return {}

@dataclass
class NotPendingStatusApplicationError(ApplicationError):
    code: str = "NOT_PENDING_APPLICATION"
    status: int = 409

    @property
    def message(self) -> str:
        return ""

    @property
    def detail(self) -> dict:
        return {}


@dataclass(kw_only=True)
class TooLongTagNameError(ApplicationError):
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
class TooLongNameError(ApplicationError):
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
class NotValidMemberStatusError(ApplicationError):
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
class NotFoundProjectRoleError(ApplicationError):
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
class RoleAlreadyExsistsError(ApplicationError):
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
class MaxProjectsLimitExceededError(ApplicationError):
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
class MaxPositionsPerProjectLimitExceededError(ApplicationError):
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
class AlreadySlugProjectExistsError(ApplicationError):
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


@dataclass(kw_only=True)
class AccessDeniedProjectError(ApplicationError):
    code: str = "PROJECT_ACCESS_DENIED"
    status: int = 403

    @property
    def message(self) -> str:
        return "Insufficient project permissions"

    @property
    def detail(self) -> dict:
        return {}

