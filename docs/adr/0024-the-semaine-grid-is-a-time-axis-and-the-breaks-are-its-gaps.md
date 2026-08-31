# The semaine grid is a time axis, and la récréation is a gap in it

`buildWeekGrid` takes every boundary the semaine's créneaux name, sorts them, and makes the
consecutive pairs the grid's **bands** — thirteen for this EDT. A cellule spans the bands
its créneau covers, and a jour column is a grid of those bands by its lanes.

The obvious alternative is one row per printed time range, and it does not fit this
timetable. Vendredi's two 30' cells are stored as 11h30-12h00 and 12h00-12h30 rather than on
the 11h30-12h15 / 12h15-12h30 rows the other jours use, because the printed durations could
not fit the printed rows (ADR-0003). A grid of distinct ranges therefore has twelve rows, of
which two are vendredi's alone and two are the other three jours' alone — four rows with
holes in them, and the holes are not real: something is taught in every one of those minutes
on every jour.

Derived bands have no holes at all. Every band of every jour is covered by exactly one
créneau — the tests assert it, summing lane spans band by band — except two, which no
créneau of any jour covers.

## Those two gaps are la récréation and la pause méridienne

`timetable_slots` has no row for 10h15-10h45 or for 12h30-14h00. §4.1 prints them both, and
so does the cahier journal, so the grid has to draw them.

They are found rather than declared: a band no créneau covers is a break. What is declared
is only the name, in a four-line table in `week-grid.ts` holding what §4.1 calls them. The
alternative — two constants with hard-coded times drawn unconditionally — states the same
two facts twice, and would keep drawing a récréation at 10h15 if the EDT ever moved one.
A gap the table does not name still draws, unlabelled: the hole is the data, the name is the
decoration.

## The columns come from the response

Three columns in S1, four elsewhere: `week.days` is the source, never a constant (ADR-0022).
A jour chômé keeps its column and its cellules, drawn empty under its motif (ADR-0001).
