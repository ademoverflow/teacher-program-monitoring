# 03 - Vue Année: the five périodes and their semaines

Type: task
Status: resolved
Blocked by: 02

§7 écran 1, from the single `GET /api/calendar`. Five cards, one per période, each listing
its semaines as clickable chips (`S1`, `P1-S1`, dates), the vacances that follow it, and a
mark on the semaine courante.

`days_off` is on every `WeekSummary`: a semaine that loses a jour says so, so the teacher
sees P4-S6 is short before she opens it.

`current_week_number` is 1 today and null after 02/07/2027. The « current » mark uses it
where it is set and nothing where it is not — the redirect in ticket 04 is what needs a
fallback, not this view.

**Done when**: 36 semaines in 7/7/5/6/11 across 5 cards, 5 vacances shown, every semaine
chip navigates to `/semaine/$number`.
