from fastapi import APIRouter

from app.projects.routes.v1 import projects


router_v1 = APIRouter()
router_v1.include_router(projects.router, prefix="/projects", tags=["projects"])

