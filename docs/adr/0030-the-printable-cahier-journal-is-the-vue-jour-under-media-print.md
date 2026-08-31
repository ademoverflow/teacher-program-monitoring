# The printable cahier journal is the vue Jour under `@media print`

There is no `/jour/$date/impression`. Ctrl+P on the vue Jour prints
`docs/exemple-cahier-journal-quotidien.pdf`: « Période 1 – Semaine 2 », the date in full
with « CM1-CM2 – Cycle 3 » opposite it, and the three-column table with la récréation and la
pause méridienne across it.

A separate route was the alternative and it duplicates the page for nothing. The screen
version and the printed version show the *same three columns of the same lignes*; the only
difference is what is taken away — the sidebar, the jour navigation, the controls column,
« Programmation du jour ». `print:hidden` says that in one word per element, at the element,
where a second route would restate the whole assembly and then drift from it. It also keeps
one URL: the teacher prints the day she is looking at rather than finding a link to a
printable copy of it.

**The fields print as text because they auto-grow.** A `<textarea>` prints what fits its
box, so a bilan of four lines in a two-line box would print two. `.autogrow` puts the field
and a hidden copy of its own text in one grid cell, so the cell is always as tall as the
text — no measurement in JavaScript, and what is on screen is what comes out. In print the
fields lose their background and their chrome: a printed cahier journal must not look like a
form.

Two details are the model's and not CSS's defaults. The controls column is hidden, so a
break row spans **three** columns rather than four — a `colSpan` of four prints a rule
sticking out past the table. And the column widths are shares, not pixels, so the share the
controls column gives up in print goes to « Objectif(s) et compétence(s) », which is the
widest column of the model and the one with the most to say.
