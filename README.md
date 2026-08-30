# Teacher Program Monitoring

## Description

A project for my wife, to help her monitoring her teacher journey :)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Webapp (React SPA)                        │
│                    localhost:12108                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │
│  │  TanStack   │ │  TanStack   │ │    Tailwind CSS     │    │
│  │   Router    │ │    Query    │ │                     │    │
│  └─────────────┘ └─────────────┘ └─────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core API (FastAPI)                         │
│                   localhost:12109                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │
│  │   SQLModel  │ │     JWT     │ │      Alembic        │    │
│  │     ORM     │ │    Auth     │ │    Migrations       │    │
│  └─────────────┘ └─────────────┘ └─────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │ TCP
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL 17                              │
│                   db:5432                                    │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, TanStack Router/Query, Tailwind CSS |
| AI | Anthropic API (daily-journal feedback) |
| Backend | Python 3.13, FastAPI, SQLModel, Alembic, Pydantic |
| Database | PostgreSQL 17 |
| Auth | None — local, single-user application |
| Package Managers | pnpm (Node), uv (Python) |
| Code Quality | Biome (JS/TS), Ruff + MyPy (Python) |
| Containers | Docker, Docker Compose |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [pnpm](https://pnpm.io/installation) (v10.23.0+)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)

## Quick Start

### 1. Start the Development Stack

```bash
make up
```

`make up` creates `.env` from `env.example` (with this host's UID/GID) if it is
missing, builds the images and starts every service. No manual configuration is
required: every backend setting has a sensible default. Edit `.env` afterwards to
set `ANTHROPIC_API_KEY` if you want the AI feedback feature.

### 2. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| Webapp | http://localhost:12108 | React frontend |
| Core API | http://localhost:12109 | FastAPI backend |
| API Docs | http://localhost:12109/docs | Swagger UI |
| Adminer | http://localhost:12107 | Database admin |

## Project Structure

```
/
├── core/                    # Python FastAPI backend
│   ├── src/core/           # Application source
│   ├── tests/              # Backend tests
│   ├── Dockerfile          # Multi-stage Docker build
│   ├── pyproject.toml      # Dependencies
│   └── README.md           # Backend documentation
│
├── webapp/                  # React TypeScript frontend
│   ├── src/                # Application source
│   ├── Dockerfile          # Multi-stage Docker build
│   ├── package.json        # Dependencies
│   └── README.md           # Frontend documentation
│
├── scripts/                 # Development utilities
│   ├── clean-cache.sh      # Clear build caches
│   ├── clean-node.sh       # Clean node_modules
│   ├── code-quality-checkers.sh
│   └── update-package-version.sh
│
├── .github/                 # CI/CD workflows
│   └── workflows/
│       ├── commitlint.yml  # Commit message validation
│       └── semantic-release.yml
│
├── docs/                    # Source PDFs (official programmes, timetable, methodologies)
├── MASTER-PROMPT.md        # Project reference: scope, data model, phased plan
├── compose.yaml            # Docker Compose config
├── pyproject.toml          # Root Python config + tools
├── package.json            # Root Node config
├── biome.json              # JS/TS linting config
├── CLAUDE.md               # AI assistant guide
└── env.example             # Environment template
```

## Development

### Running Locally (without Docker)

**Backend:**
```bash
cd core
uv sync
uv run python -m core
```

**Frontend:**
```bash
cd webapp
pnpm install
pnpm dev
```

### Code Quality

```bash
make check          # Everything (Ruff + MyPy + Biome)
make check-python   # Ruff format/lint/import-sort + MyPy
make check-webapp   # Biome lint + format
make fix            # Auto-fix Python formatting and import order
```

### Testing

```bash
make test-core      # pytest, inside the core container
make test-webapp    # vitest, on the host
```

### Database Migrations

Migrations auto-run on app startup. For manual control:

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Environment Variables

See `env.example` for all available options. Key variables:

All variables are optional except `USER_ID`/`USER_GID` (container file ownership).

| Variable | Default | Description |
|----------|---------|-------------|
| `USER_ID` / `USER_GID` | host UID/GID | UID/GID used inside the containers |
| `DATABASE_URL` | `postgresql://admin:admin@db:5432/db` | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | *(empty)* | Anthropic key; empty disables the AI feedback feature |
| `ANTHROPIC_MODEL` | `claude-sonnet-5` | Model used for journal feedback |
| `DEV_MODE` | `false` | Enable development features (hot reload) |

## Documentation

- [Backend (Core) Documentation](core/README.md)
- [Frontend (Webapp) Documentation](webapp/README.md)
- [AI Assistant Guide](CLAUDE.md)
- [Project reference & phased plan](MASTER-PROMPT.md)

## License

MIT
