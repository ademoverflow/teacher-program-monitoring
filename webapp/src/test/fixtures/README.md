# Frozen API responses

Captured verbatim from a seeded stack (`make up && make seed`) so the front's assembly can
be tested with no network and no database:

| File | `GET` | Why this one |
|---|---|---|
| `week-01.json` | `/api/weeks/1` | S1 has **three jours** — the year opens on a mardi — 38 séances, both kinds of split (a cellule holding two séances at mardi 09h10, two cellules side by side at mardi 11h30) and vendredi's off-grid 11h30-12h00 / 12h00-12h30 |
| `week-25.json` | `/api/weeks/25` | lundi 29/03/2027 is **chômé**: 10 cellules, 0 séance, `off_reason` « Lundi de Pâques » |
| `calendar.json` | `/api/calendar` | 36 semaines in 7/7/5/6/11, 5 vacances, `current_week_number` |
| `subjects.json` | `/api/subjects` | 12 matières with their colour, 45 domaines |
| `program-items-fractions-cm1.json` | `/api/program-items?q=fractions&level=CM1` | the 3 items §8 Phase 5 names |

Re-capture with the same URLs when the API's shapes change; a test that fails against a
re-captured fixture is the point.
