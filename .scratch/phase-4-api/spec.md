# Phase 4 — API backend

MASTER-PROMPT.md §8 Phase 4. Exposes what Phases 1 to 3 put in the database, and adds the
one thing the database does not have yet: a cahier journal.

Phase 4 exposes, it does not display. No React component, no TanStack route, no change to
`webapp/src` — that is Phase 5.

## What is already in the database (recomputed, never assumed)

| | |
|---|---|
| `subjects` · `domains` | 12 · 45 |
| `periods` · `weeks` | 5 · 36 (7/7/5/6/11) |
| `school_days` | 143, of which **139** taught |
| `timetable_slots` | 44 — 10 lundi · 12 mardi · 12 jeudi · 10 vendredi |
| `program_items` | 220, `search_vector` generated + GIN |
| `sequences` · `sequence_sessions` | 120 · 36 |
| `planned_sessions` | **1740**, of which 208 cells carry two (ADR-0010) |
| `planned_session_program_items` | 4040 |
| `app_settings` | 2 alternances |
| `journal_entries` | **0** — Phase 4 is what first writes one |

Séances per semaine: S1 = 38 (no lundi), a full semaine = 50, S36 = 50.

## Decisions taken before coding

Each is written up as an ADR; numbering resumes at 0018.

1. **The tests get a real Postgres, in CI as well** (ADR-0018). Phase 4 is almost entirely
   database, and a suite that skips its own phase in CI is not a suite. `.github/workflows`
   gains a `postgres:17` service; a session-scoped fixture migrates it with
   `alembic upgrade head`, then seeds it once.
2. **A router test shares the test's transaction** (ADR-0019). `app.dependency_overrides`
   hands the endpoint the very session the test opened, bound to a connection whose outer
   transaction is rolled back at the end — so an endpoint that commits still leaves nothing
   behind. The client is `httpx.AsyncClient` over `ASGITransport` rather than `TestClient`:
   `TestClient` drives the app from another thread's event loop, and an asyncpg connection
   cannot cross event loops.
3. **The generation is synchronous, and confirmation is a parameter** (ADR-0020). It takes
   0.5 s. `POST /api/generation` refuses with 409 when a targeted période is already under
   way and the caller did not say `confirm`; `GET /api/generation` says which périodes those
   are, so the UI can ask before it posts.
4. **A cahier journal is initialised once, from the day's séances, and never over itself**
   (ADR-0021). `core/services/journal.py`. A line takes the créneau's label as its
   discipline (the matière's, where the créneau alternates and the label names a pair), the
   créneau's `duration_minutes`, and the séance's title above its objectifs — which is what
   `docs/exemple-cahier-journal-quotidien.pdf` prints in those two columns.
5. **A semaine is rendered as the grid, not as a list of séances** (ADR-0022). One request
   gives every créneau of every jour with the 0, 1 or 2 séances in it, so Phase 5 draws
   §4.1 without a second call. Response schemas are declared for the API and never the
   SQLModel rows.

## Endpoints

All under `/api`.

| Method | Path | What |
|---|---|---|
| GET | `/calendar` | the year: périodes → semaines, vacances, semaine courante |
| GET | `/calendar/today` | today, and the next jour de classe if today is not one |
| GET | `/timetable` | the 44 créneaux of the gabarit |
| GET | `/subjects` | matières with their domaines (filters, colours) |
| GET | `/weeks/{number}` | the semaine as a grid: jours × créneaux × séances |
| GET | `/days/{date}` | the jour: its séances in order, with items de programme |
| GET | `/sessions/{id}` | one séance |
| POST | `/sessions` | add a séance to a (jour, créneau, niveau) |
| PATCH | `/sessions/{id}` | edit title, objectifs, contenu, matériel, statut, position |
| DELETE | `/sessions/{id}` | remove a séance |
| GET | `/program-items` | filtered by niveau/matière/domaine, `?q=` full-text |
| GET | `/program-items/{id}` | one item, with its source reference |
| GET | `/sessions?program_item_id=` | « voir les séances liées » (§7 écran 4) |
| GET | `/journal/{date}` | the day's cahier journal |
| POST | `/journal/{date}/initialise` | fill it from the day's séances, once |
| POST | `/journal/{date}/entries` | add a ligne |
| PATCH | `/journal/entries/{id}` | edit a ligne |
| DELETE | `/journal/entries/{id}` | remove a ligne |
| PUT | `/journal/{date}/order` | reorder the lignes |
| GET | `/generation` | which périodes are under way, and what is written |
| POST | `/generation` | run it (whole year or given périodes), return the report |
| GET | `/settings` | the réglages |
| PUT | `/settings/{key}` | change one, validated against its own vocabulary |

## Out of scope

- No auth (§10): no `get_current_user`, no login router, no roles.
- No AI: `journal_revisions` stays empty and unexposed — Phase 7.
- No frontend.
- No schema migration is expected: Phase 4 reads what Phase 3 wrote and writes
  `journal_entries`, both of which already have their tables.
