# 09 - Acceptance: sample the year by hand, write the ADRs

Type: task
Status: ready-for-agent
Blocked by: 08

§8 Phase 3 acceptance:

- generation under a minute, validation report without an error;
- manual sample — **P1-S1 complete** and one week of **P3** — read against §4.1 and the
  méthodos;
- `make check`, `make test`, `make seed` still idempotent from an empty database
  (`docker compose down -v && make up && make seed`).

Plus: one ADR per decision of `spec.md` (0009…0014), `CONTEXT.md` updated with the
vocabulary the generation brought out (rituel, alternance résolue, marge), and the
end-of-phase report (fait / non fait / ambiguïtés).
