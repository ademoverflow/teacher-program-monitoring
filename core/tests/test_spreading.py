"""The one rule that spreads a progression over the year's créneaux."""

from core.services.programmation.spreading import shares, spread

WORKED_MONDAYS = 33
CRENEAUX = 3


def test_shares_cover_every_position_exactly_once() -> None:
    """A progression may not leave a créneau uncovered, nor claim one twice."""
    for count in range(1, 25):
        for slots in range(40):
            covered = [position for share in shares(count, slots) for position in share]

            assert covered == list(range(slots))


def test_shares_differ_in_length_by_at_most_one() -> None:
    """« Réparties sur l'année » means evenly, not four weeks then one."""
    for count in range(1, 25):
        for slots in range(count, 40):
            lengths = {len(share) for share in shares(count, slots)}

            assert max(lengths) - min(lengths) <= 1


def test_the_retz_grammaire_progression_over_the_year_s_lundis() -> None:
    """14 séquences de grammaire, 33 lundis travaillés: five of them get three."""
    lengths = [len(share) for share in shares(14, 33)]

    assert lengths == [2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 3]
    assert sum(lengths) == WORKED_MONDAYS


def test_the_retz_conjugaison_progression_over_the_year_s_mardis() -> None:
    """7 séquences de conjugaison over 36 mardis, before the RETZ advice narrows it."""
    lengths = [len(share) for share in shares(7, 36)]

    assert lengths == [5, 5, 5, 5, 5, 5, 6]


def test_nothing_to_spread_leaves_every_creneau_free() -> None:
    """Poésie has no item de programme; a matière with none must not raise."""
    assert shares(0, 12) == ()
    assert spread((), 3) == ((), (), ())


def test_more_things_than_creneaux_leaves_some_of_them_unplaced() -> None:
    """More thèmes than créneaux in a période: the ones that miss out keep their order.

    The empty shares fall where the even cut puts them rather than all at the end, so
    the things that are placed stay in the order the source prints them.
    """
    placed = shares(5, 3)

    assert [len(share) for share in placed] == [0, 1, 0, 1, 1]
    assert sum(len(share) for share in placed) == CRENEAUX


def test_spread_names_the_owner_of_each_creneau() -> None:
    """The caller reads the plan position by position, in date order."""
    assert spread(("a", "b"), 5) == (("a",), ("a",), ("b",), ("b",), ("b",))
