# Frozen API responses

Captured verbatim from a seeded stack (`make up && make seed`) so the front's assembly can
be tested with no network and no database:

| File | `GET` | Why this one |
|---|---|---|
| `week-01.json` | `/api/weeks/1` | S1 has **three jours** — the year opens on a mardi — 38 séances, both kinds of split (a cellule holding two séances at mardi 09h10, two cellules side by side at mardi 11h30) and vendredi's off-grid 11h30-12h00 / 12h00-12h30 |
| `week-25.json` | `/api/weeks/25` | lundi 29/03/2027 is **chômé**: 10 cellules, 0 séance, `off_reason` « Lundi de Pâques » |
| `calendar.json` | `/api/calendar` | 36 semaines in 7/7/5/6/11, 5 vacances, `current_week_number` |
| `today.json` | `/api/calendar/today` | on 2026-08-31: `school_day: null`, `next_taught_day` mardi 01/09 — the home page's fallback, which is the only path the year currently takes |
| `subjects.json` | `/api/subjects` | 12 matières with their colour, 45 domaines |
| `program-items-fractions-cm1.json` | `/api/program-items?q=fractions&level=CM1` | the 3 items §8 Phase 5 names |
| `day-2026-09-01.json` | `/api/days/2026-09-01` | la rentrée, where `/aujourdhui` lands: 14 séances, **no `previous_day`** |
| `journal-2026-09-01.json` | `/api/journal/2026-09-01` | its cahier journal, never filled |
| `day-2026-09-07.json` | `/api/days/2026-09-07` | a full lundi: **12 séances**, whose créneaux leave exactly the two gaps that are la récréation and la pause méridienne |
| `journal-2026-09-07.json` | `/api/journal/2026-09-07` | the same day **initialised**: 12 lignes, the alternating créneau filed under « Arts plastiques », the vendredi-style durée/borne split visible on l'accueil (10 min) |
| `journal-2026-09-07-vide.json` | `/api/journal/2026-09-07` | the same day before it is filled: `initialised: false`, 0 ligne |
| `day-2027-03-29.json` | `/api/days/2027-03-29` | a **jour chômé**: `is_off`, « Lundi de Pâques », 0 séance |
| `journal-2027-03-29.json` | `/api/journal/2027-03-29` | its cahier journal: legal, empty, and never fillable — there is nothing to copy |

Re-capture with the same URLs when the API's shapes change; a test that fails against a
re-captured fixture is the point.

`journal-2026-09-07.json` is the one that is not a plain `GET` of a freshly seeded stack: it
needs `POST /api/journal/2026-09-07/initialise` first, which **writes**. Re-capture it with

```
curl -sX POST localhost:12109/api/journal/2026-09-07/initialise > /dev/null
curl -s localhost:12109/api/journal/2026-09-07 | python3 -m json.tool > journal-2026-09-07.json
```

and delete the day's lignes afterwards if the development database should stay at rest — a
day holding a cahier journal is a day `make generate` will not write again (ADR-0020).
