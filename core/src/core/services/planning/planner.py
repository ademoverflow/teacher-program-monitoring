"""Turn the year, the timetable and the méthodos into the séances of the year.

Deterministic and pure: the same input always gives the same plan, and no database is
involved. Four rules fill a créneau — a séquence, an alternance resolved to a matière, a
rituel, and otherwise the items de programme of the créneau's matière spread over the
year's occurrences of it. Whatever the rules cannot hold is reported, never worked
around: the EDT is immutable (§10).
"""

from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from datetime import date

from core.models.level import Level
from core.services.planning.inputs import (
    PlanInput,
    PlannedDay,
    ProgramItem,
    Slot,
)
from core.services.planning.inputs import (
    Sequence as MethodSequence,
)
from core.services.planning.problems import Problem, ProblemKind
from core.services.planning.retz import (
    CONJUGAISON,
    GRAMMAIRE,
    RETZ_CM2_DOMAINS,
    VERB_SEQUENCE_PREFIX,
)
from core.services.planning.spreading import shares, spread
from core.services.planning.themes import assign_periods

# §4.3: a maths séquence is « une suite de 4 séances » on the week's maths créneaux.
MATHS_SESSIONS_PER_SEQUENCE = 4
MATHS = "mathematiques"
FRANCAIS = "francais"
# The four maths cells of the EDT that teach a lesson. Calcul mental and the ateliers
# problèmes are the timetable's other two maths domaines and are not séquence work.
MATHS_LESSON_DOMAINS = ("nombres", "calculs", "grandeurs-et-mesures", "geometrie")
RETZ_DOMAINS = (GRAMMAIRE, CONJUGAISON)
HISTORY_AND_GEOGRAPHY = ("histoire", "geographie")
# §4.5 names this créneau as the one the œuvres are read in.
OEUVRE_SUIVIE_LABEL = "Lecture — Œuvre suivie"
LITTERATURE = "litterature"
# §4.5: « Hansel et Gretel (repli en P5 si manque de temps) » — the fallback, read last.
LITTERATURE_FALLBACK = "Hansel et Gretel"
FALLBACK_PERIOD = "P5"
# §4.2 gives the year one week of margin over the 35 maths séquences: « dernière
# semaine = révisions/bilans/fin des œuvres ».
REVISION_SUFFIX = " — révisions"
# The poésie half of the vendredi 12h00 créneau. Poésie has no programme of its own:
# it is an entrée of « Culture littéraire et artistique » in français (ADR-0014).
POETRY_SLOT_LABEL = "Dictée bilan / Poésie"
POETRY_DOMAIN = "culture-litteraire-et-artistique"
POETRY_ITEM_TITLE = "Savourer le goût des mots, imaginer et créer en poésie"

LEVEL_ORDER = {Level.COMMUN: 0, Level.CM1: 1, Level.CM2: 2}

CellId = tuple[date, str, Level]


@dataclass(frozen=True, slots=True)
class Cell:
    """One séance to fill: a jour de classe, a créneau, and the niveau it is for."""

    day: PlannedDay
    slot: Slot
    level: Level
    subject: str | None

    @property
    def id(self) -> CellId:
        """Return what identifies the séance — the natural key of ``planned_sessions``."""
        return (self.day.date, self.slot.key, self.level)


@dataclass(frozen=True, slots=True)
class Fill:
    """What a rule decided to put in a cell."""

    title: str
    objectives: str | None = None
    content: str | None = None
    materials: str | None = None
    domain: str | None = None
    sequence: str | None = None
    sequence_step: str | None = None
    items: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SessionDraft:
    """A séance, ready to be written, holding natural keys rather than UUIDs."""

    date: date
    slot: str
    level: Level
    title: str
    objectives: str | None
    content: str | None
    materials: str | None
    subject: str | None
    domain: str | None
    sequence: str | None
    sequence_step: str | None
    program_items: tuple[str, ...]
    position: int


@dataclass(frozen=True, slots=True)
class Plan:
    """Every séance of the year, and everything the rules could not hold."""

    sessions: tuple[SessionDraft, ...]
    problems: tuple[Problem, ...]
    sequences_placed: dict[str, int] = field(default_factory=dict)
    alternations: dict[str, int] = field(default_factory=dict)


