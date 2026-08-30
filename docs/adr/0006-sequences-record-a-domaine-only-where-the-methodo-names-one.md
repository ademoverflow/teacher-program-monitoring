# A séquence records its domaine only where the méthodo names one

`sequences` carries a nullable `domain_id`. It is set for the 21 RETZ CM1 séquences, where the
progression prints a colour legend that separates « Séquences de grammaire » from « Séquences de
conjugaison », and left null everywhere else — for the CM2 progression, which is given as a
sommaire with no legend, and for the maths séquences, whose méthodo lists titles and périodes
and nothing more.

Without the column, the printed classification would be lost at extraction time and Phase 3 would
have to invent it, because the timetable teaches grammaire on Monday and conjugaison on Tuesday
in separate créneaux and has to know which séquence goes where. Deriving it from the titles
instead was the alternative, and it is exactly the invention §10 forbids: it happens to read well
for CM2 (a tense name is conjugaison) and it would be ours, not the source's.

The consequence is a column that is populated for a third of the rows, which looks like an
oversight and is not. A reader of `sequences` cannot assume `domain_id` is set; a null there
means the méthodo did not say, and Phase 3 has to decide and record that decision as its own.
