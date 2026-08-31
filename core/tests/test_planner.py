"""The year the generator plans, checked against the EDT and the méthodos.

Built from the versioned seeds rather than from the database, so the counts §8 Phase 3
asks for are checked by CI even though CI has no Postgres.
"""

from collections import Counter, defaultdict
from datetime import date

from core.models.level import Level
from core.models.weekday import Weekday
from core.services.planning import ProblemKind, plan_input_from_seeds, plan_year
from core.services.planning.inputs import Sequence as MethodSequence
from core.services.planning.planner import (
    MATHS_SESSIONS_PER_SEQUENCE,
    OEUVRE_SUIVIE_LABEL,
    REVISION_SUFFIX,
    SessionDraft,
    is_maths_lesson,
    is_retz,
    session_levels,
)
from core.services.planning.themes import assign_periods

PLAN_INPUT = plan_input_from_seeds()
PLAN = plan_year(PLAN_INPUT)
SLOTS = {slot.key: slot for slot in PLAN_INPUT.slots}
SEQUENCES = {sequence.key: sequence for sequence in PLAN_INPUT.sequences}
ITEMS = {item.key: item for item in PLAN_INPUT.program_items}
WEEK_OF = {day.date: day.week_number for day in PLAN_INPUT.days}
PERIOD_OF = {week.number: week.period_code for week in PLAN_INPUT.weeks}

# 1532 couples (jour de classe, créneau), plus the six créneaux that carry per-niveau
# content and so become two séances: 2 x 33 lundis + 2 x 36 mardis + 35 jeudis + 35
# vendredis = 208.
EXPECTED_SESSIONS = 1740
TAUGHT_DAYS = 139
DAYS_OFF = (date(2027, 3, 29), date(2027, 5, 6), date(2027, 5, 7), date(2027, 5, 17))
SPLIT_SLOTS = 6
MATHS_SEQUENCES = 35
RETZ_SEQUENCES = 21
OEUVRE_CRENEAUX = 33
LITTERATURE_STEPS = 36
OEUVRES = 8


def _week(session: SessionDraft) -> int:
    """Return the semaine a séance falls in."""
    return WEEK_OF[session.date]


def _sequence_of(session: SessionDraft) -> MethodSequence:
    """Return the séquence a séance runs; only call it on a séance that has one."""
    assert session.sequence is not None
    return SEQUENCES[session.sequence]


def _sessions_of_method(method: str) -> tuple[SessionDraft, ...]:
    """Collect every séance driven by one méthodo, in date order."""
    return tuple(
        session
        for session in PLAN.sessions
        if session.sequence and SEQUENCES[session.sequence].method == method
    )


# --------------------------------------------------------------------- the grid


def test_every_taught_creneau_of_the_year_carries_exactly_one_seance() -> None:
    """§8 Phase 3: « chaque créneau de chaque jour couvert »."""
    owed = {
        (day.date, slot.key, level)
        for day in PLAN_INPUT.taught_days()
        for slot in PLAN_INPUT.slots_of(day.day_of_week)
        for level in session_levels(slot)
    }
    planned = [(session.date, session.slot, session.level) for session in PLAN.sessions]

    assert len(planned) == len(set(planned))
    assert set(planned) == owed
    assert len(planned) == EXPECTED_SESSIONS


def test_the_count_is_the_grid_plus_the_creneaux_split_by_niveau() -> None:
    """The total is arithmetic, not a number to be believed (ADR-0010)."""
    per_weekday = Counter(day.day_of_week for day in PLAN_INPUT.taught_days())
    slots_per_weekday = Counter(slot.day_of_week for slot in PLAN_INPUT.slots)
    pairs = sum(per_weekday[weekday] * slots_per_weekday[weekday] for weekday in per_weekday)
    split = sum(
        per_weekday[slot.day_of_week]
        for slot in PLAN_INPUT.slots
        if len(session_levels(slot)) == 2  # noqa: PLR2004
    )

    assert pairs == 1532  # noqa: PLR2004
    assert split == EXPECTED_SESSIONS - pairs
    assert len(PLAN_INPUT.taught_days()) == TAUGHT_DAYS


