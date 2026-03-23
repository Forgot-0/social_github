from fastapi import APIRouter

from app.chats.routes.v1 import chats, messages, ws

router_v1 = APIRouter()
router_v1.include_router(chats.router, prefix="/chats", tags=["chats"])
router_v1.include_router(ws.router, prefix="/chats", tags=["chats"])
router_v1.include_router(messages.router, prefix="/chats/{chat_id}/messages", tags=["messages"])
 