from dishka.integrations.faststream import FromDishka
from faststream.kafka import KafkaRouter

from app.analytics.service import AnalyticsClickHouseService
from app.core.configs.app import app_config


router = KafkaRouter()


@router.subscriber(app_config.ANALYTICS_KAFKA_TOPIC, group_id="analytics-consumer")
async def process_analytics_event(msg: dict, service: FromDishka[AnalyticsClickHouseService]) -> None:
    await service.insert_event(msg)


