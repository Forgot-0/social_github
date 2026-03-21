
class ChatKeys:

    @staticmethod
    def user_online(user_id: int) -> str:
        return f"presence:user:{user_id}"

    @staticmethod
    def unread_count(user_id: int, chat_id: int) -> str:
        return f"unread:{user_id}:{chat_id}"

    @staticmethod
    def last_read(user_id: int, chat_id: int) -> str:
        return f"lastread:{user_id}:{chat_id}"

    @staticmethod
    def chat_channel(chat_id: int) -> str:
        return f"chat:{chat_id}:channel"

    @staticmethod
    def user_channel(user_id) -> str:
        return f"user:{user_id}:channel"

    @staticmethod
    def rate_limit(user_id: int, action: str) -> str:
        return f"ratelimit:{action}:{user_id}"

    @staticmethod
    def chat_member_count(chat_id: int) -> str:
        return f"chat:{chat_id}:member_count"

    @staticmethod
    def chat_cache(chat_id: int) -> str:
        return f"cache:chat:{chat_id}"
