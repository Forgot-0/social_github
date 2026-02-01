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
    def detail(self):
        return {"project_id": self.project_id}


@dataclass(kw_only=True)
class TooLongTagNameException(ApplicationException):
    name: str
    code: str = "TOO_LONG_TAG_NAME"
    status: int = 400

    @property
    def message(self):
        return f"Too long tag name {self.name}"

    @property
    def detail(self):
        return {
            "tag_name": self.name
        }


@dataclass(kw_only=True)
class NotFoundProjectRoleException(ApplicationException):
    role_id: int

    code: str = "NOT_FOUND_PROJECT_ROLE"
    status: int = 404

    @property
    def message(self) -> str:
        return "Project role not found"

    @property
    def detail(self):
        return {"role_id": self.role_id}

