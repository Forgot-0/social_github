from fastapi import APIRouter

from app.projects.routes.v1 import projects, positions, applications, project_roles


router_v1 = APIRouter()
router_v1.include_router(projects.router, prefix="/projects", tags=["projects"])
router_v1.include_router(positions.router, prefix="/positions", tags=["positions"])
router_v1.include_router(project_roles.router, prefix="/project_roles", tags=["roles"])
router_v1.include_router(applications.router, prefix="/applications", tags=["applications"])

