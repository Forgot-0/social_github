from fastapi import APIRouter

from app.chats.routes.v1 import chats


router_v1 = APIRouter()
router_v1.include_router(chats.router, prefix="/chats", tags=["chats"])