def test_no_seance_falls_on_a_jour_chome() -> None:
    """§8 Phase 3: « aucune séance hors créneau/jour off » (ADR-0001)."""
    planned_days = {session.date for session in PLAN.sessions}

    assert planned_days.isdisjoint(DAYS_OFF)
    assert len(planned_days) == TAUGHT_DAYS


def test_only_a_creneau_driven_by_a_per_niveau_methodo_is_split() -> None:
    """The four maths créneaux and the two RETZ ones, and nothing else (ADR-0010)."""
    split = [slot for slot in PLAN_INPUT.slots if len(session_levels(slot)) == 2]  # noqa: PLR2004

    assert len(split) == SPLIT_SLOTS
    assert all(is_maths_lesson(slot) or is_retz(slot) for slot in split)
    assert all(slot.level is Level.COMMUN for slot in split)


def test_a_seance_runs_in_the_creneau_it_says_it_does() -> None:
    """A séance may not move: the EDT is immutable (§10)."""
    for session in PLAN.sessions:
        slot = SLOTS[session.slot]

        assert Weekday(session.date.isoweekday()) == slot.day_of_week
        assert session.level in session_levels(slot)


def test_the_day_is_ordered_from_the_first_creneau_to_the_last() -> None:
    """``position`` is the order of the day, which the cahier journal is printed in."""
    by_day: dict[date, list[SessionDraft]] = defaultdict(list)
    for session in PLAN.sessions:
        by_day[session.date].append(session)

    for sessions in by_day.values():
        ordered = sorted(sessions, key=lambda session: session.position)
        starts = [SLOTS[session.slot].starts_at for session in ordered]

        assert [session.position for session in ordered] == list(range(1, len(ordered) + 1))
        assert starts == sorted(starts)


# ---------------------------------------------------------------- les séquences


def test_every_maths_sequence_is_placed_in_order_one_per_semaine() -> None:
    """§8 Phase 3: « couverture des 35 séquences x 2 », sans trou."""
    for level in (Level.CM1, Level.CM2):
        method = f"maths-{level.value.lower()}"
        weeks_of: dict[int, set[int]] = defaultdict(set)
        for session in _sessions_of_method(method):
            weeks_of[_sequence_of(session).number].add(_week(session))

        assert sorted(weeks_of) == list(range(1, MATHS_SEQUENCES + 1))
        assert all(weeks == {number} for number, weeks in weeks_of.items())
        assert PLAN.sequences_placed[method] == MATHS_SEQUENCES


def test_a_maths_sequence_fills_the_four_maths_creneaux_of_its_semaine() -> None:
    """§4.3: « une suite de 4 séances … sur les créneaux Mathématiques » (ADR-0011)."""
    sessions = _sessions_of_method("maths-cm1")
    full = [session for session in sessions if _week(session) == 17]  # noqa: PLR2004

    assert all(is_maths_lesson(SLOTS[session.slot]) for session in sessions)
    assert len(full) == MATHS_SESSIONS_PER_SEQUENCE
    assert [session.title[-6:] for session in full] == ["e 1/4)", "e 2/4)", "e 3/4)", "e 4/4)"]


def test_a_semaine_short_of_maths_creneaux_places_fewer_and_says_so() -> None:
    """S1 has no lundi; three semaines lose a maths créneau to a jour chômé (§10)."""
    short = {
        _week(session)
        for level in ("cm1", "cm2")
        for session in _sessions_of_method(f"maths-{level}")
    }
    counted = Counter(
        (_week(session), session.level) for session in _sessions_of_method("maths-cm1")
    )
    lacking = {week for (week, _), count in counted.items() if count < MATHS_SESSIONS_PER_SEQUENCE}

    assert short == set(range(1, MATHS_SEQUENCES + 1))
    assert lacking == {1, 25, 28, 30}
    reported = [p for p in PLAN.problems if "créneaux de mathématiques" in p.message]

    assert len(reported) == 2 * len(lacking)
    assert {p.kind for p in reported} == {ProblemKind.CALENDRIER}


