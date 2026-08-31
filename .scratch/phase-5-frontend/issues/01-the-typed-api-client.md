# 01 - Grow the typed client, one module per resource

Type: task
Status: open

`webapp/src/lib/api.ts` knows one endpoint. The three screens read eight, against 44
OpenAPI schemas. Split it: `lib/api/client.ts` for `apiGet`, `ApiError` and the query
string, then one module per resource (`calendar`, `weeks`, `subjects`, `program-items`,
`planned-sessions`, `health`) plus `shared.ts` for the refs every response embeds
(`SubjectRef`, `DomainRef`, `SlotSummary`, `PlannedSessionSummary`, `Level`, `Weekday`).

Hand-written zod, not generated: `make check` runs with no stack, so a generator would
need a committed `openapi.json` and a build step for eight endpoints' worth of shapes.
Schemas declare the fields the screens read; zod strips the rest, so the API may grow
without breaking the front.

**No write verbs.** `apiPost`/`apiPatch`/`apiDelete` are Phase 6 and ship with the screen
that needs them.

**Done when**: every call the three screens make goes through a named function in
`lib/api/`, `tsc --noEmit` is clean, and `App.test.tsx`'s health case still passes against
the moved module.
