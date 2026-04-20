# Social GitHub - Development Runbook

A high-performance social networking platform built with FastAPI, PostgreSQL, and modern DevOps practices.

## Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Environment Setup](#development-environment-setup)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Database Management](#database-management)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Docker Setup](#docker-setup)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)

## Project Overview

Social GitHub is a comprehensive platform providing:

- **Authentication**: JWT-based auth with OAuth support (Google, Yandex, GitHub)
- **Real-time Chat**: WebSocket-based messaging with LiveKit integration
- **User Profiles**: Detailed user management and profile services
- **Projects**: Project creation and management
- **Analytics**: Event tracking with ClickHouse
- **Notifications**: Real-time notification system
- **Storage**: S3-compatible storage via MinIO
- **Task Queue**: Async task processing with Taskiq + Redis

**Tech Stack**:
- Backend: FastAPI 0.135+, Python 3.12+
- Database: PostgreSQL 18
- Cache/Queue: Redis 7
- Message Broker: Apache Kafka 8.2
- Analytics: ClickHouse 25.3
- Storage: MinIO
- Async Tasks: Taskiq with Redis broker
- Real-time: WebSockets, LiveKit
- Monitoring: Prometheus, Grafana, Loki, Vector
- Containerization: Docker & Docker Compose

---

## Prerequisites

### System Requirements

- **OS**: Linux, macOS, or Windows (with WSL2 recommended)
- **Docker**: 20.10+ and Docker Compose 2.0+
- **Python**: 3.12 - 3.14
- **Git**: Latest version
- **RAM**: Minimum 4GB (8GB recommended for full stack)
- **Disk**: At least 5GB free space for Docker volumes

### Install Prerequisites

#### On macOS (using Homebrew):
```bash
brew install docker docker-compose python@3.12 git
```

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose python3.12 python3.12-venv git
sudo usermod -aG docker $USER  # Add user to docker group
newgrp docker  # Activate docker group
```

#### On Windows:
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop) (includes Docker Compose)
2. Install [Python 3.12+](https://www.python.org/downloads/)
3. Install [Git for Windows](https://git-scm.com/)
4. Enable WSL2 in Docker Desktop settings

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Forgot-0/social_github.git
cd social_github
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Essential variables to set**:
```bash
ENVIRONMENT=local
PROJECT_NAME=SocialGithub
DOMAIN=localhost
SECRET_KEY=your-secret-key-here  # Generate: openssl rand -hex 32
JWT_SECRET_KEY=your-jwt-secret   # Generate: openssl rand -hex 32
POSTGRES_PASSWORD=your-password
```

### 3. Create Docker Network

```bash
docker network create app-network
```

### 4. Start Services with Docker Compose

```bash
# Start all services (app, database, redis, kafka, minio, clickhouse)
docker-compose up -d

# Verify all services are healthy
docker-compose ps

# Check logs
docker-compose logs -f app
```

### 5. Run Database Migrations

```bash
# Option A: Via Docker Compose (automatic)
docker-compose up migrations

# Option B: Local (if running without Docker)
alembic upgrade head
```

### 6. Access Application

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Development Environment Setup

### 1. Create Python Virtual Environment

```bash
# Using venv
python3.12 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install runtime dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev,test,lint]"

# Or install all at once
pip install -e ".[dev,test,lint]"
```

### 3. Install Pre-commit Hooks

```bash
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### 4. Verify Installation

```bash
# Check Python version
python --version  # Should be 3.12+

# Check key packages
python -c "import fastapi; import sqlalchemy; print('All good!')"

# Verify linting tools
ruff --version
mypy --version
pylint --version
```

---

## Running the Application

### Local Development (without Docker)

#### 1. Start PostgreSQL with Docker Only

```bash
# Start only the database
docker-compose up -d db redis kafka minio clickhouse

# Wait for services to be healthy (check docker-compose ps)
```

#### 2. Start Application in Development Mode

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the FastAPI CLI
fastapi run
```

#### 3. Start Task Queue Worker

In a separate terminal:

```bash
# Start taskiq worker
taskiq worker app.tasks:broker --no-configure-logging
```

#### 4. Start Event Consumer

In another terminal:

```bash
# Start Kafka consumer
faststream run app.consumers:app --host 0.0.0.0 --port 9002
```

#### 5. (Optional) Start Scheduler

For scheduled tasks:

```bash
taskiq scheduler app.tasks:scheduler --no-configure-logging
```

### With Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Rebuild and restart a specific service
docker-compose up --build -d app

# Stop all services
docker-compose down

# Stop and remove volumes (caution: data loss!)
docker-compose down -v
```

---

## Project Structure