def test_the_last_semaine_is_the_marge_the_calendar_leaves() -> None:
    """§4.2: 35 séquences for 36 semaines — « dernière semaine = révisions »."""
    revisions = [session for session in PLAN.sessions if session.title.endswith(REVISION_SUFFIX)]

    assert {_week(session) for session in revisions} == {len(PLAN_INPUT.weeks)}
    assert len(revisions) == 2 * MATHS_SESSIONS_PER_SEQUENCE


def test_every_retz_sequence_is_placed_on_the_creneau_of_its_domaine() -> None:
    """§4.4: grammaire le lundi, conjugaison le mardi."""
    for level in (Level.CM1, Level.CM2):
        method = f"retz-{level.value.lower()}"
        sessions = _sessions_of_method(method)
        numbers = {_sequence_of(session).number for session in sessions}

        assert numbers == set(range(1, RETZ_SEQUENCES + 1))
        assert PLAN.sequences_placed[method] == RETZ_SEQUENCES
        assert all(is_retz(SLOTS[session.slot]) for session in sessions)
        assert all(session.level == level for session in sessions)
        for session in sessions:
            slot = SLOTS[session.slot]
            expected = Weekday.MONDAY if slot.domain == "grammaire" else Weekday.TUESDAY

            assert slot.day_of_week == expected


def test_a_retz_sequence_runs_over_consecutive_creneaux() -> None:
    """A séquence is a run, not a scattering: its créneaux follow one another."""
    for method in ("retz-cm1", "retz-cm2"):
        by_sequence: dict[str, list[date]] = defaultdict(list)
        for session in _sessions_of_method(method):
            by_sequence[_sequence_of(session).key].append(session.date)

        for key, days in by_sequence.items():
            ordered = sorted(days)
            weeks = [WEEK_OF[day] for day in ordered]
            same_slot = {
                other.slot for other in _sessions_of_method(method) if other.sequence == key
            }

            assert len(same_slot) == 1
            assert weeks == sorted(weeks)


def test_conjugaison_waits_for_the_grammaire_sequence_on_the_verb() -> None:
    """§4.4 relays RETZ: « ne démarrer … la conjugaison qu'après les notions de verbe »."""
    for method in ("retz-cm1", "retz-cm2"):
        sessions = _sessions_of_method(method)
        verb = max(
            session.date
            for session in sessions
            if _sequence_of(session).title.startswith("Le verbe")
        )
        conjugation = [
            session for session in sessions if SLOTS[session.slot].domain == "conjugaison"
        ]

        assert conjugation
        assert min(session.date for session in conjugation) > verb


def test_a_conjugaison_creneau_before_retz_opens_still_carries_the_programme() -> None:
    """The créneau exists every week; it works on the programme until RETZ reaches it."""
    waiting = [
        session
        for session in PLAN.sessions
        if SLOTS[session.slot].domain == "conjugaison" and not session.sequence
    ]

    assert waiting
    assert all(session.program_items for session in waiting)
    assert all(session.level in (Level.CM1, Level.CM2) for session in waiting)


# --------------------------------------------------------------- la littérature


def test_the_oeuvres_are_read_in_the_creneau_oeuvre_suivie_and_nowhere_else() -> None:
    """§4.5 names the lundi 11h30 créneau; nothing else carries a séance de séquence."""
    steps = [session for session in PLAN.sessions if session.sequence_step]

    assert steps
    assert {SLOTS[session.slot].label for session in steps} == {OEUVRE_SUIVIE_LABEL}
    assert {session.level for session in steps} == {Level.COMMUN}


def test_the_year_is_three_oeuvre_creneaux_short_of_the_planning() -> None:
    """36 semaines d'œuvres for 33 lundis: an impossibility, reported not worked around."""
    creneaux = [
        session for session in PLAN.sessions if SLOTS[session.slot].label == OEUVRE_SUIVIE_LABEL
    ]
    steps = sum(len(sequence.steps) for sequence in PLAN_INPUT.sequences_of("litterature"))

    assert len(creneaux) == OEUVRE_CRENEAUX
    assert steps == LITTERATURE_STEPS
    assert sum(bool(session.sequence_step) for session in creneaux) == OEUVRE_CRENEAUX


