from taskiq import AsyncBroker

from app.auth.tasks import register_auth_tasks
from app.profiles.tasks import register_profiles_tasks
from app.projects.tasks import register_project_tasks


def register_tasks(broker: AsyncBroker) -> None:

    register_auth_tasks(broker)
    register_profiles_tasks(broker)
    register_project_tasks(broker)
