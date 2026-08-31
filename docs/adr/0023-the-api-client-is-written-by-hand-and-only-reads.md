# The typed client is written by hand, one module per resource, and only reads

`webapp/src/lib/api/` holds a `client.ts` with `apiGet`, `ApiError` and the query string,
and one module per resource — `calendar`, `weeks`, `subjects`, `program-items`, `health` —
plus a `shared.ts` for the refs several responses embed. The zod schemas are typed out
against `core/src/core/schemas.py` rather than generated from `openapi.json`.

Generating them was the alternative, and it is the one that looks obviously right: the API
declares 44 schemas and the front reads a dozen. It loses on the build. `make check` and
`make test-webapp` run with no stack up, so a generator would have to run against a
committed `openapi.json` — which is a snapshot written by hand in a different sense, kept
fresh by nobody, plus a code generator in the toolchain and a `dist` of generated types in
review. Against that, the front's three screens read eight endpoints, and zod strips what a
schema does not declare, so the API may grow a field without breaking anything here.

The price is real and worth naming: nothing mechanically stops the hand-written schemas
drifting from the API's. What guards them is that the tests parse **frozen responses
captured from a seeded stack** (`webapp/src/test/fixtures/`) through those very schemas, so
a shape that no longer matches fails on re-capture rather than in the teacher's browser.

## The client only reads

There is no `apiPost`, `apiPatch` or `apiDelete`. Phase 5 draws écrans 1, 2 and 4, all of
which read; the CRUD of `planned_sessions` and the cahier journal are Phase 6's, and §8 asks
each phase not to anticipate the next. A half-abstraction was the worry — a client with one
verb — and it is the smaller cost: an unused write verb is a promise no screen keeps, and
the shape the write verbs want (an error body the UI can show, an optimistic update) is
knowledge Phase 6 will have and Phase 5 does not.
