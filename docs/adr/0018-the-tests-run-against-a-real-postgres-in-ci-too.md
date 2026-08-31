# The tests run against a real Postgres, in CI as well as in the container

`.github/workflows/check.yml` starts a `postgres:17` service and points `DATABASE_URL` at
it, and `core/tests/conftest.py` brings a blank database to `head` with
`alembic upgrade head`, loads the seeds and generates the year — once for the whole suite.
The 17 tests of Phases 2 and 3 that used to skip in CI now run there, and the twelve router
modules of Phase 4 run beside them: 207 green, no skips.

The alternative was to keep faking the database. Phase 3 could afford it — the planner is
pure, and `plan_input_from_seeds` fed it the same shape the database does, which is what
let its placement rules be covered in CI. Phase 4 has no such seam: an endpoint is a query,
and a test that mocks the query tests the mock. The choice was therefore between a Postgres
in CI and a phase whose acceptance criterion — « tests pytest par router (TestClient + DB de
test) » — was verified only on the developer's machine.

The fixtures still skip where no database answers, so `make test-core-host` on a laptop with
no stack running is a partial run rather than a failure, and `make test-core` in the
container is unchanged. The price is a CI job that is a minute longer and a `greenlet`
dependency named explicitly: SQLAlchemy installs it itself only on the platforms it ships a
wheel for, and without it the async engine cannot connect at all.

The fill is deterministic — it generates against 31/08/2026, the day before the pupils come
back — so the year the tests read is the same in June as in September. It commits, which
means running the suite against the development database re-seeds and re-generates it. Both
are idempotent and neither touches a cahier journal (§10), so that is what `make seed` would
have done anyway.
