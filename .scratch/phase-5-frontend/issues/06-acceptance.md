# 06 - Acceptance

Type: task
Status: resolved
Blocked by: 03, 04, 05

§8 Phase 5's criteria, each recomputed:

- année → période → semaine navigates with no dead end;
- `/semaine` opens the semaine courante;
- « fractions » returns the items expected;
- the grid is faithful to §4.1: lun/mar/jeu/ven columns, hour bands, CM1/CM2 splits,
  matière colours.

Plus the rules common to every phase: `make check` green, `make test` green, `make seed`
still idempotent from an empty database (`docker compose down -v && make up && make seed`),
conventional commits, and a short report.

**Done when**: all of the above, and `mattpocock-skills:code-review` has been run and
answered.
