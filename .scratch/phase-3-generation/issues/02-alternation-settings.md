# 02 - Seed the alternances into `app_settings`

Type: task
Status: ready-for-agent

Six créneaux carry an `alternation_group` and no matière (ADR-0002). Which matière a
week's créneau actually teaches is a **setting** (§4.1: « à paramétrer, modifiable dans
l'app »), and `app_settings` is empty.

Add `core/seed/settings.json` with the §4.1 defaults and load it from
`core.services.seeding`:

- `alternance.histoire-geographie` — weekly rotation, histoire on odd semaines.
- `alternance.arts-plastiques-education-musicale` — arts plastiques on the lundi
  créneau, éducation musicale on the jeudi one (§4.1 asks for one of each per week and
  does not say which goes where; this is ours).

**These rows are inserted only when absent, never upserted**: a re-seed must not
overwrite a choice the teacher has changed. `make seed` stays idempotent.

**Done when**: `make seed` twice leaves the same two rows; changing a value by hand and
re-seeding leaves the changed value in place.
