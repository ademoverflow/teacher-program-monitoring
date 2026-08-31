# 05 - Navigateur de programmes: filters, recherche, fiche

Type: task
Status: resolved
Blocked by: 02

§7 écran 4. `GET /api/program-items?level=&subject=&domain=&q=&limit=&offset=`, with the
filter state in the URL search params so a filtered list is a link the teacher can keep.

The recherche is already `websearch_to_tsquery('french', …)` server-side: the input is
debounced and sent, and **nothing is filtered client-side on top of it**. Without `q` the
items arrive in the source's order; with one, by rank — the list never re-sorts them.

The matière and domaine options come from `GET /api/subjects`; picking a matière narrows
the domaine list to its own. `poesie` has zero items and stays in the list: it is a
matière the teacher has, and a filter that returns nothing is a true answer (ADR-0014).

`/programmes/$id` shows the item, its description, `source_file`/`source_page`, the
`needs_review` mark where the extraction was unsure (ADR-0022), and « voir les séances
liées » from `GET /api/planned-sessions?program_item_id=`.

**Done when**: `?q=fractions&niveau=CM1` shows the 3 expected items, the filters compose,
paging works over 220 items, and a fiche names its source page.
