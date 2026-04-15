import logging
from contextlib import asynccontextmanager

from dishka.integrations.faststream import FastStreamProvider, setup_dishka
from faststream import ContextRepo
from faststream.asgi import AsgiFastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.prometheus import KafkaPrometheusMiddleware
from prometheus_client import CollectorRegistry, make_asgi_app
import structlog

from app.core.configs.app import app_config
from app.core.di.container import create_container
from app.core.log.init import configure_logging
from app.core.message_brokers.base import BaseMessageBroker

from app.profiles.consumers import user
from app.analytics.consumers import analytics

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(context: ContextRepo) :
    logger.info("Starting FastStream")
    container = context.get("container__")
    message_broker = await container.get(BaseMessageBroker)
    await message_broker.start()

    yield

    await message_broker.stop()


def setup_router(broker: KafkaBroker) -> None:
    broker.include_router(user.router)
    broker.include_router(analytics.router)


def init_app() -> AsgiFastStream:
    configure_logging()
    registry = CollectorRegistry()
    log = structlog.get_logger("main")
    broker = KafkaBroker(
        app_config.BROKER_URL,
        client_id=app_config.GROUP_ID,
        middlewares=(
            KafkaPrometheusMiddleware(registry=registry),
        ),
        logger=log
    )
    app = AsgiFastStream(
        broker,
        asgi_routes=[
            ("/metrics", make_asgi_app(registry)),
        ],
        logger=log
    )

    setup_router(broker)
    container = create_container(FastStreamProvider())
    app.context.set_global("container__", container)

    setup_dishka(container=container, broker=broker, auto_inject=True)

    logger.info("Init app FastStream")
    return app


app = init_app()
