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
│   ├── security/           # Authentication
│   │   ├── token.py        # JWT creation/validation
│   │   └── password.py     # Argon2id hashing
│   │
│   ├── middlewares/        # Request middleware
│   │   └── user.py         # User extraction from JWT
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
│   └── test_health.py
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

The `CORE_JWT_*` / `WEBAPP_URL` / `COOKIE_DOMAIN` settings are leftovers from the
monorepo template: this application has no login, so they are unused.

## Database

### Connection

Uses async SQLAlchemy with asyncpg driver. Connection configured via `DATABASE_URL`:

```
postgresql://user:password@host:5432/database
```

### Migrations

Migrations auto-run on application startup. Manual commands:

```bash
# Generate a new migration
alembic revision --autogenerate -m "Add users table"

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
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

This application has **no authentication** (a single user, running locally). The
helpers below still ship with the template but are not wired into any route — do not
add `get_current_user` dependencies or a login router.

### Password Hashing

Uses Argon2id with secure defaults:

```python
from core.security.password import hash_password, verify_password

hashed = hash_password("plaintext")
is_valid = verify_password("plaintext", hashed)
```

### JWT Tokens

```python
from core.security.token import create_access_token
from datetime import timedelta

token = create_access_token(
    data={"sub": str(user_id)},
    expires_delta=timedelta(minutes=60)
)
```

### Auth Middleware

Inject current user into route handlers:

```python
from typing import Annotated
from fastapi import Depends
from core.middlewares.user import get_current_user
from core.models.user import User

@router.get("/me")
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
```

Supports both:
- Cookie-based auth (for web app)
- Bearer token in `Authorization` header (for mobile/API clients)

## Testing

Tests run inside the core container (they need the database):

```bash
make test-core                                    # all core tests
docker compose exec core bash -c 'uv run pytest core/tests/test_health.py -v'
```

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
