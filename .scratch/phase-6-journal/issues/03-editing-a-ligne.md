# 03 - Editing, adding, removing, reordering a ligne

Type: task
Status: ready-for-agent
Blocked by: 02

**A field saves when it is left** (ADR-0029). Local state per field, `PATCH` on blur when
the value changed, Échap reverts, Entrée commits a one-line field. The response is the
written ligne: put it in the cache with `setQueryData` rather than invalidating, so a
refetch never lands under the cursor of the field being typed in.

`duration_minutes` is a number and may be null. `discipline` is `min_length=1` server-side:
a ligne emptied to nothing is refused with a 422, and the field reverts saying so.

**Adding** — « Ajouter une ligne » posts a discipline the teacher then edits. It lands at
the end (`position` is computed server-side when absent).

**Removing** — one button, no undo, because there is none: the ligne is hers.

**Reordering** — ▲ / ▼, and the request names **every** id of the day in the new order
(all-or-nothing, 400 otherwise). The response is the whole `JournalDay`; it replaces the
cached one.

**The statut** (ADR-0031) is a `PATCH /api/planned-sessions/{id}` from a select on the
ligne, present only where `planned_session_id` is set.

Every mutation that fails shows the server's sentence (ticket 01) beside the row, and
nothing is lost: the field keeps what was typed.

**Done when**: a bilan typed and blurred survives a reload ; ▲ on the second ligne swaps
it with the first and the order sticks ; a partial order is impossible to send ; an emptied
discipline reverts with the server's message.
