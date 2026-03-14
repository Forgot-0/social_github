from sqlalchemy import String, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY

from app.projects.config import project_config



class SetArrayString(TypeDecorator):
    impl = ARRAY(String(project_config.MAX_LEN_TAG))
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, set):
            return list(v.lower() for v in value)
        return list(v.lower() for v in value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return set(value)

