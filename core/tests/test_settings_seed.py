"""The seeded réglages resolve the alternances the timetable leaves open.

Read from ``core/seed/settings.json`` and ``core/seed/timetable.json``, so CI checks
them without a database.
"""

from core.services.seed_files import load_settings, load_subjects, load_timetable

SETTINGS = {setting.key: setting for setting in load_settings()}
SLOTS = load_timetable()
SUBJECT_CODES = {subject.code for subject in load_subjects()}

ALTERNATION_PREFIX = "alternance."


def test_every_alternation_group_of_the_timetable_has_a_setting() -> None:
    """ADR-0002 leaves six créneaux without a matière; nothing else resolves them."""
    groups = {slot.alternation_group for slot in SLOTS if slot.alternation_group}

    assert {key.removeprefix(ALTERNATION_PREFIX) for key in SETTINGS} == groups


def test_the_settings_name_matieres_that_exist() -> None:
    """A dangling code would resolve to no matière and leave the créneau empty."""
    named = {
        subject
        for setting in SETTINGS.values()
        for subject in [*setting.value.subjects, *(slot.subject for slot in setting.value.slots)]
    }

    assert named <= SUBJECT_CODES


def test_histoire_and_geographie_rotate_week_by_week() -> None:
    """§4.1: « rotation histoire/géographie, par défaut alternance hebdomadaire »."""
    setting = SETTINGS["alternance.histoire-geographie"].value

    assert setting.mode == "hebdomadaire"
    assert setting.subjects == ["histoire", "geographie"]


def test_arts_and_music_take_one_creneau_each() -> None:
    """§4.1: « un créneau arts plastiques + un créneau éducation musicale par semaine »."""
    setting = SETTINGS["alternance.arts-plastiques-education-musicale"].value

    assert setting.mode == "par-creneau"
    assert [(int(slot.day), slot.subject) for slot in setting.slots] == [
        (1, "arts-plastiques"),
        (4, "education-musicale"),
    ]


def test_each_alternating_creneau_of_the_timetable_is_named_exactly_once() -> None:
    """A « par-creneau » setting must cover its group's créneaux and no others."""
    for key, setting in SETTINGS.items():
        if setting.value.mode != "par-creneau":
            continue
        group = key.removeprefix(ALTERNATION_PREFIX)
        named = {(slot.day, slot.starts_at) for slot in setting.value.slots}
        expected = {(slot.day, slot.starts_at) for slot in SLOTS if slot.alternation_group == group}

        assert named == expected
