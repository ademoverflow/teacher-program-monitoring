# CLAUDE.md - AI Assistant Guide

This document provides essential context for AI assistants working with this codebase.

## Project Overview

Full-stack monorepo with:
- **Backend**: Python 3.13+ / FastAPI
- **Frontend**: TypeScript / React 19 / Vite
- **Database**: PostgreSQL 17
- **Containerization**: Docker Compose

All development commands are available via `make`. Run `make help` to see all targets.

## Code Quality Standards

### Python (Ruff + MyPy)

Configuration in `/pyproject.toml`:
- Line length: 100 characters
- Indent: 4 spaces
- Quote style: double quotes
- All rules enabled with specific ignores (see `[tool.ruff.lint]`)

```bash
make check-format   # Check formatting
make fix-format     # Fix formatting
make check-lint     # Run linting
make check-sort     # Check import order
make fix-sort       # Fix import order
make type-check     # Run mypy
make check-python   # Run all Python checks
make fix            # Fix all auto-fixable Python issues
```

### TypeScript/JavaScript (Biome)

Configuration in `/biome.json`:
- Tab indentation
- Double quotes
- Organize imports enabled

```bash
make lint-webapp        # Run linter
make format-webapp      # Run formatter
make type-check-webapp  # Run tsc --noEmit (Biome does not typecheck)
make check-webapp       # Run linter/formatter and the typecheck
```

### All Checks

```bash
make check          # Run ALL checks (Python + webapp)
```

### Commit Messages

Conventional commits enforced via commitlint. Format: `type(scope): description`

Allowed types: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`, `wip`

## Project Structure

```
/
├── core/                    # Python FastAPI backend
│   ├── seed/               # Versioned JSON seeds (`make seed` loads them)
│   ├── src/core/
│   │   ├── __main__.py     # Entry point
│   │   ├── seed.py         # `make seed` entry point
│   │   ├── generate.py     # `make generate` entry point
│   │   ├── main.py         # FastAPI app setup
│   │   ├── settings.py     # Pydantic settings
│   │   ├── clock.py        # Today, as a dependency (overridable in tests)
│   │   ├── schemas.py      # Every response shape the API renders
│   │   ├── database.py     # Async SQLAlchemy setup
│   │   ├── routers/        # API route handlers (one per resource)
│   │   ├── models/         # SQLModel data models
│   │   ├── services/       # Business logic (calendar, seed loader, programmation,
│   │   │                   #   reference, schedule, curriculum, journal,
│   │   │                   #   planned_sessions, generation)
│   │   ├── logger/         # Structured logging
│   │   └── alembic/        # Database migrations
│   └── tests/              # conftest.py holds the shared DB fixtures
├── webapp/                  # React SPA frontend
│   └── src/
│       ├── main.tsx        # App bootstrap
│       ├── router.tsx      # TanStack Router route tree (French paths)
│       ├── env.ts          # T3 Env configuration
│       ├── pages/          # One default-exported page per route
│       ├── components/     # Named-export components (AppLayout, WeekGrid…)
│       ├── lib/            # Typed API client (api/), dates, colors, week-grid, day-journal
│       ├── test/           # Render helpers + API responses frozen from a seeded stack
│       └── integrations/   # Library integrations
├── docs/                    # Source PDFs (§3) + adr/ + agents/ (skill conventions)
├── scripts/                 # Development utilities
├── .claude/skills/          # Claude Code slash commands
├── Makefile                 # Development command runner
└── compose.yaml            # Docker orchestration
```

## Design Patterns

### Backend (Python/FastAPI)

**Router Pattern** (routers are mounted under the `/api` prefix in `main.py`):
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ResponseModel(BaseModel):
    field: str

@router.get("/endpoint", tags=["Tag"])
def handler() -> ResponseModel:
    return ResponseModel(field="value")
```

**SQLModel ORM**:
```python
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, UUID, text

class Model(SQLModel, table=True):
    id: uuid.UUID = Field(
        sa_column=Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    )
```

**Async Database Session**:
```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_session

async def handler(session: Annotated[AsyncSession, Depends(get_session)]) -> None:
    ...
```

**Settings Management**:
```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### Frontend (React/TypeScript)

**TanStack Router** (code-based):
```typescript
import { createRoute } from "@tanstack/react-router";

const route = createRoute({
    getParentRoute: () => rootRoute,
    path: "/path",
    component: Component,
});
```

**TanStack Query** (always through the typed client in `webapp/src/lib/api/`):
```typescript
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";

const { data } = useQuery({
    queryKey: ["key"],
    queryFn: () => apiGet("/endpoint", schema),
});
```

**API access**: the frontend only ever uses relative `/api/...` URLs. Vite's
`server.proxy` forwards `/api` to `http://core:80` (override with
`API_PROXY_TARGET` when running Vite on the host), so there is no CORS setup
and no LAN IP anywhere in the frontend.

**Environment Variables** (T3 Env + Zod):
```typescript
import { env } from "@/env";
// Only access validated env vars through this import
```

## Testing

```bash
make test           # Run all tests (core + webapp)
make test-core      # Run Python tests (pytest, inside the running core container)
make test-core-host # Run Python tests on the host, without Docker (what CI runs)
make test-webapp    # Run JS tests (vitest, on host)
```

### Python Tests

