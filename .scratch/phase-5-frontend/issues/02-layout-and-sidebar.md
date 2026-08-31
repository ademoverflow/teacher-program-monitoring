# 02 - The persistent layout and its sidebar

Type: task
Status: resolved
Blocked by: 01

§7 asks for a sidebar that never leaves: Année · Semaine · Programmes for Phase 5, with
« Aujourd'hui » and « Réglages » arriving with the screens that fill them (Phase 6). The
root route renders it around an `<Outlet/>`.

The sidebar footer keeps the Phase 0 smoke test alive as an « État de l'API » line: for a
teacher whose containers did not start, « API injoignable » is the one diagnostic worth
having on every page.

`/` redirects to `/annee`. Phase 6 repoints it at « Aujourd'hui » — one line, and no URL
the teacher bookmarked moves.

**Done when**: every route renders inside the layout, the active nav item is marked, and
the API status line reports both states.