```
social_github/
├── app/                      # Main application package
│   ├── main.py              # FastAPI app initialization
│   ├── pre_start.py         # Pre-startup checks
│   ├── init_data.py         # Initial data loading
│   ├── consumers.py         # Kafka event consumers
│   ├── tasks.py             # Taskiq task definitions
│   │
│   ├── auth/                # Authentication module
│   │   ├── routers.py       # Auth endpoints
│   │   ├── services/        # Auth business logic
│   │   ├── providers.py     # OAuth providers (Google, Yandex, GitHub)
│   │   ├── commands/        # Commands for auth operations
│   │   ├── queries/         # Query handlers
│   │   ├── repositories/    # Data access layer
│   │   └── schemas/         # Pydantic models
│   │
│   ├── chats/               # Chat/messaging module
│   │   ├── routers.py       # Chat endpoints
│   │   ├── services/        # Chat services
│   │   └── ...
│   │
│   ├── profiles/            # User profiles module
│   ├── projects/            # Projects module
│   ├── analytics/           # Analytics & tracking
│   ├── notifications/       # Notification service
│   │
│   ├── core/                # Core utilities
│   │   ├── db/              # Database configuration
│   │   ├── di/              # Dependency injection
│   │   ├── api/             # API setup
│   │   ├── config/          # Settings & configuration
│   │   ├── events/          # Event handlers
│   │   ├── filters/         # Exception filters
│   │   ├── middlewares/     # Request middlewares
│   │   ├── services/        # Core services (email, storage)
│   │   └── websockets/      # WebSocket utilities
│   │
│   └── media/               # Media handling (images, files)
│
├── migrations/              # Alembic database migrations
│   └── versions/            # Migration scripts
│
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   ├── auth/                # Auth tests
│   ├── profiles/            # Profile tests
│   └── ...
│
├── monitoring/              # Monitoring stack configs
│   ├── prometheus/          # Prometheus configuration
│   ├── grafana/             # Grafana provisioning
│   ├── loki/                # Loki logging config
│   └── vector/              # Vector log forwarding
│
├── nginx/                   # Nginx reverse proxy config
├── infra/                   # Infrastructure configs
│   ├── postgres/            # PostgreSQL config
│   └── livekit/             # LiveKit config
│
├── docker-compose.yaml      # Development services
├── docker-compose.prod.yaml # Production services
├── Dockerfile               # Application container
├── gunicorn.conf.py         # Gunicorn configuration
├── pyproject.toml           # Project metadata & dependencies
├── mypy.ini                 # MyPy type checking config
├── .ruff.toml               # Ruff linter config
└── README.md                # This file
```

---

## Database Management

### Running Migrations

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "Add user_preferences table"

# Review the migration file in migrations/versions/
nano migrations/versions/<revision>_.py

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history --indicate-current
```

### Database Connection

Local PostgreSQL connection details (from `.env`):
```
Host: localhost (or 'db' inside Docker)
Port: 5432
Database: app
User: user
Password: password
```

Connect locally:
```bash
# Via psql
psql -h localhost -U user -d app

# Via Python
python -c "
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect('postgresql://user:password@localhost/app')
    result = await conn.fetch('SELECT version();')
    print(result)
    await conn.close()

asyncio.run(test())
"
```

### Database Backup & Restore

```bash
# Backup
docker-compose exec db pg_dump -U user -d app > backup.sql

# Restore
docker-compose exec -T db psql -U user -d app < backup.sql

# Full backup with Docker
docker-compose exec db pg_dump -U user app --format=custom > backup.dump
docker-compose exec -T db pg_restore -U user -d app backup.dump
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/auth/test_login.py

# Run tests matching pattern
pytest -k "test_login"

# Run with coverage
pytest --cov=app --cov-report=html

# Run in parallel (faster)
pytest -n auto

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run specific test node
pytest tests/auth/test_login.py::test_user_login
```

### Test Configuration

See `pytest.ini` options in [pyproject.toml](pyproject.toml#L65-L68):
- Tests located in `tests/` directory
- Async mode: `auto` (pytest-asyncio)
- Parallel execution: supported via `pytest-xdist`

### Writing Tests

Example test structure:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """Test user creation endpoint."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepass123",
            "username": "testuser"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
```

---

## Code Quality

### Linting with Ruff

```bash
# Check code style and issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .

# Check specific file
ruff check app/auth/services.py --fix
```

### Type Checking with MyPy

```bash
# Run type checker
mypy

# Check specific file
mypy app/auth/providers.py

# Show error codes
mypy --show-error-codes

# Strict mode
mypy --strict app/
```

### Linting with Pylint

```bash
# Run pylint on specific file
pylint app/auth/services.py

# Run on entire app
pylint app/

# Generate report
pylint app/ --output-format=json > lint-report.json
```

### Pre-commit Hooks

```bash
# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Update hook versions
pre-commit autoupdate
```

### Code Quality Checklist Before Commit

