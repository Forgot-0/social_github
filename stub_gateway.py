"""Stub of the chat gateway REST + WS contract, for smoke testing the scenarios.

Not part of the deliverable. It only reproduces the wire contract:
  POST /api/v1/chats/{chat_id}/messages/  -> 201 + MessageDTO-ish body
  WS   /api/v1/chats/ws/?token=...        -> ws.ready, subscribe/resume/pong,
                                             fanout of new_message with origin_ts
"""
import asyncio
import json
import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
subs: dict[str, set[WebSocket]] = defaultdict(set)
seqs: dict[str, int] = defaultdict(int)
LATENCY = float(__import__("os").environ.get("STUB_LATENCY_S", "0.05"))
stats = {"posts": 0, "connects": 0, "resumes": 0, "subscribes": 0}


@app.post("/api/v1/chats/{chat_id}/messages/")
async def send(chat_id: str, body: dict):
    stats["posts"] += 1
    seqs[chat_id] += 1
    seq = seqs[chat_id]
    origin = time.time()
    msg_id = str(uuid.uuid4())

    async def fanout():
        # Emulate outbox -> kafka -> router -> stream delay.
        await asyncio.sleep(LATENCY)
        event = {
            "type": "new_message",
            "event_name": "chats.message.sent",
            "event_id": str(uuid.uuid4()),
            "chat_id": chat_id,
            "payload": {"message_id": msg_id, "sender_id": 1},
            "seq": seq,
            "origin_ts": origin,
            "fanout_strategy": "fanout_on_write",
            # ts overwritten per frame, exactly like WSConnection.try_send
            "ts": None,
        }
        for ws in list(subs[chat_id]):
            frame = {**event, "ts": time.time()}
            try:
                await ws.send_text(json.dumps(frame))
            except Exception:
                subs[chat_id].discard(ws)

    asyncio.create_task(fanout())
    return {"id": msg_id, "chat_id": chat_id, "seq": seq, "content": body.get("content")}


@app.websocket("/api/v1/chats/ws/")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept(subprotocol="chat.v1")
    stats["connects"] += 1
    await websocket.send_text(json.dumps({
        "type": "ws.ready",
        "payload": {"connection_id": str(uuid.uuid4()), "gateway_id": "stub",
                    "heartbeat_interval": 30, "heartbeat_timeout": 75},
    }))
    mine: set[str] = set()
    try:
        while True:
            raw = await websocket.receive_text()
            cmd = json.loads(raw)
            op = cmd.get("op")
            if op == "subscribe":
                stats["subscribes"] += 1
                cid = str(cmd["chat_id"])
                mine.add(cid)
                subs[cid].add(websocket)
                await websocket.send_text(json.dumps(
                    {"type": "ws.subscribed", "chat_id": cid, "ts": time.time()}))
            elif op == "unsubscribe":
                cid = str(cmd["chat_id"])
                subs[cid].discard(websocket)
                mine.discard(cid)
            elif op == "resume":
                stats["resumes"] += 1
                await websocket.send_text(json.dumps(
                    {"type": "ws.resumed", "payload": {"cursors": cmd.get("cursors", {})},
                     "ts": time.time()}))
            elif op == "pong":
                pass
    except WebSocketDisconnect:
        pass
    finally:
        for cid in mine:
            subs[cid].discard(websocket)


@app.get("/stub/stats")
async def get_stats():
    return {**stats, "subscribed_chats": {k: len(v) for k, v in subs.items() if v}}
