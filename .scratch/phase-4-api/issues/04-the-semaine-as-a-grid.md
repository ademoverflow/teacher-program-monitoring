# 04 - Render a semaine as the grid, not as a list

Type: task
Status: resolved
Blocked by: 02

`GET /api/weeks/{number}` returns the semaine the way §4.1 prints it: one entry per jour de
classe, and inside it one cell per créneau of that weekday, each carrying the 0, 1 or 2
séances planned in it.

Three traps, all recomputed rather than assumed:

- **A cell can hold two séances** — 6 créneaux commun are split by niveau (ADR-0010), which
  is 208 cells of the year. That is not the same thing as the cells where the EDT itself has
  two créneaux at one time (mardi 11h30 CM1/CM2, jeudi 11h30, jeudi 15h00): the first is one
  créneau, the second is two.
- **S1 has no lundi.** 38 séances, not 50. A response that assumes four jours breaks.
- **A jour chômé keeps its cells, empty**, and carries its `off_reason` (ADR-0001).

The response carries the previous and next semaine numbers so §7's week navigation needs
nothing else.

**Done when**: S1 renders three jours and 38 séances, a full semaine 50, the semaine
holding lundi de Pâques renders a jour chômé with a motif and no séance, and the mardi
09h10 cell of a full semaine carries two séances, CM1 and CM2.
