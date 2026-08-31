# 01 - The typed client learns to write

Type: task
Status: ready-for-agent

ADR-0023 left the write verbs to this phase on purpose. Add them to
`webapp/src/lib/api/client.ts`, one `request()` behind `apiGet`, `apiPost`, `apiPatch`,
`apiPut` and `apiDelete`.

**The error is the point.** FastAPI answers `{"detail": "…"}` in French — `PUT /order`
with a partial list says « L'ordre doit nommer exactement les lignes du cahier journal de
ce jour, une fois chacune », and that is a sentence the teacher can act on. `ApiError`
gains `detail: string | null`, read from the body when the body has one, and its `message`
becomes that sentence where there is one. A body that is not JSON, or has no `detail`,
falls back to what the client already says.

`apiDelete` answers 204 with no body: parse nothing.

Then one module per resource, hand-written zod against `core/src/core/schemas.py`
(ADR-0023): `lib/api/days.ts` (`DayDetail`, `PlannedSessionDetail`),
`lib/api/journal.ts` (`JournalDay`, `JournalEntry`, and the five calls),
`lib/api/planned-sessions.ts` (the statut).

`test/app.tsx`'s `stubApi` only answers `GET`. Teach it the other verbs — a route key
becomes `"POST /api/journal/2026-09-07/initialise"`, a bare path still means `GET` — and
let a stub answer with a status so a test can drive a 400.

**Done when**: `stubApi` can answer a `PATCH`, an `ApiError` from a `{"detail": …}` body
carries that sentence as its message, and the five journal calls parse the frozen
fixtures.
