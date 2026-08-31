# 04 - Spread N things over M créneaux, evenly and deterministically

Type: task
Status: resolved

Three placements are the same problem: 14 RETZ grammaire séquences over 33 lundis, the
items de programme of a matière over the year's créneaux of that matière, the thèmes
of a période over that période's histoire créneaux.

One helper: thing `i` of `n` owns the créneaux `[floor(i·m/n), floor((i+1)·m/n))`.
Lengths differ by at most one and the spread is even across the year.

**Done when**: the helper is total (n = 0, n > m, m = 0 all answered), and its tests
pin the exact split of 33 over 14 and 36 over 7.
