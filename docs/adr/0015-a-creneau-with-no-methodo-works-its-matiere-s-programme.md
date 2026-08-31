# A créneau with no méthodo works its matière's programme — spread if it teaches, whole if it is a rituel

Most of the timetable has no méthodo behind it: sciences, anglais, EMC, EPS, the
orthographe and vocabulaire créneaux, the reading and writing ones. §8 Phase 3 asks for
« séances génériques liées aux items de programme correspondants », and there are two
ways to read that.

Linking *every* item of the matière to *every* séance is one, and it says nothing: the
teacher opening a séance de sciences would get the whole programme de sciences, 22 items,
in June as in September. So the year's créneaux of one (matière, domaine, niveau) are
instead cut into as many consecutive shares as the programme has items, in the order the
programme prints them, and each séance links the one item its share has reached. That is
what turns a list of items into a programmation: sciences walks its twelve CM1 items
across its 68 créneaux, about six créneaux each. The séance takes that item's intitulé as
its title where the niveaux agree on one, and the créneau's own intitulé where they do
not.

The cut is even and deterministic (`spreading.shares`), and it is ours — the source gives
an order, never a pace. The order is not ours: `program_items.source_order` records the
rank of each block in the source document, because a primary key defaulted by
`gen_random_uuid()` cannot, and without it the progression would have followed random
UUIDs and changed on every rebuild.

A **rituel** is the exception, and is defined as a créneau of twenty minutes or less —
which picks out exactly the short daily cells of §4.1: l'accueil, le calcul mental, la
lecture offerte, la dictée du jour. A rituel repeats rather than progresses, so it keeps
its whole programme on every occurrence: the dictée du jour works the three orthographe
items all year, because that is what a daily dictée does. L'accueil has neither matière
nor domaine and links nothing; it carries its intitulé and that is all the source says
about it.
