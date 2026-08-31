# 07 - The cahier journal: initialise it once, then let it live

Type: task
Status: ready-for-agent
Blocked by: 05

There are zero `journal_entries` today. §8 Phase 4 asks for « l'initialisation du cahier
journal d'un jour depuis ses séances », plus the CRUD and the reordering.

The service lives in `core/src/core/services/journal.py`. A ligne copies, from the séance
and its créneau:

- `discipline` — the créneau's label, or the matière's where the créneau alternates and the
  label names a pair (« Histoire ou Géographie »), suffixed with the niveau when the séance
  is not commun;
- `duration_minutes` — the créneau's, not `ends_at - starts_at` (ADR-0003);
- `objectives` — the séance's title, and its objectifs under it, which is what
  `docs/exemple-cahier-journal-quotidien.pdf` prints in that column;
- `position` — the order of the day;
- `bilan` and `notes` — empty. The bilan is written after the lesson.

**A day that already has a cahier journal is never re-initialised**, not even partly: the
endpoint returns what is there and says it created nothing. That is the §10 rule the
generator already honours (`_untouchable_days`), stated on the other side.

Endpoints: `GET /api/journal/{date}`, `POST /api/journal/{date}/initialise`,
`POST /api/journal/{date}/entries`, `PATCH` and `DELETE` on `/api/journal/entries/{id}`,
and `PUT /api/journal/{date}/order` taking the ids in their new order.

**Done when**: initialising a lundi gives 12 lignes in the order of the day with the right
durées; initialising again changes nothing; a ligne edits, a ligne is added, a ligne is
deleted, and the order is rewritten by ids.
