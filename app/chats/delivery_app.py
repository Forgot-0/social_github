import asyncio
import logging

from app.chats.services.delivery_router import ChatDeliveryRouter
from app.core.di.container import create_container
from app.core.log.init import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging()
    container = create_container()
    try:
        router = await container.get(ChatDeliveryRouter)
        await router.run_forever()
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
