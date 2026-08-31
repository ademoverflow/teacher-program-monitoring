# 05 - The jour détaillé, and the CRUD of the séances

Type: task
Status: resolved
Blocked by: 02

`GET /api/days/{date}` returns the jour in the order it is taught: its semaine and its
période, whether it is chômé and why, and its séances with everything a séance says —
title, objectifs, contenu, matériel, statut, the créneau it sits in, the séquence and the
séance de séquence behind it, and the items de programme it links.

Then the CRUD §8 asks for: `GET`, `POST`, `PATCH` and `DELETE` on `/api/sessions`. A
`POST` names a jour, a créneau and a niveau — the natural key of ADR-0009 — and must fail
cleanly (409) when that triple is taken rather than blowing up on the constraint.

`duration_minutes` comes from the créneau, and is not `ends_at - starts_at` for the
vendredi calcul mental (ADR-0003).

**Done when**: `/api/days/2026-09-07` returns the 12 séances of that lundi in order; a
`PATCH` on a séance persists; a `POST` on a taken triple answers 409; `/api/days/2027-03-29`
returns a jour chômé with no séance.
