# 08 - Write the year, skip what must not be touched, report

Type: task
Status: ready-for-agent
Blocked by: 01, 05, 06, 07

- Bulk-upsert the drafts on the natural key of issue 01; replace the link rows of the
  séances written. More than 1700 séances, so one statement per table, not one per
  séance (§8: under a minute).
- **Never touch** a jour de classe in the past or one that already has a cahier journal
  (§10). Jours chômés get no séance.
- `generate_year(reference_date, periods=None)` — a re-generation of one période only
  touches that période.
- Return a report: séances written, séquences covered, alternances counted, and every
  impossibility (issue 05's unplaced littérature weeks, short maths weeks, uncovered
  créneaux).
- Entry point `core.generate` (`make generate`), and `make seed` runs the generation
  after the seeds so a fresh database is usable.

**Done when**: generation from an empty database is under a minute, running it twice
changes nothing, and the report is clean apart from the impossibilities the calendar
imposes.
