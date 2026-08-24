class ChatKeys:
    _NAMESPACE = "chat:v1:"

    @staticmethod
    def presence_last_seen_zset() -> str:
        return f"{ChatKeys._NAMESPACE}presence:last_seen"

    @staticmethod
    def user_channel(user_id: int) -> str:
        return f"{ChatKeys._NAMESPACE}user:{user_id}:channel"


class WebsocketKeys:
    @staticmethod
    def user_route_key(user_id: int) -> str:
        return f"ws:route:user:{int(user_id)}"

    @staticmethod
    def gateway_route_key(gateway_id: str) -> str:
        return f"ws:route:gateway:{gateway_id}"

    @staticmethod
    def connection_key(connection_id: str) -> str:
        return f"ws:conn:{connection_id}"

    @staticmethod
    def gateway_stream_key(gateway_id: str) -> str:
        return f"ws:gateway:{gateway_id}:stream"

    @staticmethod
    def active_subscription_key(chat_id: str) -> str:
        return f"ws:sub:chat:{chat_id}"

    @staticmethod
    def connection_subscription_key(connection_id: str, chat_id: str) -> str:
        return f"ws:sub:conn:{connection_id}:{chat_id}"

    @staticmethod
    def active_subscription_route(user_id: int, gateway_id: str, connection_id: str) -> str:
        return f"{int(user_id)}:{gateway_id}:{connection_id}"
