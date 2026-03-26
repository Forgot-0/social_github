from fastapi import APIRouter

from app.rooms.routes.v1 import rooms


router_v1 = APIRouter()
router_v1.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
