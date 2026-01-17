from enum import Enum
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableSet


from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin



class SkillLevel(str, Enum):
    NONE = "none"


class Profile(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    skills: Mapped[set[str]] = mapped_column(MutableSet.as_mutable(ARRAY(String(30))))

    @classmethod
    def create(
        cls, user_id: int,
        display_name: str | None,
        bio: str | None,
        skills: set[str] | None = None,
    ) -> "Profile":
        instance = cls(
            user_id=user_id,
            display_name=display_name,
            bio=bio,
            skills=skills or set()
        )
        return instance

    def change_display_name(self, name: str) -> None:
        if len(name) >= 100:
            raise

        self.display_name = name

    def add_skill(self, skill: str) -> None:
        if len(skill) > 30:
            raise

        self.skills.add(skill)

    def remove_skill(self, skill: str) -> None:
        if skill not in self.skills:
            raise

        self.skills.remove(skill)

    def set_new_avatar(self, avatar_url: str) -> None:
        self.avatar_url = avatar_url
