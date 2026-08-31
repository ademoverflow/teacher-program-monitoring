# A cahier journal is initialised once, from the day's séances, and never over itself

`core/services/journal.py` fills a day's `journal_entries` from its `planned_sessions`, in
the order of the day, and only where the day has none. `POST /api/journal/{date}/initialise`
can be called every time the vue jour opens: it answers **201** the once it fills the day
and **200** every time after, so a caller can tell a fill from a no-op without a flag on a
schema that `GET` shares. That is §10's rule — « les cahiers journaux … ne sont jamais écrasés » —
stated on the write side, where the generator already states it on its own
(`_untouchable_days`).

What a ligne copies is settled by `docs/exemple-cahier-journal-quotidien.pdf`, which prints
three columns:

- **Discipline** takes the créneau's own label, which is the EDT's wording (§4.1) and reads
  like the example's headings — « Grammaire », « Calcul mental », « Anglais ». The six
  alternating créneaux are the exception: their label names a pair (« Histoire ou
  Géographie »), so the matière the séance resolved to is what goes down (ADR-0002). The
  niveau is appended wherever the séance is not commun, because a split créneau puts two
  lignes at the same hour (ADR-0010).
- **Durée** takes the créneau's `duration_minutes`, not `ends_at - starts_at`: the cahier
  journal prints teaching time, and for the vendredi calcul mental the two differ
  (ADR-0003).
- **Objectifs et compétences** takes the séance's title, and its objectifs under it. The
  example puts both in that one cell — « Séquence 1 Les types de phrases … », « Utiliser les
  nombres jusqu'à 200 / Séance 1 » — and a séance whose objectifs repeat its title says it
  once.
- **Bilan** and the notes start empty. A bilan is written after the lesson; that is what the
  word means (`CONTEXT.md`).

Taking the domaine's label as the discipline was the obvious alternative, and it reads well
until it does not: the CM1 sciences créneau would be filed under « La matière, les mouvements
et les signaux » and the anglais one under « Compréhension de l'oral ». The créneau's label
is the teacher's own name for the cell and never has that problem.

A day whose lignes have all been deleted reads as never initialised and can be filled again.
That is the one state this cannot tell apart, and it is the one where filling it is what
would be asked for anyway; the alternative would be a column recording that a day was once
initialised, which is a row of bookkeeping for a case the teacher can undo with one click.
