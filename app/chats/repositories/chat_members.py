from dataclasses import dataclass

from app.chats.models.chat_members import ChatMember
from app.core.db.repository import CacheRepository, IRepository


@dataclass
class ChatMembersRepository(IRepository[ChatMember], CacheRepository):
    _LIST_VERSION_KEY = "chat_members:list"


