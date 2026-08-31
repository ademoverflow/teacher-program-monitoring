# A router test shares the test's transaction, and speaks to the app over ASGI

`core/tests/conftest.py` binds each test's `AsyncSession` to a connection whose outer
transaction the fixture owns, with `join_transaction_mode="create_savepoint"`, and hands
that session to the app through `app.dependency_overrides[get_session]`. The rollback at the
end undoes everything — including the writes of an endpoint that called `commit()`, which
only releases a savepoint inside the fixture's transaction.

Without the override, the endpoint would open its own session from the module-level engine
and its writes would land in the development database for good; without the savepoint join,
`POST /api/sessions` would commit and the rollback would have nothing left to undo. Both are
needed, and neither is visible from a test that only reads.

The client is `httpx.AsyncClient` over `ASGITransport`, not FastAPI's `TestClient`. §8 asks
for `TestClient`, and it cannot be used here: it drives the app from a worker thread running
its own event loop, and an asyncpg connection belongs to the loop that opened it — so the
session the fixture built on the test's loop cannot serve a request on the client's. The two
are the same thing at the HTTP level (`TestClient` *is* an httpx client over a portal), and
`test_health.py` still uses `TestClient`, being the one endpoint that reads nothing.

The lifespan is not entered, which is deliberate: `core.main.app`'s lifespan runs
`alembic upgrade head`, and migrating is the fixture's job here — once for the suite rather
than once per test. `TestClient(app)` at module level does not enter it either, which is why
`test_health.py` has always passed with no database at all.
