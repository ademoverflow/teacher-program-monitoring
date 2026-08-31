# 02 - Vue Jour: the cahier journal

Type: task
Status: ready-for-agent
Blocked by: 01

`/jour/$date` — §7 écran 3, « cœur de l'app ». Two calls: `GET /api/days/{date}` for the
programmation and `GET /api/journal/{date}` for the cahier journal.

**The header is the print model's header** (`docs/exemple-cahier-journal-quotidien.pdf`):
« Période 1 – Semaine 2 » over « lundi 7 septembre 2026 » with « CM1-CM2 – Cycle 3 » to
its right. Previous/next jour from `previous_day`/`next_day`. A chip says « Aujourd'hui »
or « Prochain jour de classe » where the date earns it.

**The table is the print model's table**: *Discipline - Durée* | *Objectif(s) et
compétence(s)* | *Bilan*, plus a controls column that does not print. La récréation and
la pause méridienne print **across** it, found from the day's own créneaux the way
`week-grid.ts` finds them in a semaine (ADR-0024) — only their names are written down.

**Initialisation** (ADR-0028): today or a past day fills itself on opening; a future day
shows « Initialiser depuis la programmation ». 201 and 200 both land on the same rendered
day, so nothing branches on them beyond what the button says afterwards.

**A jour chômé says why** — « Lundi de Pâques », `initialised: false`, no séance to copy —
rather than drawing an empty table. **A date that is not a jour de classe** (a mercredi, a
week-end, des vacances) is a 404: say so, with a link back to the semaine.

**Done when**: 2026-09-07 draws 12 lignes with the récréation after « Calcul mental » and
la pause méridienne after « Dictée du jour » ; 2027-03-29 draws no table and names its
motif ; 2026-09-02 says it is not a jour de classe.
