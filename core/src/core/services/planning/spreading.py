"""Spread N things evenly over M créneaux.

Three placements are the same problem — the RETZ séquences over the year's lundis, the
items d'un programme over the year's créneaux of their matière, the thèmes of a période
over that période's créneaux — and they are all solved here so they are all solved the
same way.
"""

from collections.abc import Sequence


def shares(count: int, slots: int) -> tuple[range, ...]:
    """Cut ``slots`` positions into ``count`` consecutive shares.

    Thing ``i`` of ``n`` owns ``[⌊i·m/n⌋, ⌊(i+1)·m/n⌋)``: the shares differ in length by
    at most one and the longer ones fall evenly across the year rather than bunching at
    one end. When there are fewer positions than things, the shares at the end come out
    empty — the caller reports those rather than working around them.
    """
    if count <= 0:
        return ()
    return tuple(range(slots * i // count, slots * (i + 1) // count) for i in range(count))


def spread[T](things: Sequence[T], slots: int) -> tuple[tuple[T, ...], ...]:
    """Say which thing owns each of ``slots`` positions, in order.

    Returns one tuple per position: the things that own it — one, or none where there
    are more positions than things have been given.
    """
    owners: list[list[T]] = [[] for _ in range(slots)]
    for thing, share in zip(things, shares(len(things), slots), strict=True):
        for position in share:
            owners[position].append(thing)
    return tuple(tuple(owner) for owner in owners)
