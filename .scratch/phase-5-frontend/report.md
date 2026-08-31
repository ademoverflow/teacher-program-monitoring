# Phase 5 — rapport

Frontend : navigation & programmes. §7 écrans 1 (Année), 2 (Semaine) and 4 (Programmes),
plus the persistent layout. `core/` did not change; no migration; the API was consumed, not
touched.

## Fait

| | |
|---|---|
| Routes | `/` → `/annee` · `/annee` · `/semaine` → semaine courante · `/semaine/$number` · `/programmes` · `/programmes/$id` |
| Client API | `webapp/src/lib/api/` — `client.ts` (`apiGet`) plus one module per resource, hand-written zod |
| Tests | **53** vitest (was 2), **208** pytest — 261 green, no skips |
| ADR | 0023 (client) · 0024 (grid axis + breaks) · 0025 (colour cascade) · 0026 (French routes + why the route tree left `main.tsx`) |
| Glossaire | `CONTEXT.md` gains **bande**, **récréation**, **pause méridienne** |

Every acceptance criterion of §8 Phase 5, recomputed against a database rebuilt from empty
(`docker compose down -v && make up && make seed`, then `make seed` again — identical):

- **année → période → semaine** — the year view draws the 5 périodes with 7/7/5/6/11
  semaines and the 5 vacances from one `GET /api/calendar`; every semaine chip links to its
  grid; no dead link anywhere.
- **semaine courante par défaut** — `/semaine` resolves `current_week_number`, falling back
  to the semaine of `next_taught_day`.
- **recherche « fractions »** — `?q=fractions&niveau=CM1` returns the 3 expected items, in
  the server's rank order, nothing re-sorted or re-filtered client-side.
- **grille fidèle au §4.1** — lun/mar/jeu/ven columns from the response, hour bands, CM1/CM2
  badges, matière colours from `subjects.color`.
- `make check` green (ruff · mypy · biome · **tsc**), `make test` green, `vite build` green.

### The grid, which is where the phase's thinking went

The bands are **derived** from the créneaux' own boundaries rather than written down
(ADR-0024): 13 of them, and a cellule spans the ones its créneau covers. That is what makes
vendredi work. Its two 30' cells sit on 11h30-12h00 and 12h00-12h30 rather than on the
11h30-12h15 / 12h15-12h30 the other jours use (ADR-0003), so a grid of one row per printed
range would have four rows with holes that are not real. Derived bands have **no holes at
all** — a test asserts it, summing lane spans band by band — except two, which no créneau of
any jour covers: those are la récréation and la pause méridienne, which have no row in
`timetable_slots`. Only their names are written down.

The three traps are covered against responses frozen from a seeded stack: S1 draws three
columns and 38 séances; S25's lundi keeps its ten cellules, empty, under « Lundi de
Pâques »; mardi 09h10 is **one** box with two stacked séances while mardi 11h30 is **two**
boxes side by side.

## Non fait — délibérément

- **Pas de route `/jour`.** §7 écran 2 asks for « clic sur un jour → vue Jour » and écran 3
  is Phase 6. A link to a page whose content belongs to the next phase is worse than no
  link, so the jour headers are not links. Phase 6 adds the route and makes them one.
- **« Aujourd'hui » et « Réglages » ne sont pas dans la sidebar.** §7 lists five entries;
  three are built. The other two ship with the screens that fill them (Phase 6/8) rather
  than as links to nothing. `/` redirects to `/annee` so that Phase 6 can repoint it at
  « Aujourd'hui » without moving a URL the teacher has kept.
- **Aucun verbe d'écriture dans le client** — no `apiPost`/`apiPatch`/`apiDelete`. §8 asks
  each phase not to anticipate the next, and the shape the write path wants is knowledge
  Phase 6 has (ADR-0023). Nothing in `webapp/src` mentions `/api/journal`,
  `POST /api/generation` or `/api/settings`.

## Ce qui a changé hors `webapp/src`

