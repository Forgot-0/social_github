from dataclasses import dataclass

from app.chats.dtos.websocket import WSConnection
from app.chats.schemas.ws import WSClientOp
from app.core.commands import BaseCommand, BaseCommandHandler


@dataclass(frozen=True)
class PingCommand(BaseCommand):
    conn: WSConnection
    op: WSClientOp = WSClientOp.PING


@dataclass(frozen=True)
class PingCommandHandler(BaseCommandHandler[PingCommand, None]):
    async def handle(self, command: PingCommand) -> None:
        command.conn.try_send({
            "type": "ws.pong",
            "payload": {},
        })

