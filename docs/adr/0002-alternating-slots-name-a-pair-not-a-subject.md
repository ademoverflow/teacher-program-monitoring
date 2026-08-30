# Alternating créneaux name a pair, not a matière

Six créneaux of the timetable do not have a fixed matière: the four "Histoire ou Géographie"
slots (two per niveau per week) and the two "Arts plastiques / Éducation musicale" slots. These
rows carry an `alternation_group` naming the pair they rotate within and leave `subject_id`
null; which matière actually falls on a given week is decided when the year's séances are
generated (Phase 3), and the chosen rotation is a setting the teacher can change.

The alternative was to bake the rotation into the timetable seed — two template weeks, A and B,
each with its matière resolved. We rejected it because the timetable (§4.1) is immutable while
the rotation is explicitly "à paramétrer, modifiable dans l'app": baking the rotation in would
have made a mutable choice part of the immutable structure, and doubled the template for a
choice that belongs to the generator. The cost is that `subject_id` is nullable on
`timetable_slots` and readers of a single row cannot tell what is taught in it without resolving
the alternance.
