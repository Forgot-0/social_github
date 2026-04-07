from enum import Enum
from typing import TYPE_CHECKING, Self
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import UUID, BigInteger, Boolean, Enum as SAEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.projects.config import project_config
from app.projects.exceptions import AlreadyMemberException, TooLongTagNameException
from app.projects.models.member import MembershipStatus
from app.projects.models.application import Application

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


    id: Mapped[PyUUID] = mapped_column(UUID, primary_key=True)
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

    project: Mapped["Project"] = relationship("Project", back_populates="positions")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="position", lazy="noload")

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
            raise AlreadyMemberException()

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
    def validate_skills(self, key, value):

        if len(value) != len(set(value)):
            raise ValueError("Duplicate skills are not allowed")

        for tag in value:
            if len(tag) > project_config.MAX_LEN_TAG:
                raise TooLongTagNameException(name=tag)

        return value
