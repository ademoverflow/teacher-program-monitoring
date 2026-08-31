# 05 - « Aujourd'hui » as the home page, and the three dead ends

Type: task
Status: ready-for-agent
Blocked by: 02

§8: « "Aujourd'hui" comme page d'accueil (redirige vers le prochain jour de classe si
férié/week-end) ».

- `/` redirects to `/aujourdhui` (was `/annee`; ADR-0026 said this line would move).
- `/aujourdhui` resolves `GET /api/calendar/today` and replaces itself with
  `/jour/{next_taught_day}` — which is today when today is taught. On 2026-08-31 that is
  mardi 01/09, so the fallback is the only path the year currently exercises. A year that
  is over has no `next_taught_day`: say so rather than redirect to nothing.
- The sidebar gains « Aujourd'hui ». « Réglages » still links nowhere and still is not
  there (écran 5, decision 7).

Three dead ends of Phase 5 become links now that there is somewhere to go:

- the semaine grid's jour headers — §7 écran 2's « clic sur un jour → vue Jour » ;
- the séances liées on the fiche of an item de programme.

**Done when**: `/` lands on mardi 1 septembre 2026 ; a jour header of the semaine grid is
a link to its jour ; a séance liée is a link to its jour.
