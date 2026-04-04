from contextlib import asynccontextmanager
import logging

from dishka.integrations.faststream import FastStreamProvider, setup_dishka
from faststream import ContextRepo, FastStream
from faststream.kafka import KafkaBroker

from app.core.configs.app import app_config
from app.core.di.container import create_container
from app.core.log.init import configure_logging

from app.core.message_brokers.base import BaseMessageBroker


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(context: ContextRepo) :
    logger.info("Starting FastStream")
    container = context.get("container__")
    message_broker = await container.get(BaseMessageBroker)
    await message_broker.start()

    yield

    await message_broker.stop()


def setup_router(app: FastStream) -> None:
    ...


def init_app() -> FastStream:
    configure_logging()
    broker = KafkaBroker(app_config.BROKER_URL, client_id=app_config.GROUP_ID)
    app = FastStream(broker, lifespan=lifespan)

    setup_router(app)
    container = create_container(FastStreamProvider())
    app.context.set_global("container__", container)

    setup_dishka(container=container, broker=broker, auto_inject=True)

    logger.info("Init app FastStream")
    return app


app = init_app()
