# 06 - Browse and search the programmes

Type: task
Status: resolved
Blocked by: 02

`GET /api/program-items`, filtered by niveau, matière and domaine, and searched with `?q=`.

The search goes through `websearch_to_tsquery('french', …)` against the generated
`search_vector` column and its GIN index — not `ILIKE`. Results with a `q` are ordered by
rank; without one, by `source_order`, which is the order the source prints the blocks in
and the only thing that sorts them (the `id` is a random UUID).

`GET /api/program-items/{id}` gives one item with its source reference (file and page), and
`GET /api/sessions?program_item_id=…` answers §7 écran 4's « voir les séances
liées » — a filtered collection of séances rather than a sub-resource of an item, because
a rituel links the same items all year and the list has to be paged.

**Done when**: `?q=fractions` returns the fractions items and nothing else; filters compose;
an item of maths CM1 lists the séances that link it.
