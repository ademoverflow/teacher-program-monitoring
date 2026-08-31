# 02 - Declare the shapes the API renders

Type: task
Status: ready-for-agent
Blocked by: 01

The SQLModel rows carry `search_vector`, `created_at`, `updated_at` and `needs_review`;
none of that is the front's business, and a `tsvector` does not serialise. §6 asks for
dedicated Pydantic response models (the `health.py` pattern).

Create `core/src/core/schemas.py` for the shapes more than one router renders — a matière,
a domaine, a créneau, a séquence, an item de programme, and the summary of a séance — and
`core/src/core/services/schedule.py` for the queries that build them.

A rendered séance must let Phase 5 draw §4.1 without a second request: its niveau, its
title, its statut, its matière (with the colour) and its domaine, and the séquence behind
it where there is one.

**Done when**: `core/services/schedule.py` returns those shapes for one semaine and one
jour, and nothing in the module imports a router.
