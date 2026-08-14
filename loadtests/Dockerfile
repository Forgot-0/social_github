ARG APP_IMAGE=social_github-app
FROM python:3.14-slim AS loadtest

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY loadtests/requirements.txt /tmp/loadtests-requirements.txt
COPY pyproject.toml /tmp/pyproject.toml

RUN pip install --no-cache-dir \
        "sqlalchemy[asyncio]>=2.0" \
        asyncpg \
        pyjwt \
        pydantic \
        pydantic-settings \
        orjson \
        redis \
        prometheus-client \
        fastapi \
    && pip install --no-cache-dir -r /tmp/loadtests-requirements.txt

COPY . /app

ENV PYTHONPATH=/app

CMD ["locust", "--version"]
