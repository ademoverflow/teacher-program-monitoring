# A semaine is rendered as the grid, and the API never returns a table row

`GET /api/weeks/{number}` answers with the shape §4.1 prints: the semaine's jours, and
inside each of them one cell per créneau of that weekday, carrying the 0, 1 or 2 séances
planned in it. Phase 5 draws the week from that one response.

Returning the semaine's séances as a flat list was the alternative, and it pushes three
things onto every reader that the server already knows. A cell can hold **two** séances —
the six commun créneaux a per-niveau méthodo splits, 208 cells over the year (ADR-0010) —
and that is a different shape from the three times where the EDT itself has two créneaux at
one hour (mardi 11h30, jeudi 11h30, jeudi 15h00): the first is one cell drawn stacked, the
second is two cells side by side, and a flat list cannot tell them apart without the
gabarit. A **jour chômé** has no séance at all and still has to be drawn, with its motif over
its usual cells (ADR-0001). And **S1 has no lundi**, so a grid that assumes four columns
breaks on the first week of the year.

Rendering every créneau of every jour, filled or not, makes all three the same case: the
shape comes from the gabarit, the content from the programmation, and an empty cell is an
empty cell whether the day was lost, the créneau unplanned, or the semaine short.

Nothing the API returns is a SQLModel row. `core/schemas.py` declares every response body,
which §6 asks for on the pattern of `routers/health.py`, and here it is not only a
convention: `program_items.search_vector` is a `tsvector` that has no JSON form at all, and
`created_at`, `updated_at` and `needs_review` are the seed's business rather than the
teacher's. `needs_review` is the one that crosses over, on `ProgramItemOut`: §8 Phase 2 made
it a claim about the extraction, and an item the browser shows should say when the source was
hard to read. It is shown and not filtered on — a filter for it would be a data-quality tool
nothing has asked for.
