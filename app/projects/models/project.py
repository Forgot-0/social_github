
from sqlalchemy import ARRAY, Integer, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin


class SetArrayString(TypeDecorator):
    impl = ARRAY(String())
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



class SetArrayInteger(TypeDecorator):
    impl = ARRAY(Integer())
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

class Project(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True)

    title: Mapped[str] = mapped_column(String())
    description: Mapped[str] = mapped_column(String)

    tags: Mapped[set[str]] = mapped_column(SetArrayString())
    urls: Mapped[set[str]] = mapped_column(SetArrayString())

    collaborators: Mapped[set[int]] = mapped_column(SetArrayInteger)

