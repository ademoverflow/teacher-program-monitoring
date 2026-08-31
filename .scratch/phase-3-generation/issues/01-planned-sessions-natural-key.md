# 01 - Give `planned_sessions` a natural key

Type: task
Status: resolved

`planned_sessions` has no unique constraint beyond its primary key, so a re-generation
has nothing to conflict on and would insert the whole year again — the same trap
Phase 2 hit on `program_items`.

Add `UniqueConstraint("school_day_id", "timetable_slot_id", "level")`, named
`uq_planned_sessions_day_slot_level`. A commun créneau split by niveau (decision 2)
gives two rows that differ only by `level`, which the key already separates; no
`NULLS NOT DISTINCT` is needed because `level` is not nullable.

Generate the migration with `make db-migrate MSG="..."` against the running stack.

**Done when**: `make db-upgrade` applies cleanly and `alembic downgrade -1` reverts it.
