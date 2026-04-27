from dataclasses import dataclass
from datetime import datetime

from app.core.queries import BaseQuery
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True, kw_only=True)
class GetListChatUserQuery(BaseQuery):
    user_jwt_data: UserJWTData
    limit: int = 50
    after: datetime
    before: datetime
