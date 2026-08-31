# 04 - Vue Semaine: the grid of §4.1

Type: task
Status: resolved
Blocked by: 02

The heart of the phase, from the single `GET /api/weeks/{n}` (ADR-0022).

**The axis is derived, not written down.** Take every créneau's `starts_at`/`ends_at` in
the response, sort the distinct boundaries, and the consecutive pairs are the grid's
bands — 13 of them for this EDT. A cellule spans the bands its créneau covers. Two of the
13 are covered by no créneau on any jour: those are la récréation (10h15-10h45) and la
pause méridienne (12h30-14h00), which have no row in `timetable_slots` and are drawn as
labelled bands.

Three traps, each an assembly test on a frozen response, no network:

- **S1 has three jours.** Columns come from `week.days`, never from a constant.
- **A jour chômé keeps its cellules, empty**, and shows its `off_reason` over them.
- **A cellule holds 0, 1 or 2 séances.** Two séances stack *inside one box* (a commun
  créneau split by niveau, ADR-0010) with CM1/CM2 badges; two créneaux at one hour are two
  boxes *side by side* (mardi 11h30, jeudi 11h30, jeudi 15h00). Lanes within a jour come
  from grouping its créneaux by `(starts_at, ends_at)`.

A cellule prints the créneau's `duration_minutes`, never `ends_at - starts_at` (ADR-0003):
vendredi's calcul mental is 15' in a 20' band.

Previous/next semaine come from the response. `/semaine` with no number resolves
`current_week_number`, falling back to the semaine of `next_taught_day`.

**Done when**: S1 draws 3 columns and 38 séances, S2 draws 4 and 50, S25's lundi is an
empty chômé column reading « Lundi de Pâques », mardi 09h10 of S2 is one box with two
séances and mardi 11h30 is two boxes.