def is_maths_lesson(slot: Slot) -> bool:
    """Say whether a créneau is one of the four the maths séquence runs in (§4.3)."""
    return slot.subject == MATHS and slot.domain in MATHS_LESSON_DOMAINS


def is_retz(slot: Slot) -> bool:
    """Say whether a créneau is the grammaire or the conjugaison one RETZ fills (§4.4)."""
    return slot.subject == FRANCAIS and slot.domain in RETZ_DOMAINS


def is_oeuvre_suivie(slot: Slot) -> bool:
    """Say whether a créneau is the one the œuvres are read in (§4.5)."""
    return slot.label == OEUVRE_SUIVIE_LABEL


def session_levels(slot: Slot) -> tuple[Level, ...]:
    """Return the niveaux a créneau produces a séance for.

    A commun créneau becomes two séances — one per niveau — exactly when a méthodo
    written per niveau drives it: the four maths créneaux and the two RETZ ones. That is
    a property of the créneau, fixed for the whole year, so the week keeps its shape even
    in the semaine no séquence reaches (ADR-0010).
    """
    if slot.level is not Level.COMMUN:
        return (slot.level,)
    if is_maths_lesson(slot) or is_retz(slot):
        return (Level.CM1, Level.CM2)
    return (Level.COMMUN,)


def addresses(cell_level: Level, item_level: Level) -> bool:
    """Say whether a séance at one niveau works on a programme written for another.

    A commun séance works on both niveaux' programmes; a programme written for the
    cycle rather than for a niveau — EPS, arts plastiques, éducation musicale — is
    worked on by every séance.
    """
    return item_level is Level.COMMUN or cell_level is Level.COMMUN or cell_level == item_level


def _objectives_from(items: Sequence[ProgramItem]) -> str | None:
    """Write the linked items' intitulés as the séance's objectifs & compétences."""
    if not items:
        return None
    if len({item.level for item in items}) == 1:
        return "\n".join(item.title for item in items)
    return "\n".join(f"{item.level.value} — {item.title}" for item in items)


def _fill_from_items(slot: Slot, items: Sequence[ProgramItem]) -> Fill:
    """Build the fill of a séance whose content is items de programme.

    The séance is named after the part of the programme it works on when the items
    agree on one intitulé — a week of « Anglais » says little, « Écouter et comprendre »
    says what is planned. When they do not agree, which is every rituel (it keeps its
    whole programme) and every commun séance whose two niveaux read differently, the
    créneau's own intitulé is the honest name.
    """
    titles = {item.title for item in items}
    domains = {item.domain for item in items}
    return Fill(
        title=titles.pop() if len(titles) == 1 else slot.label,
        objectives=_objectives_from(items),
        domain=slot.domain or (domains.pop() if len(domains) == 1 else None),
        items=tuple(item.key for item in items),
    )


