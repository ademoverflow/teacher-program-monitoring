# Phase 6 — Cahier journal

MASTER-PROMPT.md §8 Phase 6. Draws §7 écran 3 (Vue Jour / Cahier journal), makes
« Aujourd'hui » the home page, and teaches the typed client to write. `core/` does not
change: Phase 4 already ships every endpoint this needs.

Phase 6 is the first phase whose screens **write**. That is what shapes every decision
below.

## What the API already gives (recomputed against the running stack, never assumed)

| Call | Answer |
|---|---|
| `GET /api/calendar/today` | on 2026-08-31: `school_day: null`, `next_taught_day` 2026-09-01 |
| `GET /api/days/2026-09-07` | 12 séances, `has_journal: false`, prev 2026-09-04, next 2026-09-08 |
| séances per jour, semaine 2 | lundi **12** · mardi **14** · jeudi **13** · vendredi **11** |
| `GET /api/journal/2026-09-07` | `initialised: false`, 0 ligne, S2, P1-S2 |
| `POST …/2026-09-07/initialise` | **201** + 12 lignes ; called again **200** + 12 |
| `GET /api/journal/2027-03-29` | `is_off: true`, « Lundi de Pâques », 0 ligne ; initialise → **200**, 0 ligne |
| `GET /api/journal/2026-09-02` | **404** (a mercredi) |
| `PUT …/order` with 11 of 12 ids | **400** `{"detail": "L'ordre doit nommer exactement …"}` |
| DB at rest | 0 `journal_entries`, 143 `school_days` (139 taught), 1740 `planned_sessions` |

Two things the handoff did not say, both checked in `planning/writer.py`:

- **`_untouchable_days` excludes a jour de classe from re-generation as soon as it holds
  one ligne de cahier journal** — not just from being overwritten, from being written at
  all. So initialising a day is a decision about that day's programmation, not only about
  its cahier journal. That is what settles decision 2.
- A day's séances carry their créneau, so **the day's own récréation and pause méridienne
  can be found the same way the semaine grid finds them** (ADR-0024): they are the gaps
  between the day's créneaux, and only their names are written down.

## Decisions taken before coding

Each is written up as an ADR; numbering resumes at 0027.

1. **The client writes with four verbs, and an error carries the server's sentence**
   (ADR-0027). `apiPost` / `apiPatch` / `apiPut` / `apiDelete` beside `apiGet`, all four
   through one `request()`. `ApiError` grows `detail`: FastAPI answers
   `{"detail": "L'ordre doit nommer exactement …"}` in French, and that sentence is the
   only thing the teacher can act on. No optimistic updates — the mutations return the row
   they wrote, and it goes into the query cache verbatim.
2. **A cahier journal is initialised for the day being taught, and on request for any
   other** (ADR-0028). Opening a jour de classe that is today or past fills it; a future
   day gets a « Initialiser depuis la programmation » button. Auto-filling every day the
   teacher merely looks at would freeze its programmation against a re-generation, which
   is a silent wrong answer, not a confirmation dialog.
3. **A field saves when it is left, and the row keeps the server's answer** (ADR-0029).
   Blur, not keystroke, not a save button: a `PATCH` per keystroke is wrong and a debounce
   loses the last edit. Escape reverts, Entrée commits a one-line field. What comes back
   is written into the cache, so nothing refetches under the teacher's cursor.
4. **Reordering is two buttons and the whole list** (ADR-0029). `PUT /{date}/order` is
   all-or-nothing, so the view sends every id every time. No drag-and-drop dependency.
5. **The printable cahier journal is the vue Jour under `@media print`** (ADR-0030), not a
   second route: same data, same URL, and the teacher prints the page she is on. The
   fields auto-size so what she reads is what prints.
6. **The statut is written on the ligne and belongs to the séance** (ADR-0031). The
   cahier journal is the page; a ligne that came from a séance carries that séance's
   statut selector and a ligne the teacher wrote herself carries none — which is what
   tells the two apart. « Programmation du jour » sits below as read-only reference for
   what a ligne does not copy: séquence, items de programme, matériel, horaires.
7. **Écran 5 (Génération / Réglages) stays out.** §8 assigns it to no phase; it is the one
   screen that can rewrite 1740 séances and it needs the confirmation flow of ADR-0020.
   Half of it would be worse than none. Reported, not wired.

## Routes

| Path | Screen |
|---|---|
| `/` | redirect to `/aujourdhui` — §8 makes « Aujourd'hui » the home page |
| `/aujourdhui` | resolves `next_taught_day` and replaces itself with `/jour/$date` |
| `/jour/$date` | §7 écran 3 — the cahier journal, the programmation, the print view |

`/annee`, `/semaine`, `/semaine/$number`, `/programmes`, `/programmes/$id` do not move.
Three dead ends of Phase 5 become links to `/jour/$date`: the semaine grid's jour headers
(§7 écran 2's « clic sur un jour → vue Jour »), and the séances liées of an item de
programme.

## Out of scope

- The **panneau Feedback IA** (§7 écran 3, last line) is Phase 7.
- **Écran 5** — see decision 7.
- Creating or deleting a **séance** (`POST`/`DELETE /api/planned-sessions`): the vue Jour
  edits a séance's statut and nothing else. Deleting a séance would leave an alternating
  cellule with no colour, which the Phase 5 report already lists as a known hole.
