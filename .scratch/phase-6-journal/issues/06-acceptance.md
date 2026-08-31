# 06 - Acceptance

Type: task
Status: ready-for-agent
Blocked by: 03, 04, 05

§8 Phase 6, criterion by criterion, against a database rebuilt from empty
(`docker compose down -v && make up && make seed`):

1. **Cycle complet sur un jour de démo** — ouvrir `/jour/2026-09-07` → initialiser →
   éditer une discipline et une durée → écrire un bilan → imprimer.
2. **Les modifications persistent en DB** — read the rows back with `psql`, not just the
   UI.
3. **Le cahier journal reste intact après une régénération** — initialise, edit, run
   `make generate`, read the cahier journal back and check the edit is still there. Check
   what the report says it skipped.
4. `make check` green (ruff · mypy · biome · tsc), `make test` green, `make seed`
   idempotent from empty.

Then `mattpocock-skills:code-review` before the final commit (§9), and the report:
fait / non fait / ambiguïtés.
