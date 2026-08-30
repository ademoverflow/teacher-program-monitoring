"""The seeded séquences are the ones the méthodos lay out (MASTER-PROMPT.md §4.3 to §4.5).

Read from ``core/seed/sequences.json``, so the counts §8 Phase 2 asks for are checked
by CI even though CI has no database.
"""

from collections import Counter

from core.models.level import Level
from core.services.seed_files import SequenceSeed, load_sequences, load_subjects

SEQUENCES = load_sequences()
SUBJECTS = load_subjects()

SEQUENCES_PER_METHOD = {
    "maths-cm1": 35,
    "maths-cm2": 35,
    "retz-cm1": 21,
    "retz-cm2": 21,
    "litterature": 8,
}
PERIOD_CODES = {"P1", "P2", "P3", "P4", "P5"}

# §4.5, in the order the périodes take them.
OEUVRES = (
    "Charlie et la chocolaterie",
    "Hansel et Gretel",
    "Contes de Perrault",
    "Emilie et le crayon magique",
    "Sherlock Holmes",
    "Le Magicien d’Oz",
    "Jumanji",
    "Zathura",
)
CHARLIE_WEEKS = 7

# §4.3 spreads both niveaux the same way: « les nombres de séquences par période
# (7/7/6/7/8) ne coïncident pas exactement avec les semaines des périodes ».
MATHS_PERIODS = {"P1": 7, "P2": 7, "P3": 6, "P4": 7, "P5": 8}


def _sequences_of(method: str) -> list[SequenceSeed]:
    """Collect the séquences of one méthodo, in number order."""
    return sorted((s for s in SEQUENCES if s.method == method), key=lambda s: s.number)


def test_every_methodo_has_the_sequences_it_announces() -> None:
    """§8 Phase 2: 35 séquences de maths par niveau, 21 RETZ par niveau, les 8 œuvres."""
    assert Counter(sequence.method for sequence in SEQUENCES) == SEQUENCES_PER_METHOD


def test_sequences_are_unique_on_their_natural_key() -> None:
    """(method, number) is what ``make seed`` upserts on."""
    keys = [(sequence.method, sequence.number) for sequence in SEQUENCES]

    assert len(set(keys)) == len(keys)


def test_each_methodo_is_numbered_from_one_without_a_hole() -> None:
    """The generator (Phase 3) walks the séquences in order: a hole would skip a week."""
    for method, count in SEQUENCES_PER_METHOD.items():
        assert [sequence.number for sequence in _sequences_of(method)] == list(range(1, count + 1))


def test_maths_sequences_carry_the_titles_of_the_document() -> None:
    """§4.3 is authoritative for the maths méthodo — the PDFs only confirm it."""
    cm1 = _sequences_of("maths-cm1")
    cm2 = _sequences_of("maths-cm2")

    assert cm1[0].title == "Nombres jusqu'à 9999"
    assert cm1[11].title == "Addition et soustraction de nombres décimaux"
    assert cm1[34].title == "Angles"
    assert cm2[0].title == "Nombres jusqu'à 999 999"
    assert cm2[34].title == "Solides"
    assert {sequence.level for sequence in cm1} == {Level.CM1}
    assert {sequence.level for sequence in cm2} == {Level.CM2}


def test_maths_sequences_sit_in_the_periods_the_methodo_gives_them() -> None:
    """§4.3 prints them période by période; Phase 3 decides the real weeks."""
    assert Counter(s.period_code for s in _sequences_of("maths-cm1")) == MATHS_PERIODS
    assert Counter(s.period_code for s in _sequences_of("maths-cm2")) == MATHS_PERIODS


def test_retz_sequences_carry_the_titles_of_the_document() -> None:
    """§4.4: 21 séquences per niveau, bonus ones included."""
    cm1 = _sequences_of("retz-cm1")
    cm2 = _sequences_of("retz-cm2")

    assert cm1[0].title == "Les groupes dans la phrase"
    assert cm1[20].title == "Le passé simple des verbes à la 3e personne (bonus)"
    assert cm2[0].title == "Les groupes dans la phrase"
    assert cm2[20].title == "La proposition subordonnée relative (bonus)"
    assert {sequence.subject for sequence in cm1 + cm2} == {"francais"}


def test_every_retz_cm1_sequence_carries_the_objectives_the_pdf_prints() -> None:
    """The CM1 progression prints objectives for each séquence; the CM2 one does not."""
    assert all(sequence.objectives for sequence in _sequences_of("retz-cm1"))
    assert not any(sequence.objectives for sequence in _sequences_of("retz-cm2"))


def test_retz_sequences_say_whether_they_are_grammaire_or_conjugaison() -> None:
    """The CM1 progression colour-codes them; the EDT teaches them on different days."""
    domains = Counter(sequence.domain for sequence in _sequences_of("retz-cm1"))

    assert domains == {"grammaire": 14, "conjugaison": 7}
    assert not any(sequence.domain for sequence in _sequences_of("retz-cm2"))


def test_the_eight_oeuvres_of_the_year_are_all_there() -> None:
    """§4.5, numbered in the order of the périodes they are read in."""
    litterature = _sequences_of("litterature")

    assert tuple(sequence.title for sequence in litterature) == OEUVRES
    assert [sequence.period_code for sequence in litterature] == [
        "P1",
        "P1",
        "P2",
        "P3",
        "P3",
        "P4",
        "P5",
        "P5",
    ]
    assert {sequence.level for sequence in litterature} == {Level.COMMUN}


def test_charlie_runs_over_the_seven_weeks_of_its_planning() -> None:
    """§8 Phase 2: « Charlie = 7 semaines de séances dans le PDF par semaine »."""
    charlie = next(s for s in SEQUENCES if s.title == "Charlie et la chocolaterie")

    assert len(charlie.sessions) == CHARLIE_WEEKS
    assert [session.number for session in charlie.sessions] == list(range(1, CHARLIE_WEEKS + 1))
    assert all(session.content and session.materials for session in charlie.sessions)


def test_weekly_seances_are_unique_within_their_sequence() -> None:
    """(sequence, number) is what ``make seed`` upserts sequence_sessions on."""
    for sequence in SEQUENCES:
        numbers = [session.number for session in sequence.sessions]
        assert len(set(numbers)) == len(numbers)


def test_every_sequence_names_a_matiere_and_a_domaine_the_seeds_know() -> None:
    """A dangling code would raise at seed time rather than land as NULL."""
    known = {(subject.code, domain.code) for subject in SUBJECTS for domain in subject.domains}
    subjects = {subject.code for subject in SUBJECTS}

    assert {s.subject for s in SEQUENCES if s.subject} <= subjects
    assert {(s.subject, s.domain) for s in SEQUENCES if s.domain} <= known


def test_periods_are_the_ones_the_calendar_knows() -> None:
    """``period_code`` is free text with no foreign key; it must still line up."""
    assert {s.period_code for s in SEQUENCES if s.period_code} <= PERIOD_CODES
