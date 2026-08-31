# 10 - Acceptance

Type: task
Status: ready-for-agent
Blocked by: 03, 04, 05, 06, 07, 08, 09

§8 Phase 4's criteria, checked one by one:

- **OpenAPI complete and coherent** — every endpoint tagged in French, every response
  modelled, `/docs` reachable and free of raw SQLModel rows.
- **Tests green** — one module per router, and no skips in CI now that it has a Postgres.
- **A curl scenario in the report** — navigate a semaine and edit a cahier journal, from an
  empty base, with the actual output.
- `make check` green, `make test` green.
- `docker compose down -v && make up && make seed` still gives the counts of the spec.
- Conventional commits, and a short report (fait / non fait / ambiguïtés).

**Done when**: all of the above hold and the phase report is written.
