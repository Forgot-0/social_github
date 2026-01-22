from enum import Enum
from typing import TypedDict
from sqlalchemy import Integer, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.profiles.config import profile_config
from app.profiles.exceptions import (
    TooLongBioException,
    TooLongDisplayNameException,
    TooLongSkillNameException
)



class SetArray(TypeDecorator):
    impl = ARRAY(String(profile_config.MAX_LEN_SKILL_NAME))
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, set):
            return list(value)
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return set(value)


class SizeAvatar(int, Enum):
    SMALL = 32
    UPPER_SMALL = 64
    MEDIUM = 256
    LARGE = 512

class TypeImageAvatar(str, Enum):
    JPG = "jpg"
    WEBP = "webp"
    AVIF = "avif"


class Profile(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, unique=True)

    avatars: Mapped[dict[SizeAvatar, dict[TypeImageAvatar, str]]] = mapped_column(JSONB, default=dict())
    display_name: Mapped[str | None] = mapped_column(String(profile_config.MAX_LEN_DISPLAY_NAME), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(profile_config.MAX_LEN_BIO), nullable=True)

    skills: Mapped[set[str]] = mapped_column(SetArray())

    @classmethod
    def create(
        cls, user_id: int, username: str,
        display_name: str | None,
        bio: str | None,
        skills: set[str] | None = None,
    ) -> "Profile":
        instance = cls(
            username=username,
            user_id=user_id,
        )
        instance.change_display_name(display_name)
        instance.change_bio(bio)
        instance.update_skills(skills or set())

        return instance

    def change_display_name(self, name: str | None) -> None:
        if name and len(name) >= profile_config.MAX_LEN_DISPLAY_NAME:
            raise TooLongDisplayNameException(name=name)

        self.display_name = name

    def change_bio(self, bio: str | None) -> None:
        if bio and len(bio) >= profile_config.MAX_LEN_BIO:
            raise TooLongBioException(bio=bio)

        self.bio = bio

    def add_skill(self, skill: str) -> None:
        if len(skill) > profile_config.MAX_LEN_SKILL_NAME:
            raise TooLongSkillNameException(name=skill)

        self.skills.add(skill.lower())

    def update_skills(self, skills: set[str]) -> None:
        if any(len(skill) > profile_config.MAX_LEN_SKILL_NAME for skill in skills):
            raise TooLongSkillNameException(name=max(skills, key=lambda x: len(x)))

        self.skills = {skill.lower() for skill in skills}
