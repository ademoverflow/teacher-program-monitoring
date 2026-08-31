"""Histoire and géographie place themselves: a thème names the périodes it wants."""

from core.models.level import Level
from core.services.programmation.inputs import ProgramItem, plan_input_from_seeds
from core.services.programmation.themes import ThemePeriods, assign_periods, periods_of

PLAN = plan_input_from_seeds()
EVERY_THEME = 17


def _themes(subject: str, level: Level) -> tuple[ProgramItem, ...]:
    """Collect the thèmes of one matière at one niveau, in the programme's order."""
    return PLAN.items_of(subject, None, level)


def _read(theme: ProgramItem) -> ThemePeriods:
    """Read what the thème says about its périodes; it must say something."""
    found = periods_of(theme)
    assert found is not None, theme.title
    return found


def test_every_theme_of_the_programme_says_where_it_goes() -> None:
    """All 17 of them: 10 histoire, 7 géographie, no thème left without a placement."""
    themes = [
        theme
        for subject in ("histoire", "geographie")
        for level in (Level.CM1, Level.CM2)
        for theme in _themes(subject, level)
    ]

    assert len(themes) == EVERY_THEME
    assert all(periods_of(theme) for theme in themes)


def test_a_theme_that_names_its_periods_gets_exactly_those() -> None:
    """« (deuxième et troisième périodes) » is the source placing itself."""
    monarchie = _themes("histoire", Level.CM1)[1]

    assert _read(monarchie).codes == ("P2", "P3")


def test_the_one_theme_that_prints_its_period_inside_the_block_is_still_read() -> None:
    """CM2's « Vers une France républicaine » puts « (deuxième période) » in the body."""
    republique = _themes("histoire", Level.CM2)[1]

    assert "période" not in republique.title
    assert _read(republique).codes == ("P2",)


def test_histoire_covers_the_year_at_both_niveaux() -> None:
    """Every période gets a thème d'histoire, and two of them share P2."""
    for level, expected in (
        (Level.CM1, {"P1": 1, "P2": 2, "P3": 1, "P4": 1, "P5": 1}),
        (Level.CM2, {"P1": 1, "P2": 2, "P3": 1, "P4": 1, "P5": 1}),
    ):
        assigned = assign_periods(_themes("histoire", level))
        per_period = dict.fromkeys(expected, 0)
        for codes in assigned.values():
            for code in codes:
                per_period[code] += 1

        assert per_period == expected


def test_geographie_themes_take_the_periods_the_source_leaves_open() -> None:
    """« 1 ou 2 périodes au choix »: the leftover période goes to the first thème."""
    assigned = assign_periods(_themes("geographie", Level.CM1))
    themes = _themes("geographie", Level.CM1)

    assert [assigned[theme.key] for theme in themes] == [("P1", "P2"), ("P3",), ("P4",), ("P5",)]


def test_geographie_cm2_fills_the_five_periods_exactly() -> None:
    """2 + 2 + 1 périodes, and the year has five."""
    themes = _themes("geographie", Level.CM2)
    assigned = assign_periods(themes)

    assert [assigned[theme.key] for theme in themes] == [("P1", "P2"), ("P3", "P4"), ("P5",)]


def test_no_theme_is_left_without_a_periode() -> None:
    """A thème with no période would be a piece of programme never taught."""
    for subject in ("histoire", "geographie"):
        for level in (Level.CM1, Level.CM2):
            themes = _themes(subject, level)
            assigned = assign_periods(themes)

            assert set(assigned) == {theme.key for theme in themes}
            assert all(assigned[theme.key] for theme in themes)
