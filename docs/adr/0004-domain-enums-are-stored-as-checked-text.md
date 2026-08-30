# Domain enums are stored as checked text, not as Postgres enum types

Columns holding a domain enumeration — `level` (`CM1`/`CM2`/`commun`), a séance's `status`,
a révision IA's `status` — are `varchar` columns with a named `CHECK` constraint listing the
allowed values, generated from the Python `StrEnum` so the two cannot drift. The obvious path
with SQLModel is a native Postgres `ENUM` type, and this is a deliberate departure from it.

Native enum types make Alembic awkward in exactly the ways this project will hit: autogenerate
does not reliably create or drop the type alongside the table, and adding a value later needs a
hand-written `ALTER TYPE` that cannot run inside a transaction on older servers. A `CHECK`
constraint gives the same integrity, the same Python-side typing (the field is still typed as
the `StrEnum`), readable values in Adminer, and a one-line migration when a value is added.

The trade-off is that Postgres will not enumerate the allowed values for you through
`pg_type` — the constraint definition is where they are written down.
