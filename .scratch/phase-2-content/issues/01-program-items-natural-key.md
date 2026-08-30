# 01 - Give `program_items` a natural key

Type: task
Status: resolved

`program_items` has no unique constraint beyond its primary key, so an upsert has
nothing to conflict on and `make seed` would insert the whole curriculum again on
every run.

Add `UniqueConstraint("level", "subject_id", "domain_id", "title")`, named
`uq_program_items_level_subject_domain_title`, with `postgresql_nulls_not_distinct=True`
so a null `domain_id` still collides with itself. Generate the migration with
`make db-migrate MSG="..."` against the running stack.

**Done when**: `make db-upgrade` applies cleanly and `alembic downgrade` reverts it.
