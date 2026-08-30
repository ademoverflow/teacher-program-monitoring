# 06 - Load the new seeds

Type: task
Status: resolved
Blocked by: 01, 02, 03, 04, 05

`core/src/core/services/seed_files.py`: `ProgramItemSeed`, `SequenceSeed`,
`SequenceSessionSeed` + `load_program_items()` / `load_sequences()`.
`core/src/core/services/seeding.py`: `seed_program_items()` and `seed_sequences()`,
wired into `seed_database()`, upserting on the natural keys.

**Done when**: `make seed` twice from an empty database leaves an identical snapshot
(fingerprint, not eyeball), and `test_seeding.py`'s expected counts include the three
new tables.
