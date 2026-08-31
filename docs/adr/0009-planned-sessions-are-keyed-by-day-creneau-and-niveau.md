# A séance is identified by its jour de classe, its créneau and its niveau

`planned_sessions` carries a unique constraint on `(school_day_id, timetable_slot_id,
level)`, named `uq_planned_sessions_day_slot_level`. That is what the generator upserts
on, and without it a second run would insert the whole year alongside the first — the
same trap Phase 2 hit on `program_items` (ADR-0005).

`(school_day_id, timetable_slot_id)` reads like enough and is not: a commun créneau that
carries per-niveau content becomes two séances that differ only by their niveau
(ADR-0010), and they have to be able to sit side by side. Nothing needs
`NULLS NOT DISTINCT` here — all three columns are `NOT NULL`.

The consequence is that the generator can never plan the same créneau twice on the same
day for the same niveau, which is exactly the promise the EDT makes: a créneau is one
cell of a week, and a day gets one séance out of it per niveau taught in it.
