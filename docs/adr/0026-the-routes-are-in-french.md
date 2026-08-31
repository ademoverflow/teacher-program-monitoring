# The routes are in French

`/annee`, `/semaine/12`, `/programmes?q=fractions&niveau=CM1`. The component that renders
each is `YearPage`, `WeekPage`, `ProgramsPage`, and the query keys are `["week", 12]`.

§10 says « UI et contenus en français ; code, identifiants et messages de commit en
anglais », and a URL is genuinely both. We read it as UI: it is the one identifier the
teacher sees, types and bookmarks, and it sits beside a sidebar that says « Année ·
Semaine · Programmes ». `/programmes?matiere=mathematiques` is legible to her;
`/program-items?subject=mathematiques` is legible to us. The code identifiers — components,
hooks, query keys, the zod schema names — stay English, which is where §10's rule bites.

The API keeps its English paths, and that is the same line drawn twice: `/api/*` is code
talking to code, and `Programs.tsx` is the one file where the two vocabularies meet, mapping
`niveau`/`matiere`/`domaine` onto `level`/`subject`/`domain`.

Accents stay out of the paths (`/annee`, not `/année`) so nothing has to be percent-encoded
to be readable.

`/` redirects to `/annee`. §8 Phase 6 makes « Aujourd'hui » the home page; the redirect is
where that lands, and no URL the teacher has kept moves when it does.
