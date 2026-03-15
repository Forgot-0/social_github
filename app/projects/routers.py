from fastapi import APIRouter

from app.projects.routes.v1 import router_v1 as projects_router_v1


router_v1 = APIRouter()
router_v1.include_router(projects_router_v1)