class _Planner:
    """Walks the year once per rule, writing into one map of cell → fill."""

    def __init__(self, plan_input: PlanInput) -> None:
        self.input = plan_input
        self.problems: list[Problem] = []
        self.fills: dict[CellId, Fill] = {}
        self.alternations: Counter[str] = Counter()
        self.sequences_placed: Counter[str] = Counter()
        self.cells = self._build_cells()

    # ------------------------------------------------------------------ the grid

    def _build_cells(self) -> tuple[Cell, ...]:
        """Every séance the year owes, in the order it runs."""
        cells: list[Cell] = []
        for day in self.input.taught_days():
            for slot in self.input.slots_of(day.day_of_week):
                subject = self._resolve_subject(day, slot)
                cells.extend(
                    Cell(day=day, slot=slot, level=level, subject=subject)
                    for level in session_levels(slot)
                )
        return tuple(cells)

    def _resolve_subject(self, day: PlannedDay, slot: Slot) -> str | None:
        """Resolve the matière a créneau teaches, following its alternance where it has one."""
        if not slot.alternation_group:
            return slot.subject

        alternation = self.input.alternation(slot.alternation_group)
        if alternation is None:
            self._report(
                ProblemKind.ERREUR,
                f"aucun réglage pour l'alternance « {slot.alternation_group} » : "
                f"le créneau « {slot.label} » reste sans matière",
            )
            return None

        if alternation.mode == "hebdomadaire" and alternation.subjects:
            week = self.input.week(day.week_number)
            subject = alternation.subjects[(week.number - 1) % len(alternation.subjects)]
        else:
            match = next(
                (
                    candidate
                    for candidate in alternation.slots
                    if candidate.day_of_week == slot.day_of_week
                    and candidate.starts_at == slot.starts_at
                ),
                None,
            )
            if match is None:
                self._report(
                    ProblemKind.ERREUR,
                    f"l'alternance « {slot.alternation_group} » ne dit rien du créneau "
                    f"« {slot.label} » à {slot.starts_at:%H:%M}",
                )
                return None
            subject = match.subject

        self.alternations[subject] += 1
        return subject

    def _report(self, kind: ProblemKind, message: str) -> None:
        """Add one line to the rapport de validation."""
        self.problems.append(Problem(kind=kind, message=message))

    def _cells_where(self, keep: Callable[[Cell], bool]) -> tuple[Cell, ...]:
        """Keep the cells a predicate accepts, in the order they run."""
        return tuple(cell for cell in self.cells if keep(cell))

    def _free(self, cells: Sequence[Cell]) -> tuple[Cell, ...]:
        """Keep the cells no rule has filled yet."""
        return tuple(cell for cell in cells if cell.id not in self.fills)

    def _place(self, cell: Cell, fill: Fill) -> None:
        """Fill one cell."""
        self.fills[cell.id] = fill

    def _period_of(self, cell: Cell) -> str:
        """Return the période a cell falls in."""
        return self.input.week(cell.day.week_number).period_code

    # --------------------------------------------------------------- les séquences

    def plan_maths(self) -> None:
        """§4.3: one séquence per semaine, four séances on the week's maths créneaux (ADR-0011)."""
        weeks = sorted(self.input.weeks, key=lambda week: week.number)
        for level in (Level.CM1, Level.CM2):
            method = f"maths-{level.value.lower()}"
            sequences = self.input.sequences_of(method)
            if len(sequences) > len(weeks):
                self._report(
                    ProblemKind.ERREUR,
                    f"{method} : {len(sequences)} séquences pour {len(weeks)} semaines de classe",
                )
            for sequence, week in zip(sequences, weeks, strict=False):
                cells = tuple(
                    cell
                    for cell in self.cells
                    if cell.day.week_number == week.number
                    and cell.level == level
                    and is_maths_lesson(cell.slot)
                )
                for rank, cell in enumerate(cells[:MATHS_SESSIONS_PER_SEQUENCE], start=1):
                    self._place(
                        cell,
                        Fill(
                            title=(
                                f"Séquence {sequence.number} — {sequence.title} "
                                f"(séance {rank}/{MATHS_SESSIONS_PER_SEQUENCE})"
                            ),
                            objectives=sequence.objectives,
                            sequence=sequence.key,
                        ),
                    )
                if cells:
                    self.sequences_placed[method] += 1
                if len(cells) < MATHS_SESSIONS_PER_SEQUENCE:
                    self._report(
                        ProblemKind.CALENDRIER,
                        f"S{week.number} : {len(cells)} créneaux de mathématiques pour les "
                        f"{MATHS_SESSIONS_PER_SEQUENCE} séances de la séquence "
                        f"{sequence.number} « {sequence.title} » ({level.value})",
                    )

    def plan_retz(self) -> None:
        """§4.4: grammaire on the lundi créneau, conjugaison on the mardi one (ADR-0012)."""
        for level in (Level.CM1, Level.CM2):
            method = f"retz-{level.value.lower()}"
            by_domain = self._retz_by_domain(method)

            grammar = by_domain[GRAMMAIRE]
            landed = self._place_retz(method, grammar, self._retz_cells(GRAMMAIRE, level))

            opens_after = self._conjugaison_opens_after(method, grammar, landed)
            waiting = tuple(
                cell
                for cell in self._retz_cells(CONJUGAISON, level)
                if opens_after is None or cell.day.date > opens_after
            )
            self._place_retz(method, by_domain[CONJUGAISON], waiting)

    def _retz_by_domain(self, method: str) -> dict[str, tuple[MethodSequence, ...]]:
        """Split one RETZ progression into its grammaire and its conjugaison séquences."""
        found: dict[str, list[MethodSequence]] = {GRAMMAIRE: [], CONJUGAISON: []}
        for sequence in self.input.sequences_of(method):
            domain = sequence.domain or RETZ_CM2_DOMAINS.get(sequence.title)
            if domain in found:
                found[domain].append(sequence)
            else:
                self._report(
                    ProblemKind.ERREUR,
                    f"{method} : la séquence {sequence.number} « {sequence.title} » n'est "
                    f"classée ni en grammaire ni en conjugaison",
                )
        return {domain: tuple(sequences) for domain, sequences in found.items()}

    def _retz_cells(self, domain: str, level: Level) -> tuple[Cell, ...]:
        """Collect the year's créneaux of one étude de la langue domaine, for one niveau."""
        return self._cells_where(
            lambda cell: is_retz(cell.slot) and cell.slot.domain == domain and cell.level == level
        )

    def _place_retz(
        self, method: str, sequences: Sequence[MethodSequence], cells: Sequence[Cell]
    ) -> dict[str, date]:
        """Spread a RETZ progression over its créneaux, and say where each séquence ended."""
        ended: dict[str, date] = {}
        for sequence, share in zip(sequences, shares(len(sequences), len(cells)), strict=True):
            if not share:
                self._report(
                    ProblemKind.CALENDRIER,
                    f"{method} : la séquence {sequence.number} « {sequence.title} » n'a "
                    f"trouvé aucun créneau",
                )
                continue
            for rank, position in enumerate(share, start=1):
                cell = cells[position]
                title = f"Séquence {sequence.number} — {sequence.title}"
                if len(share) > 1:
                    title += f" (séance {rank}/{len(share)})"
                self._place(
                    cell,
                    Fill(
                        title=title,
                        objectives=sequence.objectives,
                        sequence=sequence.key,
                        domain=cell.slot.domain,
                    ),
                )
                ended[sequence.key] = cell.day.date
            self.sequences_placed[method] += 1
        return ended

    def _conjugaison_opens_after(
        self, method: str, grammar: Sequence[MethodSequence], ended: dict[str, date]
    ) -> date | None:
        """Return the last day of the grammaire séquence on « Le verbe ».

        §4.4 relays the RETZ advice not to start conjugaison before the notions of verbe
        and of sujet are done, and both progressions teach the groupe sujet before it.
        """
        verb = next(
            (sequence for sequence in grammar if sequence.title.startswith(VERB_SEQUENCE_PREFIX)),
            None,
        )
        if verb is None:
            self._report(
                ProblemKind.SOURCE,
                f"{method} : aucune séquence « {VERB_SEQUENCE_PREFIX}… » en grammaire, "
                f"la conjugaison démarre donc dès la première semaine",
            )
            return None
        return ended.get(verb.key)

    def plan_litterature(self) -> None:
        """§4.5: the œuvres, in order, one séance de séquence per œuvre-suivie créneau.

        The year is three créneaux short of the planning; what falls off is reported
        rather than squeezed in somewhere else (ADR-0017).
        """
        cells = self._cells_where(lambda cell: is_oeuvre_suivie(cell.slot))
        oeuvres = self.input.sequences_of(LITTERATURE)
        ordered = [oeuvre for oeuvre in oeuvres if oeuvre.title != LITTERATURE_FALLBACK]
        ordered += [oeuvre for oeuvre in oeuvres if oeuvre.title == LITTERATURE_FALLBACK]

        cursor = 0
        for oeuvre in ordered:
            if not oeuvre.steps:
                self._report(
                    ProblemKind.SOURCE,
                    f"littérature : « {oeuvre.title} » n'a aucun planning hebdomadaire dans "
                    f"la source et n'est donc pas placée",
                )
                continue
            period = FALLBACK_PERIOD if oeuvre.title == LITTERATURE_FALLBACK else oeuvre.period_code
            cursor = max(cursor, self._first_cell_of_period(cells, period))
            placed = 0
            for step in oeuvre.steps:
                if cursor >= len(cells):
                    self._report(
                        ProblemKind.CALENDRIER,
                        f"littérature : « {oeuvre.title} », {step.title.lower()} — plus aucun "
                        f"créneau « {OEUVRE_SUIVIE_LABEL} » dans l'année",
                    )
                    continue
                cell = cells[cursor]
                cursor += 1
                placed += 1
                self._place(
                    cell,
                    Fill(
                        title=f"{oeuvre.title} — {step.title}",
                        objectives=oeuvre.objectives,
                        content=step.content,
                        materials=step.materials,
                        sequence=oeuvre.key,
                        sequence_step=step.key,
                    ),
                )
            if placed:
                self.sequences_placed[LITTERATURE] += 1

    def _first_cell_of_period(self, cells: Sequence[Cell], period_code: str | None) -> int:
        """Return the index of the first créneau falling in a période."""
        if period_code is None:
            return 0
        for index, cell in enumerate(cells):
            if self._period_of(cell) == period_code:
                return index
        return len(cells)

    # -------------------------------------------------------------- les programmes

    def plan_themes(self) -> None:
        """Histoire and géographie place their thèmes by the périodes they name (ADR-0016)."""
        for subject in HISTORY_AND_GEOGRAPHY:
            for level in (Level.CM1, Level.CM2):
                themes = self.input.items_of(subject, None, level)
                if not themes:
                    continue
                periods = assign_periods(themes)
                cells = self._free(
                    tuple(
                        cell
                        for cell in self.cells
                        if cell.subject == subject and cell.level == level
                    )
                )
                for code in sorted({code for codes in periods.values() for code in codes}):
                    here = tuple(cell for cell in cells if self._period_of(cell) == code)
                    sharing = tuple(theme for theme in themes if code in periods[theme.key])
                    self._place_themes(subject, sharing, here, code)

    def _place_themes(
        self,
        subject: str,
        themes: Sequence[ProgramItem],
        cells: Sequence[Cell],
        period_code: str,
    ) -> None:
        """Share one période's créneaux between the thèmes that claim it."""
        if not cells:
            self._report(
                ProblemKind.CALENDRIER,
                f"{subject} : aucun créneau en {period_code} pour les {len(themes)} thème(s) "
                f"qui s'y rattachent",
            )
            return
        for cell, owning in zip(cells, spread(themes, len(cells)), strict=True):
            if owning:
                self._place(cell, _fill_from_items(cell.slot, owning))

    def plan_maths_revision_weeks(self) -> None:
        """Fill the maths créneaux no séquence reached — the marge §4.2 leaves at the end."""
        for cell in self._free(self._cells_where(lambda cell: is_maths_lesson(cell.slot))):
            items = self.input.items_of(MATHS, cell.slot.domain, cell.level)
            fill = _fill_from_items(cell.slot, items)
            self._place(cell, replace(fill, title=cell.slot.label + REVISION_SUFFIX))

    def plan_rituals(self) -> None:
        """Fill each rituel, which repeats rather than progresses, with its whole programme.

        A rituel keeps its whole programme where a lesson walks through it (ADR-0015).
        """
        for cell in self._free(self._cells_where(lambda cell: cell.slot.is_ritual)):
            if cell.subject is None:
                self._place(cell, Fill(title=cell.slot.label))
                continue
            items = [
                item
                for level in self.input.levels_with_items(cell.subject, cell.slot.domain)
                for item in self.input.items_of(cell.subject, cell.slot.domain, level)
                if addresses(cell.level, level)
            ]
            self._place(cell, _fill_from_items(cell.slot, items))

    def plan_generic(self) -> None:
        """Everything else: a matière's programme spread over its year's créneaux (ADR-0015)."""
        groups: dict[tuple[str, str | None], list[Cell]] = defaultdict(list)
        for cell in self._free(self.cells):
            if cell.subject is None:
                self._place(cell, Fill(title=cell.slot.label))
            else:
                groups[cell.subject, cell.slot.domain].append(cell)

        chosen: dict[CellId, list[ProgramItem]] = defaultdict(list)
        for (subject, domain), cells in groups.items():
            for level in self.input.levels_with_items(subject, domain):
                items = self.input.items_of(subject, domain, level)
                reached = [cell for cell in cells if addresses(cell.level, level)]
                if not items or not reached:
                    continue
                for cell, owning in zip(reached, spread(items, len(reached)), strict=True):
                    chosen[cell.id].extend(owning)

        for cells in groups.values():
            for cell in cells:
                self._place(cell, _fill_from_items(cell.slot, chosen[cell.id]))

    def plan_poetry(self) -> None:
        """Add the poésie to the vendredi 12h00 créneau, which also carries the dictée bilan."""
        cells = self._cells_where(lambda cell: cell.slot.label == POETRY_SLOT_LABEL)
        poetry = next(
            (
                item
                for item in self.input.items_of(FRANCAIS, POETRY_DOMAIN, Level.COMMUN)
                if item.title == POETRY_ITEM_TITLE
            ),
            None,
        )
        if poetry is None:
            if cells:
                self._report(
                    ProblemKind.SOURCE,
                    f"poésie : « {POETRY_ITEM_TITLE} » est absent du programme, le créneau "
                    f"« {POETRY_SLOT_LABEL} » ne porte que la dictée bilan",
                )
            return
        for cell in cells:
            fill = self.fills.get(cell.id)
            if fill is None:
                self._report(
                    ProblemKind.ERREUR,
                    f"{cell.day.date:%d/%m/%Y} : le créneau « {POETRY_SLOT_LABEL} » n'a pas "
                    f"été rempli, la poésie n'y a pas été rattachée",
                )
                continue
            self.fills[cell.id] = replace(
                fill,
                title=cell.slot.label,
                objectives="\n".join(filter(None, (fill.objectives, poetry.title))),
                items=(*fill.items, poetry.key),
            )

    # --------------------------------------------------------------------- output

    def report_uncovered(self) -> None:
        """Check the promise: every créneau of every taught day carries a séance."""
        for cell in self.cells:
            if cell.id not in self.fills:
                self._report(
                    ProblemKind.ERREUR,
                    f"{cell.day.date:%d/%m/%Y} : le créneau « {cell.slot.label} » "
                    f"({cell.level.value}) est resté sans séance",
                )

    def drafts(self) -> tuple[SessionDraft, ...]:
        """Return every séance, ordered by day and by its place in the day."""
        drafts: list[SessionDraft] = []
        by_day: dict[date, list[Cell]] = defaultdict(list)
        for cell in self.cells:
            by_day[cell.day.date].append(cell)

        for day in sorted(by_day):
            ordered = sorted(
                by_day[day], key=lambda cell: (cell.slot.starts_at, LEVEL_ORDER[cell.level])
            )
            for position, cell in enumerate(ordered, start=1):
                fill = self.fills.get(cell.id)
                if fill is None:
                    continue
                drafts.append(
                    SessionDraft(
                        date=cell.day.date,
                        slot=cell.slot.key,
                        level=cell.level,
                        title=fill.title,
                        objectives=fill.objectives,
                        content=fill.content,
                        materials=fill.materials,
                        subject=cell.subject,
                        domain=fill.domain or cell.slot.domain,
                        sequence=fill.sequence,
                        sequence_step=fill.sequence_step,
                        program_items=fill.items,
                        position=position,
                    )
                )
        return tuple(drafts)


def plan_year(plan_input: PlanInput) -> Plan:
    """Build the whole year's séances, in order, with everything that did not fit."""
    planner = _Planner(plan_input)
    planner.plan_maths()
    planner.plan_retz()
    planner.plan_litterature()
    planner.plan_themes()
    planner.plan_maths_revision_weeks()
    planner.plan_rituals()
    planner.plan_generic()
    # A second pass over créneaux the rules above have already filled.
    planner.plan_poetry()
    planner.report_uncovered()

    return Plan(
        sessions=planner.drafts(),
        problems=tuple(planner.problems),
        sequences_placed=dict(planner.sequences_placed),
        alternations=dict(planner.alternations),
    )
