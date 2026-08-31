# 03 - A planner that reads plain data, not a database

Type: task
Status: resolved

CI has no Postgres, and the placement rules are where the bugs will be. Split the
generator in two:

- `core/services/planning/` — pure functions over frozen dataclasses (the year's
  jours de classe, the 44 créneaux, the séquences, the items de programme, the
  alternance settings) returning séance drafts and a report. No session, no I/O.
- the database side — read those inputs from the tables, call the planner, bulk-upsert
  the drafts.

Every count and every placement rule is then testable from seed files alone.

**Done when**: the planner module imports nothing from `core.database`, and its tests
build their inputs in memory.
