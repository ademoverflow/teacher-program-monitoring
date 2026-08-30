# Core API

FastAPI backend service for the application.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.115 |
| Runtime | Python 3.13 |
| ORM | SQLModel (SQLAlchemy wrapper) |
| Database | PostgreSQL 17 (async via asyncpg) |
| Migrations | Alembic |
| Auth | None (local, single-user app) |
| AI | Anthropic SDK |
| Validation | Pydantic |
| Package Manager | uv |

## Project Structure

```
core/
├── src/core/
│   ├── __init__.py         # Package version
│   ├── __main__.py         # Entry point (starts Uvicorn)
│   ├── main.py             # FastAPI app initialization
│   ├── settings.py         # Pydantic Settings config
│   ├── database.py         # Async SQLAlchemy engine
│   │
│   ├── routers/            # API route handlers (mounted under /api)
│   │   ├── __init__.py
│   │   └── health.py       # GET /api/health
│   │
│   ├── models/             # SQLModel data models
│   │   ├── __init__.py     # MUST import every model (Alembic autogenerate)
│   │   ├── user.py         # User model
│   │   └── serializer.py   # JSON serialization (orjson)
│   │
│   ├── logger/             # Logging utilities
│   │   ├── logger.py       # Custom logger setup
│   │   └── levels.py       # Log level enum
│   │
│   ├── misc/               # Utilities
│   │   └── uptime.py       # Process uptime
│   │
│   └── alembic/            # Database migrations
│       ├── alembic.ini
│       ├── env.py
│       └── versions/
│
├── tests/                  # Test suite
│   ├── test_health.py
│   └── test_settings.py
│
├── Dockerfile              # Multi-stage Docker build
├── pyproject.toml          # Dependencies
└── README.md
```

## API Endpoints

All application routers are mounted under the `/api` prefix (see `API_PREFIX` in
`main.py`); the webapp reaches them through the Vite `/api` proxy.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (status, uptime, version) |
| GET | `/docs` | Swagger UI documentation |
| GET | `/redoc` | ReDoc documentation |

## Development

### Running Locally

```bash
# Install dependencies
uv sync

# Start server
uv run python -m core
```

Server runs on `http://0.0.0.0:80` by default (configured via `CORE_SERVER_HOST` and `CORE_SERVER_PORT`).

### With Docker

```bash
# From repository root
docker compose up core
```

Accessible at `http://localhost:12109`.

## Environment Variables

Every setting has a default (`settings.py`), so the service boots with no `.env` at all.

| Variable | Default | Description |
|----------|---------|-------------|
| `CORE_SERVER_HOST` | `0.0.0.0` | Server bind address |
| `CORE_SERVER_PORT` | `80` | Server port |
| `DATABASE_URL` | `postgresql://admin:admin@db:5432/db` | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | *(empty)* | Anthropic key; empty disables the AI feedback feature |
| `ANTHROPIC_MODEL` | `claude-sonnet-5` | Model used for journal feedback |
| `DEV_MODE` | `false` | Enable development mode (hot reload) |

There is no authentication setting: this application has no login (see below).

## Database

### Connection

Uses async SQLAlchemy with asyncpg driver. Connection configured via `DATABASE_URL`:

```
postgresql://user:password@host:5432/database
```

### Migrations

Migrations auto-run on application startup. Manual commands:

```bash
# From the repository root (these run inside the core container)
make db-migrate MSG="Add users table"   # generate a new migration
make db-upgrade                         # apply all migrations
make db-downgrade                       # roll back one migration
```

### Models

SQLModel combines SQLAlchemy ORM with Pydantic validation:

```python
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = True
```

## Authentication

There is none, by design: a single teacher runs this application on her own machine
(MASTER-PROMPT §10). The template's JWT/Argon2 helpers, cookie settings and auth
middleware have been removed — do not reintroduce `get_current_user` dependencies or
a login router.

The `users` table survives as the schema Alembic was bootstrapped with; nothing reads
or writes it.

## Testing

```bash
make test-core       # all core tests, inside the running core container
make test-core-host  # the same tests on the host, without Docker (what CI runs)

# a single file
docker compose exec core bash -c 'uv run pytest core/tests/test_health.py -v'
```

`TestClient(app)` is used without its context manager, so the FastAPI lifespan (and
with it `alembic upgrade head`) does not run: the tests need no database.

Test pattern using FastAPI TestClient:

```python
from fastapi.testclient import TestClient
from core.main import app

client = TestClient(app)

def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

## Code Quality

```bash
make check-python   # Ruff format/lint/import-sort + MyPy
make fix            # Auto-fix formatting and import order
```

## Docker

Multi-stage Dockerfile with `dev` and `prod` targets:

```bash
# Development (with hot reload)
docker build --target dev -t core:dev .

# Production (minimal image)
docker build --target prod -t core:prod .
```
