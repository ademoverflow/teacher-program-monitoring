# A cellule takes its colour from the séance, then from the créneau, then from nothing

`cellSubject` is `cell.sessions[0]?.subject ?? cell.slot.subject ?? null`, and
`subjectStyle(null)` is the neutral slate. One cascade, written once, covers the three cases
the year actually contains.

**The séance first**, because the six alternating créneaux carry no matière of their own —
they name a pair, and which one falls on a given semaine is the génération's answer, carried
on the séance (ADR-0002). Reading the créneau first would leave « Histoire ou Géographie »
grey all year, which is the one place on the grid where the colour is telling the teacher
something she cannot read off the label.

**The créneau second**, so an empty cellule still shows what is normally taught in it. That
is what a jour chômé looks like: ten cellules of a lundi, no séance in any of them, and the
maths cellule still pink under « Lundi de Pâques ».

**Neither, sometimes.** L'accueil du matin has no matière at either end — the créneau has
none and neither has the séance, because the source says nothing more about it than its
intitulé (ADR-0015). 139 séances are in that case. So the cascade ends in a real neutral
rather than in a default matière, and a cellule with no colour is a true statement.

The colour itself is `subjects.color`, a pastel from the seed, used straight as the
background with an accent derived by CSS `color-mix` rather than by arithmetic in
JavaScript: a colour changed in `core/seed/subjects.json` changes the whole app.

Where a cellule holds two séances, each is tinted by its own matière. In this year they
always agree — a split créneau is one créneau taught at two niveaux — but the rule costs
nothing and does not have to assume it.
