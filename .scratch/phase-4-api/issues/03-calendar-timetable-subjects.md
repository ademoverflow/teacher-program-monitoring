# 03 - The calendrier, the gabarit and the matières

Type: task
Status: resolved
Blocked by: 02

Three read-only routers, all reference data.

- `GET /api/calendar` — the année scolaire, its five périodes each with their semaines,
  the vacances, and the number of the semaine courante. This is §7 écran 1 in one request.
  A semaine reports how many of its jours are chômés, so the year view can show the hole in
  P4-S6 without opening it.
- `GET /api/calendar/today` — today's jour de classe if there is one, and the next one
  otherwise. « Aujourd'hui » is the home page (§7).
- `GET /api/timetable` — the 44 créneaux, so the grid can be drawn for a semaine that has
  no séance at all.
- `GET /api/subjects` — the 12 matières with their colour and their 45 domaines.

**Done when**: the four endpoints return the counts recomputed in the spec, and
`/api/calendar` gives 7/7/5/6/11 semaines.
