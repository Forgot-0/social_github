from dataclasses import dataclass

from app.core.db.repository import CacheRepository, IRepository
from app.notifications.models.device import UserDeviceToken


@dataclass
class DeviceRepository(IRepository[UserDeviceToken], CacheRepository):
    _LIST_VERSION_KEY = "device:list"

    async def create(self, device: UserDeviceToken) -> None:
        self.session.add(device)

