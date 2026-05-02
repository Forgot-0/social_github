from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import orjson
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, WebSocket
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect

from app.chats.config import chat_config
from app.chats.dtos.messages import MessageDTO
from app.chats.dtos.websocket import WSConnection
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.schemas.ws import WSClientCommand, WSClientOp
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import InvalidTokenException
from app.core.services.auth.jwt_manager import JWTManager
from app.core.utils import now_utc
from app.core.websockets.base import BaseConnectionManager

router = APIRouter()
logger = logging.getLogger(__name__)


def _now() -> str:
    return now_utc().isoformat()


def _extract_ws_token(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token") or websocket.query_params.get("access_token")
    if token:
        return token

    authorization = websocket.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()

    # Useful for browser clients that pass token via subprotocol, e.g.
    # new WebSocket(url, ["chat.v1", "bearer.<jwt>"])
    protocols = websocket.headers.get("sec-websocket-protocol", "")
    for part in (p.strip() for p in protocols.split(",")):
        lower = part.lower()
        if lower.startswith("bearer."):
            return part.split(".", 1)[1]
        if lower.startswith("bearer "):
            return part.split(" ", 1)[1]
    return None


async def _send(conn: WSConnection, event: dict[str, Any]) -> bool:
    event.setdefault("ts", _now())
    return conn.try_send(event)


async def _send_error(conn: WSConnection, code: str, detail: str, request: dict[str, Any] | None = None) -> None:
    await _send(conn, {
        "type": "ws.error",
        "code": code,
        "detail": detail,
        "request": request or {},
    })


async def _assert_member(chat_repo: ChatRepository, chat_id: UUID, user_id: int) -> bool:
    member = await chat_repo.get_member_chat(chat_id=chat_id, member_id=user_id, with_role=False)
    return bool(member and not member.is_banned)


def _message_to_payload(message: Any) -> dict[str, Any]:
    return MessageDTO.model_validate(message.to_dict()).model_dump(mode="json")


async def _replay_after_seq(
    conn: WSConnection,
    message_repo: MessageRepository,
    chat_id: UUID,
    last_seq: int,
) -> None:
    limit = chat_config.WS_REPLAY_BATCH_SIZE
    messages = await message_repo.get_chat_messages_after_seq(
        chat_id=chat_id,
        last_seq=last_seq,
        limit=limit,
    )
    batch = messages[:limit]
    conn.last_seq_by_chat[str(chat_id)] = batch[-1].seq if batch else last_seq

    await _send(conn, {
        "type": "ws.history",
        "chat_id": str(chat_id),
        "payload": {
            "after_seq": last_seq,
            "messages": [_message_to_payload(message) for message in batch],
            "has_more": len(messages) > limit,
            "next_last_seq": conn.last_seq_by_chat[str(chat_id)],
        },
    })


async def _handle_subscribe(
    conn: WSConnection,
    command: WSClientCommand,
    manager: BaseConnectionManager,
    chat_repo: ChatRepository,
    message_repo: MessageRepository,
) -> None:
    if not command.chat_id:
        await _send_error(conn, "BAD_REQUEST", "chat_id is required", command.model_dump())
        return

    try:
        chat_id = UUID(command.chat_id)
    except ValueError:
        await _send_error(conn, "BAD_CHAT_ID", "chat_id must be UUID", command.model_dump())
        return

    if not await _assert_member(chat_repo, chat_id, conn.user_id):
        await _send_error(conn, "ACCESS_DENIED", "user is not a chat member", command.model_dump())
        return

    await manager.subscribe_chat(conn, str(chat_id))
    await _send(conn, {
        "type": "ws.subscribed",
        "chat_id": str(chat_id),
        "payload": {"last_seq": command.last_seq},
    })

    if command.last_seq is not None:
        await _replay_after_seq(conn, message_repo, chat_id, max(0, command.last_seq))


async def _handle_unsubscribe(
    conn: WSConnection,
    command: WSClientCommand,
    manager: BaseConnectionManager,
) -> None:
    if not command.chat_id:
        await _send_error(conn, "BAD_REQUEST", "chat_id is required", command.model_dump())
        return

    await manager.unsubscribe_chat(conn, command.chat_id)
    await _send(conn, {
        "type": "ws.unsubscribed",
        "chat_id": command.chat_id,
        "payload": {},
    })


async def _handle_resume(
    conn: WSConnection,
    command: WSClientCommand,
    manager: BaseConnectionManager,
    chat_repo: ChatRepository,
    message_repo: MessageRepository,
) -> None:
    if not command.cursors:
        await _send_error(conn, "BAD_REQUEST", "cursors map is required", command.model_dump())
        return

    for raw_chat_id, raw_last_seq in command.cursors.items():
        resume_command = WSClientCommand(
            op=WSClientOp.SUBSCRIBE,
            chat_id=raw_chat_id,
            last_seq=max(0, int(raw_last_seq)),
        )
        await _handle_subscribe(conn, resume_command, manager, chat_repo, message_repo)


async def _receive_json(websocket: WebSocket) -> dict[str, Any]:
    message = await websocket.receive()
    if message["type"] == "websocket.disconnect":
        raise WebSocketDisconnect(message.get("code", 1000))

    raw: str | bytes | None = message.get("text") or message.get("bytes")
    if raw is None:
        raise ValueError("empty websocket frame")

    if isinstance(raw, str):
        raw_bytes = raw.encode("utf-8")
    else:
        raw_bytes = raw

    if len(raw_bytes) > chat_config.WS_MAX_CLIENT_FRAME_BYTES:
        raise ValueError("websocket frame is too large")

    data = orjson.loads(raw_bytes)
    if not isinstance(data, dict):
        raise ValueError("websocket frame must be a JSON object")
    return data


@router.websocket("/ws")
@inject
async def websocket_gateway(
    websocket: WebSocket,
    jwt_manager: FromDishka[JWTManager],
    session: FromDishka[AsyncSession],
    manager: FromDishka[BaseConnectionManager],
    chat_repo: FromDishka[ChatRepository],
    message_repo: FromDishka[MessageRepository],
) -> None:
    token = _extract_ws_token(websocket)
    if not token:
        await websocket.close(code=1008, reason="missing token")
        return

    try:
        user_jwt_data = UserJWTData.create_from_token(await jwt_manager.validate_token(token))
        user_id = int(user_jwt_data.id)
    except (InvalidTokenException, ValueError):
        await websocket.close(code=1008, reason="invalid token")
        return

    offered_protocols = {p.strip() for p in websocket.headers.get("sec-websocket-protocol", "").split(",") if p.strip()}
    await websocket.accept(subprotocol="chat.v1" if "chat.v1" in offered_protocols else None)

    conn = WSConnection(
        websocket=websocket,
        user_id=user_id,
        device_id=user_jwt_data.device_id or websocket.query_params.get("device_id") or "unknown",
        gateway_id="",
    )

    await manager.register(conn)
    await _send(conn, {
        "type": "ws.ready",
        "payload": {
            "connection_id": conn.connection_id,
            "gateway_id": conn.gateway_id,
            "heartbeat_interval": chat_config.WS_HEARTBEAT_INTERVAL,
            "heartbeat_timeout": chat_config.WS_HEARTBEAT_TIMEOUT,
            "reconnect": {"mode": "last_seq_per_chat", "op": "resume"},
        },
    })

    initial_chat_id = websocket.query_params.get("chat_id")
    initial_last_seq = websocket.query_params.get("last_seq")
    if initial_chat_id and initial_last_seq is not None:
        try:
            await _handle_subscribe(
                conn,
                WSClientCommand(op=WSClientOp.SUBSCRIBE, chat_id=initial_chat_id, last_seq=int(initial_last_seq)),
                manager,
                chat_repo,
                message_repo,
            )
        except ValueError:
            await _send_error(conn, "BAD_LAST_SEQ", "last_seq must be integer")

    try:
        while True:
            try:
                payload = await _receive_json(websocket)
                conn.touch()
                command = WSClientCommand.model_validate(payload)
            except ValidationError as exc:
                await _send_error(conn, "BAD_COMMAND", exc.errors()[0].get("msg", "invalid command"))
                continue
            except ValueError as exc:
                await _send_error(conn, "BAD_FRAME", str(exc))
                continue

            if command.op == WSClientOp.PING:
                await _send(conn, {"type": "ws.pong", "payload": {}})
            elif command.op == WSClientOp.PONG:
                conn.touch()
            elif command.op == WSClientOp.SUBSCRIBE:
                await _handle_subscribe(conn, command, manager, chat_repo, message_repo)
            elif command.op == WSClientOp.UNSUBSCRIBE:
                await _handle_unsubscribe(conn, command, manager)
            elif command.op == WSClientOp.RESUME:
                await _handle_resume(conn, command, manager, chat_repo, message_repo)
            else:
                await _send_error(conn, "UNKNOWN_COMMAND", "unsupported websocket command", payload)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.unregister(conn)
        await session.rollback()
