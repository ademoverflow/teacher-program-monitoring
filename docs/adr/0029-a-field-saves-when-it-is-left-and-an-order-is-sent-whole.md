# A field saves when it is left, and an order is sent whole

`EditableText` holds a draft, and commits it with a `PATCH` when the field loses the focus
and the text has changed. Échap puts back what the server has. Entrée commits, except in a
field whose value may itself hold newlines — the objectifs and the bilan.

The three candidates were a save button, a debounce on the keystroke, and the blur. A
button is a second thing to remember on a page whose whole point is that it is written in
while the day is being lived. A debounce writes a `PATCH` per pause and still loses the last
edit when the tab is closed inside the delay — the exact edit the teacher cared about, the
bilan she wrote last. The blur writes once, writes what is there, and is triggered by
everything that ends an edit: Tab, a click on the next field, closing the row. The bilan and
the discipline behave the same way; the difference between a long field and a short one
turned out to be about *shape*, not about when to save (`FieldShape`: a durée is a line, a
discipline wraps, a bilan is a block).

**The draft is committed from a ref, not from the render's state.** A change and a blur
landing in the same task — a paste followed by a click — would otherwise send the value the
previous render closed over, which is the one that was just replaced. A test drives exactly
that.

**Nothing refetches after an edit.** The `PATCH` returns the written ligne and it is put
into the cache with `setQueryData`. Invalidating `["journal", date]` instead would refetch
while the teacher is already typing in the next field, and a re-seeded draft under a moving
cursor is a lost sentence. `["day", date]` *is* invalidated on the structural changes —
adding, removing, initialising — because `has_journal` changes and nothing is being typed
into that response.

## Reordering is two buttons, and sends every id

`PUT /api/journal/{date}/order` takes the whole order and refuses anything else with a 400
(ADR-0021's list, not a set). So ▲ and ▼ compute the day's full list of ids with two
swapped and send that; `moveEntry` is a pure function over the id list and is tested as one.

§8 offers « drag & drop **ou** boutons ». Drag and drop needs a dependency the repo does not
have, needs a keyboard story of its own to stay usable, and buys a gesture for an operation
the teacher performs a few times a day at most — a séance that ran over, one moved after
another. The buttons need nothing, are reachable by keyboard for free, and cannot express a
partial order, which is the shape the endpoint refuses.