def test_charlie_opens_the_year_over_its_seven_weeks() -> None:
    """§4.5 puts Charlie in P1; its planning is seven semaines and P1 has six lundis."""
    charlie = [
        session
        for session in PLAN.sessions
        if session.sequence and _sequence_of(session).title == "Charlie et la chocolaterie"
    ]

    assert len(charlie) == 7  # noqa: PLR2004
    assert [_week(session) for session in charlie] == [2, 3, 4, 5, 6, 7, 8]
    assert charlie[0].title.endswith("Semaine 1")
    assert charlie[0].content
    assert charlie[0].materials


def test_an_oeuvre_never_starts_before_the_periode_it_is_read_in() -> None:
    """§4.5 assigns each œuvre a période; running late is allowed, running early is not."""
    order = ("P1", "P2", "P3", "P4", "P5")
    for session in PLAN.sessions:
        if not session.sequence_step:
            continue
        oeuvre = _sequence_of(session)
        if oeuvre.title == "Hansel et Gretel" or oeuvre.period_code is None:
            continue

        assert order.index(PERIOD_OF[_week(session)]) >= order.index(oeuvre.period_code)


def test_two_of_the_eight_oeuvres_are_never_read() -> None:
    """The year is short: six œuvres get séances, and the report names the other two.

    « Hansel et Gretel » is the repli §4.5 keeps in reserve and « Zathura » has no
    weekly planning in the source at all (ADR-0017).
    """
    read = {_sequence_of(session).title for session in PLAN.sessions if session.sequence_step}

    oeuvres = PLAN_INPUT.sequences_of("litterature")

    assert len(oeuvres) == OEUVRES
    assert PLAN.sequences_placed["litterature"] == OEUVRES - 2
    assert len(read) == OEUVRES - 2
    assert {oeuvre.title for oeuvre in oeuvres} - read == {"Hansel et Gretel", "Zathura"}


def test_the_repli_and_the_oeuvre_without_a_planning_are_reported() -> None:
    """§4.5 makes Hansel the repli; the source gives Zathura no weekly planning (ADR-0017)."""
    problems = "\n".join(problem.message for problem in PLAN.problems)

    assert "Zathura" in problems
    assert "Hansel et Gretel" in problems
    assert "Jumanji" in problems


# ---------------------------------------------------------------- les alternances


def test_histoire_and_geographie_alternate_week_by_week_for_each_niveau() -> None:
    """§4.1: « rotation histoire/géographie, par défaut alternance hebdomadaire »."""
    for level in (Level.CM1, Level.CM2):
        by_week: dict[int, set[str | None]] = defaultdict(set)
        for session in PLAN.sessions:
            if session.subject in ("histoire", "geographie") and session.level == level:
                by_week[_week(session)].add(session.subject)

        assert all(len(subjects) == 1 for subjects in by_week.values())
        assert {week: subjects.pop() for week, subjects in by_week.items()} == {
            week: "histoire" if week % 2 else "geographie" for week in by_week
        }


def test_both_alternations_come_out_balanced_over_the_year() -> None:
    """§8 Phase 3: « alternances équilibrées »."""
    histoire, geographie = PLAN.alternations["histoire"], PLAN.alternations["geographie"]
    arts, musique = (
        PLAN.alternations["arts-plastiques"],
        PLAN.alternations["education-musicale"],
    )

    assert abs(histoire - geographie) <= len(PLAN_INPUT.weeks) // 10
    assert abs(arts - musique) <= len(PLAN_INPUT.weeks) // 10
    assert histoire + geographie == 142  # noqa: PLR2004


def test_arts_plastiques_and_education_musicale_take_one_creneau_each_a_week() -> None:
    """§4.1: « un créneau arts plastiques + un créneau éducation musicale par semaine »."""
    days = {
        subject: {
            SLOTS[session.slot].day_of_week
            for session in PLAN.sessions
            if session.subject == subject
        }
        for subject in ("arts-plastiques", "education-musicale")
    }

    assert days["arts-plastiques"] == {Weekday.MONDAY}
    assert days["education-musicale"] == {Weekday.THURSDAY}


