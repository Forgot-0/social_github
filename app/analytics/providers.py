
import clickhouse_connect
from clickhouse_connect.driver import AsyncClient
from dishka import Provider, Scope, provide

from app.analytics.config import analytic_config
from app.analytics.service import AnalyticsClickHouseService


class AnalyticModuleProvider(Provider):
    scope = Scope.APP

    @provide(scope=Scope.APP)
    async def async_client(self) -> AsyncClient:
        return await clickhouse_connect.get_async_client(
            host=analytic_config.CLICKHOUSE_HOST,
            port=analytic_config.CLICKHOUSE_PORT,
            user=analytic_config.CLICKHOUSE_USER,
            password=analytic_config.CLICKHOUSE_PASSWORD,
            database=analytic_config.CLICKHOUSE_DATABASE,
        )

    service = provide(AnalyticsClickHouseService)
