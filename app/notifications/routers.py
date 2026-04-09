from fastapi import APIRouter

from app.notifications.routes.v1 import notifications

router_v1 = APIRouter()
router_v1.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
