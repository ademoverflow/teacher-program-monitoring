# The alternances are a réglage, and a re-seed never overwrites one

The six créneaux that carry an `alternation_group` and no matière (ADR-0002) are
resolved from two rows of `app_settings`, seeded from `core/seed/settings.json` with the
§4.1 defaults: `histoire-geographie` rotates week by week starting on histoire, and
`arts-plastiques-education-musicale` fixes arts plastiques on the lundi créneau and
éducation musicale on the jeudi one.

Both defaults are partly ours. §4.1 gives « rotation histoire/géographie, par défaut
alternance hebdomadaire » without saying which matière opens the year, and « un créneau
arts plastiques + un créneau éducation musicale par semaine » without saying which goes
on which day.

These two rows are inserted only where the key is free — `ON CONFLICT DO NOTHING`, not
the upsert every other seed uses. §4.1 calls the alternances « à paramétrer, modifiable
dans l'app », and a `make seed` that undid a choice the teacher had made would make that
false. The cost is that a *correction* to the shipped default no longer reaches a
database that has already been seeded; that is the right way round, because the row
belongs to the teacher once it exists. `make seed` stays idempotent either way.

The rotation is read at generation time, so changing the réglage and re-running the
generation moves the whole year's histoire and géographie — which is what a paramètre is
for.
