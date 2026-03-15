from typing import TYPE_CHECKING, Self
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import ARRAY, UUID, BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.projects.config import project_config
from app.projects.exceptions import TooLongTagNameException

if TYPE_CHECKING:
    from app.projects.models.project import Project


class Position(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "positions"

    id: Mapped[PyUUID] = mapped_column(UUID, primary_key=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    title: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)

    required_skills: Mapped[list[str]] = mapped_column(
        ARRAY(String(project_config.MAX_LEN_TAG)),
        default=list
    )
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)


    project: Mapped["Project"] = relationship("Project", back_populates="postions")

    @classmethod
    def create(
        cls, project_id: int, title: str, description: str,
        required_skills: set[str], 
    ) -> Self:
        instance = cls(
            id=uuid4(),
            project_id=project_id,
            title=title,
            description=description,
            required_skills=list(required_skills),
        )
        return instance

    @validates("required_skills")
    def validate_skills(self, key, value):

        if len(value) != len(set(value)):
            raise ValueError("Duplicate skills are not allowed")

        for tag in value:
            if len(tag) > project_config.MAX_LEN_TAG:
                raise TooLongTagNameException(name=tag)

        return value