```bash
# 1. Format code
ruff format .

# 2. Fix linting issues
ruff check . --fix

# 3. Type check
mypy

# 4. Run tests
pytest

# 5. Run pre-commit hooks
pre-commit run --all-files
```

---

## Docker Setup

### Building Docker Images

```bash
# Build production image
docker build -t social-github:latest .

# Build with specific target
docker build --target production -t social-github:prod .

# Build with build arguments
docker build --build-arg ENV=production -t social-github:latest .
```

### Docker Compose Services

#### Development Stack (docker-compose.yaml)

| Service | Port | Purpose |
|---------|------|---------|
| app | 8000 | FastAPI application |
| db | 5432 | PostgreSQL database |
| redis | 6379 | Cache & task broker |
| kafka | 9092 | Message broker |
| minio | 9000/9001 | S3-compatible storage (single node) |
| clickhouse | 8123 | Analytics database |
| consumers | 9002 | Kafka event consumer |
| queue_worker | - | Task queue worker |
| scheduler | - | Task scheduler |
| migrations | - | Database migrations |

#### Production Stack (docker-compose.prod.yaml)

| Service | Port | Purpose |
|---------|------|---------|
| nginx | 80/443 | Reverse proxy & SSL |
| livekit | 7880/7881 | Real-time communication |
| app | - | FastAPI (internal) |

#### Monitoring Stack (docker-compose.monitoring.yml)

| Service | Port | Purpose |
|---------|------|---------|
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Visualization & dashboards |
| loki | 3100 | Log aggregation |
| vector | - | Log forwarding |
| redis-exporter | 9121 | Redis metrics |
| postgres-exporter | 9187 | PostgreSQL metrics |
| kafka-exporter | 9308 | Kafka metrics |
| **minio-exporter** | **9290** | **MinIO storage metrics** |

### Common Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Start specific service
docker-compose up -d app db

# View logs
docker-compose logs -f [service]

# Rebuild service
docker-compose up -d --build app

# Stop services
docker-compose down

# Remove volumes (WARNING: data loss!)
docker-compose down -v

# Execute command in container
docker-compose exec app bash

# View resource usage
docker-compose stats
```

### MinIO Highload Configuration

The project includes both single-node and distributed MinIO configurations for different load requirements:

#### Single Node (Development)
- **Service**: `minio`
- **Ports**: 9000 (API), 9001 (Console)
- **Use case**: Development, testing, low traffic
- **Resources**: 2 CPU cores, 4GB RAM

**Features enabled for highload**:
- **Erasure Coding**: `EC:2` for standard storage, `EC:1` for reduced redundancy
- **Compression**: Gzip compression for text-based files
- **Connection Limits**: Up to 2000 concurrent connections per node
- **Caching**: Intelligent caching with watermark management
- **Prometheus Metrics**: Built-in metrics collection

**Switching between configurations**:

```bash
# Use single node (default)
docker-compose up -d minio
```

### Healthchecks

All services have healthchecks configured. View status:

```bash
docker-compose ps

# Expected output:
# NAME         STATUS
# app          healthy
# db           healthy
# redis        healthy
# kafka        healthy
```

---

## Monitoring & Observability

### Prometheus

Access at: http://localhost:9090

Metrics collected from:
- Application: `/metrics` endpoint
- PostgreSQL: pg_exporter (port 9187)
- Redis: redis_exporter (port 9121)
- Kafka: kafka_exporter (port 9308)
- **MinIO**: minio-exporter (port 9290) - storage metrics, S3 operations, disk usage

### Grafana

Access at: http://localhost:3000

Default credentials (change in production):
- Username: `admin`
- Password: `changeme` (or value of `GRAFANA_PASSWORD` in `.env`)

Pre-configured dashboards:
- Application Overview
- Database Performance
- Redis Cache Metrics
- Kafka Broker Metrics
- **MinIO Storage Dashboard** - bucket usage, S3 operations, disk I/O, cluster health

### Loki (Log Aggregation)

Access at: http://localhost:3100

Logs are collected via:
- Vector: Forwards Docker container logs
- Application structured logging: Via structlog

Query logs in Grafana: Menu → Explore → Select Loki datasource

### Application Monitoring

Application exports metrics via Prometheus FastAPI Instrumentator:

```
# Request metrics
http_requests_total
http_request_duration_seconds
http_request_size_bytes

# Custom metrics
application_info
database_connection_pool_size
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs app

# Common issues:
# 1. Database not ready - wait 30s and retry
# 2. Redis connection failed - verify redis service
# 3. Kafka not available - check kafka healthcheck

# Solution: Restart app service
docker-compose restart app
```

### Database Connection Errors

```bash
# Test database connection
docker-compose exec app python -c "
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect(
        host='db',
        user='${POSTGRES_USER}',
        password='${POSTGRES_PASSWORD}',
        database='${POSTGRES_DB}'
    )
    print('Connection successful!')
    await conn.close()

