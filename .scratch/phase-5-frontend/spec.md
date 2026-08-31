# Phase 5 — Frontend : navigation & programmes

MASTER-PROMPT.md §8 Phase 5. Draws §7 écrans 1 (Année), 2 (Semaine) and 4 (Programmes) on
top of the API Phase 4 finished, plus the persistent layout §7 asks for.

Phase 5 reads. It writes nothing: no cahier journal (Phase 6), no génération (Phase 6/8),
no séance editor. `webapp/src` is the only tree it touches — `core/` does not change.

## What the API already gives (recomputed against the running stack, never assumed)

| Call | Answer |
|---|---|
| `GET /api/calendar` | 36 semaines in 7/7/5/6/11, 5 vacances, `current_week_number: 1` |
| `GET /api/calendar/today` | on 2026-08-31: `school_day: null`, `next_taught_day: 2026-09-01` |
| `GET /api/timetable` | 44 créneaux — 10 lundi · 12 mardi · 12 jeudi · 10 vendredi, 6 alternants |
| `GET /api/subjects` | 12 matières with a colour, 45 domaines, all at `level: commun` |
| `GET /api/weeks/1` | 3 jours (mar/jeu/ven), 38 séances |
| `GET /api/weeks/2` | 4 jours, 50 séances, 10/12/12/10 cellules |
| `GET /api/weeks/25` | lundi 29/03 chômé — 10 cellules, 0 séance, « Lundi de Pâques » |
| `GET /api/program-items` | 220 items ; `?q=fractions&level=CM1` → 3 |

**The handoff was wrong on one point, and it matters.** It says `current_week_number` is
null on 2026-08-31 « donc null en pratique ». It is **1**: semaine 1 runs 31/08 → 04/09
(`weeks.starts_on` is the Monday) even though P1 opens on the mardi. The fallback to
`next_taught_day` is still needed — the field is genuinely null from 03/07/2027 — so the
resolution keeps both paths, but « semaine courante par défaut » already works today.

## Decisions taken before coding

Each is written up as an ADR; numbering resumes at 0023.

1. **The API client is hand-written zod, one module per resource** (ADR-0023). No
   generation from `openapi.json`: `make check` has to stay green with no stack running,
   and the three screens read 8 of the 24 endpoints. `lib/api/client.ts` holds `apiGet`
   and nothing else — the write verbs are Phase 6's, and a client with an unused `apiPost`
   would be a promise no screen keeps.
2. **The semaine grid is a time axis, not a list of rows** (ADR-0024). The 44 créneaux'
   boundaries, deduplicated, give 13 bands; a cellule spans the bands its créneau covers.
   Vendredi's two 30' cells (ADR-0003) then land correctly with no special case, and the
   grid has **no holes at all** — every band of every jour is covered by exactly one
   créneau, or is one of the two breaks.
3. **La récréation and la pause méridienne are the gaps, named** (ADR-0024). They have no
   row in `timetable_slots`; they are the two bands of the axis that no créneau covers on
   any jour. The front derives the band and takes the label from §4.1.
4. **A cellule's colour cascades `session.subject` → `slot.subject` → neutral** (ADR-0025).
   The 6 alternating créneaux carry no matière and the séance carries the resolved one;
   l'accueil has neither. One cascade, stated once, covers all three.
5. **The routes are in French** (ADR-0026). `/annee`, `/semaine/12`, `/programmes` — §10's
   « identifiants en anglais » governs code, and the address bar is what the teacher reads.
   Component and query-key identifiers stay English.

## Routes

| Path | Screen |
|---|---|
| `/` | redirect to `/annee` — Phase 6 turns it into « Aujourd'hui » |
| `/annee` | §7 écran 1 — the 5 périodes, their semaines, the vacances |
| `/semaine` | redirect to the semaine courante |
| `/semaine/$number` | §7 écran 2 — the grid of §4.1 |
| `/programmes` | §7 écran 4 — filters + recherche, state in the search params |
| `/programmes/$id` | the fiche item and « voir les séances liées » |

No `/jour` route: §7 écran 3 is Phase 6, and a dead link is worse than no link.

## Out of scope

Vue Jour, cahier journal, impression, génération, réglages, any write verb.

## Done when

Année → période → semaine navigates without a dead end; `/semaine` opens the semaine
courante; « fractions » returns the 3 CM1 items; the grid draws lun/mar/jeu/ven with the
hour bands, the CM1/CM2 splits and the matière colours; `make check` and `make test` green;
`docker compose down -v && make up && make seed` still idempotent.
