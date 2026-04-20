import base64
from dataclasses import dataclass
from datetime import datetime

from app.chats.dtos.chats import ChatListCursorPageDTO, ChatListItemDTO
from app.chats.repositories.chat import ChatRepository
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True)
class GetChatsCursorQuery(BaseQuery):
    user_jwt_data: UserJWTData
    limit: int = 20
    cursor: str | None = None


@dataclass(frozen=True)
class GetChatsCursorQueryHandler(BaseQueryHandler[GetChatsCursorQuery, ChatListCursorPageDTO]):
    chat_repository: ChatRepository

    def _decode_cursor(self, cursor: str | None) -> tuple[datetime, int] | tuple[None, None]:
        if not cursor:
            return None, None
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts_str, chat_id_str = raw.split("|", 1)
        return datetime.fromisoformat(ts_str), int(chat_id_str)

    def _encode_cursor(self, activity_at: datetime, chat_id: int) -> str:
        payload = f"{activity_at.isoformat()}|{chat_id}"
        return base64.urlsafe_b64encode(payload.encode()).decode()

    async def handle(self, query: GetChatsCursorQuery) -> ChatListCursorPageDTO:
        user_id = int(query.user_jwt_data.id)
        cursor_activity_at, cursor_chat_id = self._decode_cursor(query.cursor)
        limit = min(query.limit, 100)

        rows = await self.chat_repository.get_user_chats_cursor(
            user_id=user_id,
            limit=limit,
            cursor_activity_at=cursor_activity_at,
            cursor_chat_id=cursor_chat_id,
        )
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [
            ChatListItemDTO.model_validate(chat.to_dict())
            for chat in rows
        ]

        next_cursor = None
        if has_more and rows and rows[-1].last_activity_at is not None:
            next_cursor = self._encode_cursor(rows[-1].last_activity_at, rows[-1].id)

        return ChatListCursorPageDTO(items=items, next_cursor=next_cursor, has_more=has_more)
