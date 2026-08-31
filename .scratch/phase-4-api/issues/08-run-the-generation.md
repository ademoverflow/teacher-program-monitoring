# 08 - Launch the generation, and ask before overwriting

Type: task
Status: ready-for-agent
Blocked by: 01

`generate_year(session, reference_date=…, periods=…)` already exists, takes 0.5 s and writes
1740 rows. That fits in a request: `POST /api/generation` runs it and returns the rapport
de validation as JSON — every ligne with its nature (`calendrier`, `source`, `erreur`), the
counts, and `is_clean`.

§7 écran 5 asks for « une confirmation explicite avant d'écraser une période déjà entamée ».
A période is under way when one of its jours de classe is past or already has a cahier
journal — the very days `_untouchable_days` protects. `POST` without `confirm` refuses those
périodes with a 409 naming them; `GET /api/generation` reports the same thing up front, so
the UI can ask before it posts.

**Done when**: a `POST` on a future année returns a clean report and writes 1740 séances; a
`POST` on a période already under way answers 409 without `confirm` and runs with it; and a
run never touches a day the cahier journal has claimed.
