from dishka import AsyncContainer, Provider, make_async_container

from app.auth.providers import AuthModuleProvider
from app.chats.providers import ChatModuleProvider
from app.core.di import get_core_providers
from app.profiles.providers import ProfileModuleProvider
from app.projects.providers import ProjectModuleProvider


def create_container(*app_providers: Provider) -> AsyncContainer:
    providers = [
        # Core providers
        *get_core_providers(),

        # Module providers
        AuthModuleProvider(),
        ProfileModuleProvider(),
        ChatModuleProvider(),
        ProjectModuleProvider(),
    ]

    return make_async_container(*providers, *app_providers)
