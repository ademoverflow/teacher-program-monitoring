# A créneau's boundaries come from the timetable grid, its duration from the cell

`timetable_slots` stores `starts_at`/`ends_at` and, separately, `duration_minutes`. For 43 of
the 44 créneaux the two agree. They disagree for Friday's calcul mental, where `docs/edt.pdf`
prints the row as 9h55-10h15 like every other day but annotates the cell "15'" instead of "20'":
the slot keeps the grid's 9h55-10h15 and records a duration of 15 minutes.

The PDF does not resolve which 15 minutes of that 20-minute row are meant, and both narrower
readings (9h55-10h10, 10h00-10h15) invent a five-minute hole the source does not show. Keeping
the printed boundaries and the printed duration side by side loses nothing and keeps the weekly
grid aligned across the four days; the price is that `ends_at - starts_at != duration_minutes`
for that one row, so code must use `duration_minutes` when it means teaching time and the
boundaries when it means position in the grid. Confirmed with the teacher on 2026-08-30.

## Why Friday's late morning is stored differently

Friday's two 30' cells — Lecture fluence and Dictée bilan/Poésie — are stored as 11h30-12h00 and
12h00-12h30 rather than on the 11h30-12h15 / 12h15-12h30 grid rows the other days use. That
looks like the opposite call, and it is worth saying why it is not.

Keeping the grid's boundaries only works while the printed duration *fits inside* the printed
row. It does for calcul mental: 15 minutes sit inside a 20-minute row, and the slack is real
teaching slack. It cannot for the dictée bilan, whose cell says 30' in a 15-minute row — no
reading of that row holds 30 minutes, and stretching it past 12h30 would run into the pause
méridienne. The two cells together span 11h30 to 12h30 exactly, which §4.1 states outright
("30', enchaîné avec la fluence sur 11h30-12h30"), so the split is arithmetic, not a choice.

The rule, stated precisely: keep the grid's boundaries and record the cell's duration whenever
the duration fits the row; where a cell's duration cannot fit its printed row, the durations
win and the boundaries are recomputed from them.
