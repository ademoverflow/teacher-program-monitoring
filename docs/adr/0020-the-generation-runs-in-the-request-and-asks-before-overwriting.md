# The generation runs inside the request, and asks before overwriting a période under way

`POST /api/generation` calls `generate_year` and returns the rapport de validation in the
same response. The whole year is 1740 séances and half a second, so a background task would
buy nothing and cost a job id, a polling endpoint and a state machine for a progress bar
that would flash once.

§7 écran 5 asks for « une confirmation explicite avant d'écraser une période déjà entamée ».
That is a parameter of the request, not a reason to defer it: the body carries
`confirm`, and without it a run targeting a période already under way is refused with 409
naming the périodes concerned. `GET /api/generation` reports the same thing up front —
which périodes are under way, how many jours each has that a run would not touch, how many
séances each holds — so the UI can put the question before the request rather than after a
refusal.

A période is « entamée » when it holds jours de classe that a re-generation would leave
exactly as they are: those in the past, and those a cahier journal already holds. That is
the set `_untouchable_days` protects in `planning/writer.py`, read from the other side. Note
what the confirmation is *not* about: those days are safe with or without it. It is about
the rest of the période, which a re-generation does rewrite — the future days of a période
the teacher has already started teaching and may already have looked ahead in.

The alternative was to key the confirmation off « the période contains today ». It is
simpler and it is wrong twice: it would ask about a période that has not been touched yet,
and it would stay silent about a past période being regenerated wholesale.
