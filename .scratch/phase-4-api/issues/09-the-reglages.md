# 09 - Expose the réglages, and say what changing one costs

Type: task
Status: resolved
Blocked by: 01

`GET /api/settings` lists the rows of `app_settings` — today the two alternances — and
`PUT /api/settings/{key}` changes one.

A value is not free-form JSON: an `alternance.*` key is validated against the same model
the seed loader uses, so `AlternationMode` stays the single spelling of that vocabulary
(ADR-0013). An unknown key is a 404, not a create — the réglages are the ones the app
defines.

The rotation is read **at generation time**: changing a réglage moves nothing until the
generation is re-run. The response says so as data (`requires_generation`), and §7 écran 5
writes the sentence.

**Done when**: the two alternances come back with their labels and their values; a valid
change persists; an invalid `mode` is a 422; an unknown key is a 404.