def test_a_theme_is_taught_in_a_periode_its_intitule_names() -> None:
    """Histoire and géographie place themselves by their thèmes (ADR-0016)."""
    for subject in ("histoire", "geographie"):
        for level in (Level.CM1, Level.CM2):
            periods = assign_periods(PLAN_INPUT.items_of(subject, None, level))
            taught = [
                session
                for session in PLAN.sessions
                if session.subject == subject and session.level == level
            ]

            assert taught
            for session in taught:
                assert len(session.program_items) == 1
                assert PERIOD_OF[_week(session)] in periods[session.program_items[0]]


# ------------------------------------------------- les rituels et le générique


def test_a_rituel_keeps_its_whole_programme_every_day() -> None:
    """A rituel repeats rather than progresses (ADR-0015)."""
    for session in PLAN.sessions:
        slot = SLOTS[session.slot]
        if not slot.is_ritual or slot.subject is None:
            continue
        whole = {
            item.key
            for level in PLAN_INPUT.levels_with_items(slot.subject, slot.domain)
            for item in PLAN_INPUT.items_of(slot.subject, slot.domain, level)
        }

        assert set(session.program_items) == whole


def test_the_accueil_carries_its_intitule_and_nothing_else() -> None:
    """The only créneau of the EDT with neither matière nor domaine."""
    accueil = [session for session in PLAN.sessions if session.subject is None]

    assert len(accueil) == TAUGHT_DAYS
    assert {session.title for session in accueil} == {
        "Accueil · rituel de langue · plan de travail"
    }
    assert not any(session.program_items for session in accueil)


def test_a_seance_never_links_an_item_of_another_matiere() -> None:
    """A link is a claim about the programme; a wrong one is worse than none."""
    for session in PLAN.sessions:
        subjects = {ITEMS[key].subject for key in session.program_items}

        assert subjects <= {session.subject}


def test_a_generic_seance_walks_its_programme_across_the_year() -> None:
    """Every item of a matière is reached, in the order the programme prints it."""
    seen: dict[tuple[str, Level], list[str]] = defaultdict(list)
    for session in sorted(PLAN.sessions, key=lambda session: (session.date, session.position)):
        for key in session.program_items:
            item = ITEMS[key]
            if item.subject == "sciences-et-technologie" and not SLOTS[session.slot].is_ritual:
                seen[item.subject, item.level].append(item.title)

    for (_, level), titles in seen.items():
        expected = [
            item.title for item in PLAN_INPUT.items_of("sciences-et-technologie", None, level)
        ]
        ordered = [
            title for index, title in enumerate(titles) if index == 0 or titles[index - 1] != title
        ]

        assert ordered == expected


def test_the_friday_creneau_carries_the_dictee_bilan_and_the_poesie() -> None:
    """Poésie has no programme of its own — it is an entrée de français (ADR-0014)."""
    poetry = [session for session in PLAN.sessions if session.title == "Dictée bilan / Poésie"]

    assert len(poetry) == 35  # noqa: PLR2004
    for session in poetry:
        domains = {ITEMS[key].domain for key in session.program_items}

        assert domains == {"orthographe", "culture-litteraire-et-artistique"}


# ------------------------------------------------------------------- le rapport


def test_the_validation_report_holds_no_error() -> None:
    """§8 Phase 3: « rapport de validation sans erreur ».

    The year always has something to report — S1 has no lundi, four jours are chômés,
    and the littérature planning is longer than the year — but none of it is an error.
    """
    kinds = Counter(problem.kind for problem in PLAN.problems)

    assert not [problem for problem in PLAN.problems if problem.kind is ProblemKind.ERREUR]
    assert kinds == {ProblemKind.CALENDRIER: 11, ProblemKind.SOURCE: 1}


def test_every_reported_impossibility_names_what_the_year_took_away() -> None:
    """A report line the teacher cannot act on is worse than none."""
    expected = ("créneaux de mathématiques", "Lecture — Œuvre suivie", "planning hebdomadaire")

    assert PLAN.problems
    assert all(any(reason in problem.message for reason in expected) for problem in PLAN.problems)


def test_the_plan_is_the_same_every_time_it_is_built() -> None:
    """Deterministic: no set iteration order, no clock, no randomness."""
    assert plan_year(plan_input_from_seeds()) == PLAN
