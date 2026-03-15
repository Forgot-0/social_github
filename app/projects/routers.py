from fastapi import APIRouter

from app.projects.routes.v1 import projects, positions, applications


router_v1 = APIRouter()
router_v1.include_router(projects.router, prefix="/projects", tags=["projects"])
router_v1.include_router(positions.router, prefix="/positions", tags=["positions"])
router_v1.include_router(applications.router, prefix="/applications", tags=["applications"])

