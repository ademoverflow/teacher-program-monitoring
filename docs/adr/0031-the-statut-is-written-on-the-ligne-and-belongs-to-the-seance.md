# The statut is written on the ligne, and belongs to the séance

§8 Phase 6 asks for « statuts des séances » in the vue Jour. A statut lives on
`planned_sessions`, a ligne de cahier journal is a different row, and `planned_session_id`
is nullable — the teacher adds lignes for things no créneau planned. So the two cannot
simply be merged, and `CONTEXT.md` is explicit that they are two things: a **discipline** is
free text, a **matière** is a row of `subjects`; a **séance** is planned, a **ligne** is what
happened.

The vue Jour is the cahier journal. A ligne that came from a séance carries that séance's
statut as a select in its controls column, and it writes to
`PATCH /api/planned-sessions/{id}`, not to the ligne. A ligne the teacher wrote herself
carries none — and that absence is the clearest statement of the distinction the screen can
make. « Programmation du jour », below, names the statut and does not set it: one place
writes, so there is never a doubt about which control won.

Two columns side by side — the programmation left, the cahier journal right — was the
alternative the phase started from. It cannot line up: at initialisation the two lists match
one for one, and from the teacher's first edit they do not. She deletes a ligne (the séance
stays), she adds one (there is no séance), she reorders (the séances keep the clock's
order). Two columns would then be two lists that look like they should align and do not,
which is a worse statement of the same fact than one column plus a nullable link.

« Programmation du jour » stays, read-only, for what a ligne does not copy: the séquence
and its étape, les items de programme (as links to their fiche), le matériel, les horaires.
What it deliberately does *not* repeat is the séance's `objectives` — a ligne already
carries those (ADR-0021), and on a rituel they are the items de programme spelled out a
second time (ADR-0015).