Three things, each because something was already wrong:

- `vite.config.ts` imported `defineConfig` from `vite`, which does not accept a `test`
  block — `tsc` failed on the config file, so **the frontend had never been typechecked**.
  It now imports from `vitest/config`.
- `make check-webapp` ran Biome only. It now runs `tsc --noEmit` as well
  (`make type-check-webapp`), so `make check` is a real gate on a TypeScript codebase.
- `webapp/src/test/setup.ts` registers Testing Library's cleanup. Vitest runs without global
  hooks here, so it had never registered itself; without it one test's DOM is still mounted
  while the next queries.

`.claude/skills/new-route/SKILL.md` was updated: it told the next agent to edit `main.tsx`
and to copy a `pages/About.tsx` that does not exist.

## Une correction au handoff

The handoff says `current_week_number` is « null hors année scolaire — et « aujourd'hui »
est le 31/08/2026 pour l'instant, donc **null en pratique** ». It is **1**: `weeks.starts_on`
is the Monday 31/08 while P1 opens on the mardi 01/09, so today already falls inside semaine
1. The `next_taught_day` fallback is kept — the field is genuinely null from 03/07/2027 — but
« semaine courante par défaut » works today without it.

## Ambiguïtés et points ouverts

1. **Une URL est-elle de l'UI ?** §10 says French UI, English identifiers. We read the
   address bar as UI (ADR-0026): `/programmes?matiere=mathematiques` is legible to the
   teacher, `/api/program-items?subject=…` is not. Components and query keys stay English.
   Reversible in an afternoon if the answer is meant to be the other one.
2. **La `poesie` reste dans le filtre matière.** It has zero items de programme by design
   (ADR-0014), so choosing it returns nothing. We show it: it is a matière the teacher has,
   and an empty result is a true answer, said in words. Hiding it would be a second rule
   about a matière that already has one.
3. **`GridBand` fixe la hauteur des bandes, pas au prorata.** The pause méridienne is 90
   minutes and would swallow the afternoon. Short bands get a floor, long ones a ceiling,
   and content can push a band open. That is §4.1's own choice — the printed EDT is not
   time-proportional either.
4. **Les dates et les heures sont des `string`.** `formatTime(day.date)` typechecks and
   would be wrong. Branded types would fix it; nothing needed them yet.
5. **Une matière alternante sans séance n'a pas de couleur.** An unplanned « Histoire ou
   Géographie » cellule falls through both rungs of the cascade to neutral, because the
   créneau names a pair and no séance resolved it. It does not happen in the generated year;
   if the teacher ever deletes such a séance in Phase 6, the box goes grey.
6. **Le lien depuis une séance liée ne mène nulle part.** On a fiche d'item, the séances
   show their date but do not link: `PlannedSessionSummary` carries the date and not the
   semaine, and there is no jour route to send it to. Phase 6 gets both.

## Revue de fin de phase

`mattpocock-skills:code-review` ran on both axes. Two findings were real bugs, and both were
invisible to the tests as written — recorded in `6effd2f`:

- **an empty cellule dropped rung 2 of ADR-0025.** `CellBox` returned before computing a
  colour, so the maths cellule of a jour chômé drew grey where the ADR says it stays pink.
  The pure function was right and tested; the component ignored it. Now fixed, muted, and a
  test reads the colour back off the DOM.
- **the domaine filter offered « Compétences travaillées » twice**, once for arts plastiques
  and once for éducation musicale, under one code — two options with the same value, which a
  `<select>` cannot tell apart. Now one option per code.

Also from the review: a séance in a stacked cellule now cascades to its créneau rather than
to the first séance's matière; an unparseable filter in the URL is dropped instead of
replacing the page with an error; `/semaine/douze` says so rather than asking the API about a
`NaN`; a 4xx is no longer retried three times (which is what `ApiError.status` was for); and
the conventions the review cited — one component per file, `@/` imports in `lib/api`, a bande
index not called a « row » — were followed.
