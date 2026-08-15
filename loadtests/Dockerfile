FROM python:3.14-rc-slim AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

FROM python-base AS builder-base

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        gcc \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR $PYSETUP_PATH
COPY pyproject.toml poetry.lock ./

RUN python -m pip install \
        --no-cache-dir \
        --upgrade \
        pip==25.1.1 \
    && python -m pip install \
        --no-cache-dir \
        setuptools==69.5.1 \
        wheel==0.43.0 \
        poetry==2.2.1

RUN poetry check \
    && poetry install \
        --without dev \
        --without test \
        --no-root \
        --no-ansi

COPY loadtests/requirements.txt /tmp/loadtest-requirements.txt
RUN $VENV_PATH/bin/pip install --no-cache-dir -r /tmp/loadtest-requirements.txt

FROM python-base AS loadtest

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

WORKDIR /app

COPY app/ ./app/
COPY loadtests/ ./loadtests/

RUN groupadd --system loadtest \
    && useradd --system --gid loadtest --create-home loadtest \
    && chown -R loadtest:loadtest /app $PYSETUP_PATH

USER loadtest
ENV PATH="$VENV_PATH/bin:$PATH" \
    PYTHONPATH="/app"
