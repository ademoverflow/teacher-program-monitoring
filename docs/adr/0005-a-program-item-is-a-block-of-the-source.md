# An item de programme is a block of the source, keyed by niveau, matière, domaine and intitulé

`program_items` holds one row per block the curriculum prints — a heading and the objectives
listed under it — not one row per learning objective. « Lire avec fluidité » at CM1 is one item
whose description is its four objectives, rather than four items. Its identity is
`(level, subject_id, domain_id, title)`, enforced by a unique constraint declared
`NULLS NOT DISTINCT` so an item with no domaine still collides with itself.

The obvious alternative — one item per objective line — was rejected because the source does not
give an objective a title of its own: an objective is a sentence inside a block, and splitting
the block would leave every row with an empty `title` and a `description` equal to it, which the
generated `search_vector` indexes twice for nothing. Keeping the block also keeps the item at the
granularity a séance is planned at: a créneau of 45 minutes works on a block, not on one line of
one.

The key was the second choice. `(level, subject_id, title)` reads like enough — it is what a
first pass would write — and it is not: the langues-vivantes programme prints *Raconter* under
both « Expression orale en continu » and « Expression écrite » for the same niveau, so the
domaine is part of the identity. `(source_file, source_page, title)` would have worked too, at
the price of tying a curriculum item's identity to the pagination of a PDF that will be reprinted
for the next rentrée. The `NULLS NOT DISTINCT` clause is the cost of `domain_id` staying
nullable — histoire and géographie are cut into thèmes, not domaines — and it needs Postgres 15
or later, which is met (Postgres 17).
