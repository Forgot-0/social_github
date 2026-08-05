from enum import Enum
from typing import TYPE_CHECKING, Any, Self
from uuid import UUID, uuid4

from sqlalchemy import (
    UUID as SAUUID,
    BigInteger,
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.projects.config import project_config
from app.projects.exceptions import AlreadyMemberError, TooLongTagNameError
from app.projects.models.application import Application
from app.projects.models.member import MembershipStatus

if TYPE_CHECKING:
    from app.projects.models.project import Project


class PositionLocationType(Enum):
    remote = "remote"
    onsite = "onsite"
    hybrid = "hybrid"


class PositionLoad(Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Position(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "positions"
    __table_args__ = (
        Index("idx_positions_tags", "required_skills", postgresql_using="gin"),
    )


    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)

    required_skills: Mapped[list[str]] = mapped_column(
        ARRAY(String(project_config.MAX_LEN_TAG)),
        default=list
    )
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)

    location_type: Mapped[PositionLocationType] = mapped_column(
        SAEnum(PositionLocationType), nullable=False, server_default=PositionLocationType.remote.name
    )
    expected_load: Mapped[PositionLoad] = mapped_column(
        SAEnum(PositionLoad), nullable=False, server_default=PositionLoad.medium.name
    )

    project: Mapped[Project] = relationship("Project", lazy="selectin", back_populates="positions")
    applications: Mapped[list[Application]] = relationship("Application", lazy="selectin", back_populates="position")

    @classmethod
    def create(
        cls,
        project_id: int,
        title: str,
        description: str,
        required_skills: set[str],
        responsibilities: str | None = None,
        location_type: PositionLocationType = PositionLocationType.remote,
        expected_load: PositionLoad = PositionLoad.low,
    ) -> Self:
        instance = cls(
            id=uuid4(),
            project_id=project_id,
            title=title,
            description=description,
            required_skills=list(required_skills),
            responsibilities=responsibilities,
            location_type=location_type,
            expected_load=expected_load,
        )
        return instance

    def add_application(
        self, candidate_id: int, message: str | None
    ) -> None:
        member = self.project.get_memeber_by_user_id(candidate_id)
        if member and member.status != MembershipStatus.active:
            raise AlreadyMemberError

        self.applications.append(
            Application.create(
                project_id=self.project.id,
                position_id=self.id,
                candidate_id=candidate_id,
                message=message
            )
        )

    def close(self) -> None:
        self.is_open = False

    @validates("required_skills")
    def validate_skills(self, key: Any, value: list[str]) -> list[str]:

        if len(value) != len(set(value)):
            raise ValueError("Duplicate skills are not allowed")

        for tag in value:
            if len(tag) > project_config.MAX_LEN_TAG:
                raise TooLongTagNameError(name=tag)

        return value
