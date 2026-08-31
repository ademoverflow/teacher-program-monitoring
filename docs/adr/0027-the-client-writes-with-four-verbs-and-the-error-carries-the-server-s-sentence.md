# The client writes with four verbs, and a failure carries the server's own sentence

`webapp/src/lib/api/client.ts` gains `apiPost`, `apiPatch`, `apiPut` and `apiDelete` beside
`apiGet`, all five over one `request()`. `ApiError` gains `detail`, read from the response
body, and takes it as its `message` where there is one. ADR-0023 left this open on purpose:
« la forme que veulent les verbes d'écriture … est une connaissance qu'a la Phase 6 ».

The choice was between generic verbs and a mutation named per action in
`lib/api/journal.ts`. It is both, and the split is the same one ADR-0023 already drew:
`client.ts` knows HTTP and knows nothing about the cahier journal; `journal.ts` declares
`initialiseJournal`, `addEntry`, `updateEntry`, `deleteEntry` and `reorderJournal`, each
with the zod schema of what comes back. A screen never names a verb or a path.

**The error body is the part that had to be decided.** `ApiError` carried only a status,
and a status is not something the teacher can act on. This API answers in French and says
what is wrong: « L'ordre doit nommer exactement les lignes du cahier journal de ce jour,
une fois chacune » for a partial `PUT /order`, « Cette séance n'existe pas » for a stale
id. So the client reads `detail` out of the body and the vue Jour shows it verbatim. Two
cases are left alone: a 422 from Pydantic answers with a *list* of field errors rather than
a string, and a body that is not JSON has nothing to read — both keep the client's own
`GET /api/x → HTTP 500`, which is a developer's message and is at least true.

**Nothing is optimistic.** Every mutation returns the row it wrote, and that row goes into
the query cache. An optimistic update would have to guess what the server does to what it
is sent — `position` is computed server-side when a ligne is added, a `PUT /order` renumbers
every ligne — and would then have to be rolled back on the 400 that is exactly the case
worth getting right. The write is fast and local; there is nothing to hide.
