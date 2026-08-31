# 04 - The printable cahier journal

Type: task
Status: ready-for-agent
Blocked by: 02

`@media print` on `/jour/$date` (ADR-0030), not a second route.

What prints is `docs/exemple-cahier-journal-quotidien.pdf`: the two header lines, the
three-column table, la récréation and la pause méridienne across it. What does not: the
sidebar, the jour navigation, the controls column, « Programmation du jour », the buttons.

The fields auto-size to their content so nothing is clipped, and print with no border and
no background — a printed cahier journal must not look like a form.

**Done when**: the print preview of 2026-09-07 is the model's page, and no control of the
screen version appears on it.
