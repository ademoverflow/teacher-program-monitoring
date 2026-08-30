# 07 - Verify the §8 Phase 2 acceptance criteria

Type: task
Status: resolved
Blocked by: 06

- Counts recomputed by test, not asserted from memory.
- Full-text search exercised in SQL: `websearch_to_tsquery('french', …)` against
  `program_items.search_vector`.
- Spot-check 10 items back against the source PDFs, listed in the report.
- `make check`, `make test`, `docker compose down -v && make up && make seed`.