Tests that need a database use the fixtures in `core/tests/conftest.py`: `session` opens an
`AsyncSession` inside a transaction that is rolled back (savepoint-joined, so an endpoint
that commits leaves nothing behind), and `client` drives the app over ASGI with that session
injected. Both skip where no Postgres answers. CI runs a `postgres:17` service, so there are
no skips there (`docs/adr/0018`, `docs/adr/0019`).

```python
from httpx import AsyncClient

async def test_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/endpoint")
    assert response.status_code == 200
```

`core/tests/expected.py` holds the year's counts (36 semaines, 44 créneaux, 1740 séances…)
and the HTTP status codes, so an assertion names the fact it checks.

`test_health.py` is the exception and still uses `TestClient`: it is the one endpoint that
reads nothing.

### JavaScript Tests

Framework: Vitest + Testing Library. `webapp/src/test/app.tsx` mounts the real router at a
chosen URL over a stubbed `fetch`; `webapp/src/test/fixtures/` holds responses captured
verbatim from a seeded stack, so the grid's assembly is tested without a network or a
database. `webapp/src/test/setup.ts` registers Testing Library's cleanup (vitest runs
without global hooks, so it does not register itself).

## Development Workflow

### Docker Services
```bash
make up             # Start all services
make down           # Stop all services
make build          # Build Docker images
make rebuild        # Rebuild and restart (no cache)
make restart        # Restart all services
make ps             # Show container status
make logs           # Tail all logs
make logs-core      # Tail core logs
make logs-webapp    # Tail webapp logs
make logs-db        # Tail database logs
```

### Ports
| Service | Port |
|---------|------|
| Adminer | 12107 |
| Webapp  | 12108 |
| Core API| 12109 |

### Database Migrations
Migrations auto-run on startup via FastAPI lifespan. Manual commands:
```bash
make db-migrate MSG="description"   # Create new migration
make db-upgrade                      # Apply all pending migrations
make db-downgrade                    # Revert last migration
make db-history                      # Show migration history
make db-current                      # Show current revision
make db-shell                        # Open psql shell
```

### Shell Access
```bash
make shell-core     # Bash into core container
make shell-webapp   # Shell into webapp container
make shell-db       # Bash into database container
```

### Utilities
```bash
make install        # Install all dependencies (Python + JS)
                    # (host-side check/test targets do this on their own when needed)
make env            # Create .env from env.example (host UID/GID) if missing
make seed           # Load the seeds and generate the programmation (idempotent)
make generate       # Regenerate the year's séances from what is already seeded
make clean          # Remove caches and build artifacts
make ip             # Show local IP and service URLs
```

`make up` creates `.env` automatically if it is missing, so a fresh clone starts with
`make up` alone. Every core setting has a default (`core/src/core/settings.py`); `.env`
only needs to exist to pin the container UID/GID and the Anthropic key.

## Claude Code Skills

Available via `/skill-name` in Claude Code:

| Skill | Description |
|-------|-------------|
| `/check` | Run code quality checks and auto-fix |
| `/db` | Database utilities (shell, history, migrations) |
| `/docker` | Docker Compose management |
| `/fix-lint` | Auto-fix linting and formatting |
| `/logs` | View Docker service logs |
| `/migrate` | Create and apply Alembic migrations |
| `/new-component` | Scaffold a React component |
| `/new-endpoint` | Scaffold a FastAPI endpoint |
| `/new-route` | Scaffold a TanStack Router route |
| `/test` | Run tests |

## Key Files Reference

| Purpose | File |
|---------|------|
| Makefile | `Makefile` |
| API client (webapp) | `webapp/src/lib/api/` |
| Route tree (webapp) | `webapp/src/router.tsx` |
| Semaine grid assembly | `webapp/src/lib/week-grid.ts` |
| Cahier journal assembly | `webapp/src/lib/day-journal.ts` |
| Récréation / pause méridienne | `webapp/src/lib/breaks.ts` |
| Frozen API responses (tests) | `webapp/src/test/fixtures/` |
| FastAPI app | `core/src/core/main.py` |
| Settings | `core/src/core/settings.py` |
| Database | `core/src/core/database.py` |
| Domain glossary | `CONTEXT.md` |
| Architecture decisions | `docs/adr/` |
| Data models | `core/src/core/models/` |
| API response schemas | `core/src/core/schemas.py` |
| Year/week/day reads | `core/src/core/services/schedule.py` |
| Matières, domaines, créneaux, séquences | `core/src/core/services/reference.py` |
| Programme browsing and search | `core/src/core/services/curriculum.py` |
| Cahier journal | `core/src/core/services/journal.py` |
| Séance CRUD rules | `core/src/core/services/planned_sessions.py` |
| Generation over HTTP | `core/src/core/services/generation.py` |
| Test DB fixtures | `core/tests/conftest.py` |
| Calendar expansion | `core/src/core/services/school_calendar.py` |
| Year generation | `core/src/core/services/planning/` |
| Seed loader | `core/src/core/services/seeding.py` |
| JSON seeds | `core/seed/` |
| Curriculum extraction | `scripts/extract_program_items.py` (+ `curriculum_map.py`) |
| React entry | `webapp/src/main.tsx` |
| Env validation | `webapp/src/env.ts` |
| Docker setup | `compose.yaml` |
| Python config | `pyproject.toml` |
| JS config | `biome.json` |
| Skills | `.claude/skills/` |

## Agent skills

### Issue tracker

Issues and specs live as markdown files under `.scratch/<feature-slug>/` in this repo. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each recorded as a `Status:` line using its own name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