asyncio.run(test())
"

# Check database logs
docker-compose logs db
```

### Redis Connection Issues

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping
# Expected: PONG

# Check Redis logs
docker-compose logs redis

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

### Kafka Connection Problems

```bash
# Check Kafka broker health
docker-compose exec kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# List topics
docker-compose exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# View consumer groups
docker-compose exec kafka kafka-consumer-groups.sh --list --bootstrap-server localhost:9092
```

### Port Already in Use

```bash
# Find and kill process using port (Linux/macOS)
lsof -i :8000
kill -9 <PID>

# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or map different port
docker-compose up -d -p "9000:8000" app
```

### Out of Memory

```bash
# Check Docker resource limits
docker stats

# Increase memory limit in docker-compose.yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G

# Restart with new limits
docker-compose up -d
```

### Migrations Stuck or Failed

```bash
# Check migration status
docker-compose exec app alembic current

# Manually rollback
docker-compose exec app alembic downgrade -1

# Try upgrading again
docker-compose exec app alembic upgrade head

# Reset (WARNING: data loss!)
docker-compose exec app alembic downgrade base
docker-compose exec app alembic upgrade head
```

### WebSocket Connection Issues

```bash
# WebSockets available at:
ws://localhost:8000/ws/chat/{room_id}

# Check if endpoint exists
curl http://localhost:8000/docs

# Test with websocat
websocat ws://localhost:8000/ws/chat/test-room

# Check for reverse proxy issues (in production)
# Ensure nginx is configured with WebSocket support
```

### Performance Issues

```bash
# Monitor resource usage
docker-compose stats

# Check slow database queries
docker-compose exec app python -c "
from app.core.db.config import SessionLocal
import time

async with SessionLocal() as session:
    start = time.time()
    # Run your query here
    print(f'Query took {time.time() - start}s')
"

# Enable query logging
# Set SQL_ECHO=True in .env

# Check application metrics
# Visit http://localhost:9090 (Prometheus)
# Or http://localhost:3000 (Grafana)
```

### Clear Cache and Reset

```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Restart all services
docker-compose restart

# Full reset (lose all data)
docker-compose down -v
docker-compose up -d
docker-compose exec app alembic upgrade head
```

---

## Development Workflow

### 1. Feature Branch Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes, commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/new-feature
```

### 2. Code Review Checklist

- [ ] Code follows project style (ruff, mypy)
- [ ] Tests written and passing (`pytest`)
- [ ] Database migrations created (if needed)
- [ ] API documentation updated
- [ ] No hardcoded secrets or credentials
- [ ] Performance impact assessed

### 3. Commit Message Format

```
feat: add new feature
fix: resolve bug
docs: update documentation
refactor: improve code structure
test: add/update tests
perf: improve performance
ci: update CI/CD configuration
```

### 4. Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] No new warnings
```

---

## Environment Variables Reference

See [.env.example](.env.example) for complete list.

### Critical Variables

```bash
# Security
SECRET_KEY                    # API secret key (generate: openssl rand -hex 32)
JWT_SECRET_KEY               # JWT signing key (generate: openssl rand -hex 32)

# Database
POSTGRES_USER                # PostgreSQL user
POSTGRES_PASSWORD            # PostgreSQL password
POSTGRES_DB                  # Database name

# API
DOMAIN                       # Domain for callbacks (e.g., api.example.com)
ENVIRONMENT                  # Environment: local, testing, production

# OAuth (optional for development)
OAUTH_GOOGLE_CLIENT_ID
OAUTH_GOOGLE_CLIENT_SECRET
OAUTH_GITHUB_CLIENT_ID
OAUTH_GITHUB_CLIENT_SECRET
```

---

## Performance Tips

### Database

```python
# Use .select_in_load() for relationships
query = session.query(User).options(
    selectinload(User.profiles)
).all()

# Use database indexes
# Configure in models with __table_args__

# Use connection pooling (already configured)
```

### Caching

```python
# Cache expensive operations
from aiocache import cached
from aiocache.serializers import JsonSerializer

@cached(cache_type='redis', serializer=JsonSerializer())
async def expensive_operation(user_id: int):
    return await db.fetch_user(user_id)
```

### Async Best Practices

```python
# Use async context managers
async with session.begin():
    user = await session.get(User, user_id)
    user.name = "New Name"

# Gather concurrent operations
results = await asyncio.gather(*tasks)
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

---

## Support & Issues

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs [service]`
3. Check service health: `docker-compose ps`
4. Create an issue with:
   - Steps to reproduce
   - Error logs
   - Environment details (OS, Docker version, Python version)

---

**Last Updated**: April 2026
**Python Version**: 3.12+
**FastAPI Version**: 0.135+
