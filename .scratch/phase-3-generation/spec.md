# Phase 3 — Génération de la programmation annuelle

MASTER-PROMPT.md §8 Phase 3. Fills `planned_sessions` (and its link table) from the
calendar, the timetable template and the pedagogical content Phase 2 loaded.

No router, no endpoint: Phase 3 fills the database, Phase 4 exposes it.

## What the year affords (recomputed, never assumed)

| | |
|---|---|
| `weeks` | 36 — 7/7/5/6/11 per période |
| `school_days` | 143, of which **139** are taught (4 chômés) |
| worked days per weekday | 33 lundis · 36 mardis · 35 jeudis · 35 vendredis |
| `timetable_slots` | 44 — 10 lundi · 12 mardi · 12 jeudi · 10 vendredi |
| (jour de classe × créneau) | **1532** |
| créneaux **par niveau** (decision 2) | 6 → **+208** séances |
| **séances attendues** | **1740** |

Œuvre-suivie créneaux available: **33** for **36** séances de séquence de littérature.
Maths créneaux per niveau: **139** for 35 séquences × 4 séances = 140.

## Decisions taken before coding

Each of the six is written up as an ADR (0009…0014).

1. **`planned_sessions` natural key** = `(school_day_id, timetable_slot_id, level)`,
   unique, with an Alembic migration. Without it a re-generation duplicates the year.
2. **A commun créneau is split into a CM1 and a CM2 séance exactly when a per-niveau
   méthodo drives it** — the 4 maths créneaux and the grammaire/conjugaison créneaux
   (6 in all). Everything else stays one séance, `level = commun`, and links the items
   de programme of both niveaux. Splitting is a property of the créneau, fixed for the
   whole year, so the week grid keeps its shape even in the weeks with no séquence.
3. **A maths séquence is the content of all four maths créneaux of its week**, séance
   1…4 in chronological order, as §4.3 lays it out ("une suite de 4 séances … sur les
   créneaux « Mathématiques »"). The créneau keeps the domaine the EDT prints — that is
   its position in the grid, not a claim about the séquence. Weeks short of four maths
   créneaux place fewer séances and say so in the report.
4. **RETZ CM2 is classified by the notion RETZ CM1 prints in colour**; the six notions
   CM2 introduces on its own are classified here. 14 grammaire / 7 conjugaison, the same
   shape as CM1. Grammaire runs the lundi créneau, conjugaison the mardi one, each
   séquence spread over its share of the year's créneaux; conjugaison does not start
   before the grammaire séquence on « Le verbe » is finished (§4.4's RETZ advice).
5. **Alternances live in `app_settings`**, seeded with the §4.1 defaults and never
   overwritten by a later `make seed` (insert-if-absent, not upsert).
   `histoire-geographie`: weekly rotation, histoire on odd semaines.
   `arts-plastiques-education-musicale`: arts plastiques lundi, éducation musicale jeudi.
6. **Poésie is not a matière with a créneau of its own**: the vendredi 12h00 créneau
   « Dictée bilan / Poésie » stays one séance in français/orthographe and additionally
   links « Savourer le goût des mots, imaginer et créer en poésie », the poésie entrée
   of Culture littéraire et artistique.

## How a créneau is filled

Four rules, tried in order:

1. **Séquence-driven** — maths (par niveau), RETZ grammaire/conjugaison (par niveau),
   littérature (commun, from `sequence_sessions`). Title and objectives come from the
   séquence; no item de programme is linked (the méthodo does not name one).
2. **Alternance-driven** — the six créneaux with no matière. The setting resolves the
   matière; histoire and géographie then place their thèmes by the périodes the thème's
   intitulé names, arts plastiques and éducation musicale spread their programme.
3. **Rituel** (a créneau of 20 minutes or less: accueil, calcul mental, lecture offerte,
   dictée du jour) — repeats rather than progresses, so it links every item de programme
   of its matière/domaine, every day.
4. **Générique** — the items de programme of the créneau's matière (and domaine when it
   names one) are spread over the year's occurrences of that créneau group, one item at
   a time, in the order the programme prints them.

Un créneau sans matière ni domaine (l'accueil) porte son intitulé et rien d'autre.

## Placement rules that need a report line when they cannot hold

- A séance de séquence de littérature with no œuvre-suivie créneau left (36 > 33).
- A maths week with fewer than four maths créneaux (S1, S25, S28, S30).
- Any créneau of a taught day left without a séance.

The EDT is immutable (§10): none of these is worked around.

## Regeneration

`generate_year(reference_date, periods=None)` is idempotent on the natural key and
**skips a jour de classe that is in the past or that already has a cahier journal**
(§8/§10). Jours chômés get no séance at all.

## Expected counts (asserted by tests that need no database)

- 1740 séances, 0 on a jour chômé, every taught (day, créneau) covered.
- 35 × 2 maths séquences placed, in order, one per semaine, no hole.
- 21 × 2 RETZ séquences placed.
- 8 œuvres, 33 of the 36 séances de séquence placed.
- Alternances: each niveau gets histoire and géographie in alternating semaines.

## Out of scope

Phase 4. No router, no endpoint, no schema Pydantic de réponse.
