from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models.role import Role
from app.auth.models.role_permission import RolesEnum
from app.chats.models.chat_roles import ChatRole
from app.chats.models.permission import ChatRolesEnum
from app.projects.models.role import ProjectRole
from app.projects.models.role_permissions import ProjectRolesEnum


async def create_first_data(db: AsyncSession) -> None:
    roles = RolesEnum.get_all_roles()
    for base_role in roles:
        role = await db.execute(select(Role).where(Role.name==base_role.name))

        if role.scalar() is None:
            db.add(base_role)

    project_roles = ProjectRolesEnum.get_all_project_roles()
    for base_role in project_roles:
        role = await db.execute(select(ProjectRole).where(ProjectRole.name==base_role.name))

        if role.scalar() is None:
            db.add(base_role)


    chat_roles = ChatRolesEnum.get_all_chat_roles()
    for base_role in chat_roles:
        role = await db.execute(select(ChatRole).where(ChatRole.name==base_role.name))

        if role.scalar() is None:
            db.add(base_role)
    await db.commit()


async def init_data(db: AsyncSession) -> None:
    await create_first_data(db)
