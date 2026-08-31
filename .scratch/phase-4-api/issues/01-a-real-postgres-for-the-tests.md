# 01 - Give the test suite a real Postgres, in CI too

Type: task
Status: resolved

Phase 4 is almost entirely database. The two DB-backed test modules of Phases 2 and 3
skip when no Postgres answers, which is every CI run: 115 green, 17 skipped. Adding
routers on top of that would leave the phase's own acceptance criterion — « tests pytest
par router (TestClient + DB de test) » — unverified everywhere it matters.

Add a `postgres:17` service to `.github/workflows/check.yml` and point `DATABASE_URL` at
it. Move the two duplicated `session` fixtures into `core/tests/conftest.py`, and have a
session-scoped fixture bring a blank database up to `head` with `alembic upgrade head`
before anything runs.

The per-test session must survive an endpoint that commits: bind it to a connection whose
outer transaction the fixture rolls back, with `join_transaction_mode="create_savepoint"`.

**Done when**: `make test-core-host` runs the whole suite green against a local Postgres
with zero skips, and still skips cleanly with no database at all.
