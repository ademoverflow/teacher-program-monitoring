# An œuvre is one séquence of a single `litterature` méthodo

The eight books of §4.5 are seeded as séquences 1 to 8 of one méthodo named `litterature`,
numbered in the order of the périodes they are read in, and the week-by-week planning of a book
becomes that séquence's `sequence_sessions` — Charlie et la chocolaterie is séquence 1 with seven
séances de séquence.

The alternative was a méthodo per book (`litterature-charlie-et-la-chocolaterie` and so on, each
numbered 1…N over its own weeks). Both fit the `(method, number)` unique key, and they do not
mix, so it had to be settled before extracting. We took the single méthodo because the model
already has a place for "the séances a méthodo lays out", and a book's weekly planning is exactly
that: putting the weeks in `sequence_sessions` keeps a book one thing rather than seven, and lets
the count §8 asks for — the eight œuvres of §4.5 — be read off `sequences` directly. Numbering
across the year rather than within a book is the one part of this that is ours and not the
source's; the source numbers the weeks, which is what `sequence_sessions.number` keeps.
