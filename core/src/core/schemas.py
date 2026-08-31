"""The shapes the API renders.

Every response body of the API is declared here, and none of them is a SQLModel row: the
tables carry a `tsvector` that does not serialise, timestamps the webapp has no use for,
and an extraction flag (`needs_review`) that is the seed's business rather than the
teacher's. §6 asks for dedicated Pydantic schemas, on the pattern of ``routers/health.py``
— which keeps its own, being the one endpoint that reads nothing.

The names are the domain's (`CONTEXT.md`) with English identifiers (§10): a `Session` here
is a séance, a `Slot` a créneau, a `JournalEntry` a ligne de cahier journal.
"""

import datetime
import uuid

from pydantic import BaseModel

from core.models.level import Level
from core.models.status import SessionStatus
from core.models.weekday import Weekday
from core.services.planning.problems import ProblemKind

# How much of a long list one page holds. The programmes are 220 items and a rituel links
# the same item on 139 days, so both of those lists are paged and both page the same way.
PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

# --------------------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------------------


class DomainRef(BaseModel):
    """A domaine, as it is named on a séance or in a filter."""

    id: uuid.UUID
    code: str
    label: str
    level: Level


class SubjectRef(BaseModel):
    """A matière, with the colour the grid draws it in."""

    id: uuid.UUID
    code: str
    label: str
    color: str


class SubjectWithDomains(SubjectRef):
    """A matière and the domaines under it — what the programme filters are built from."""

    domains: list[DomainRef]


class SlotSummary(BaseModel):
    """One créneau of the gabarit.

    ``duration_minutes`` is the teaching time the cell prints and is not always
    ``ends_at - starts_at``: the vendredi calcul mental sits in the grid's 9h55-10h15 row
    and lasts 15 minutes (ADR-0003). Use the boundaries to place a cell in the grid and
    the duration whenever you mean teaching time.
    """

    id: uuid.UUID
    day_of_week: Weekday
    starts_at: datetime.time
    ends_at: datetime.time
    duration_minutes: int
    label: str
    level: Level
    is_alternating: bool
    alternation_group: str | None
    subject: SubjectRef | None
    domain: DomainRef | None


class SequenceRef(BaseModel):
    """The séquence a séance comes from."""

    id: uuid.UUID
    method: str
    level: Level
    number: int
    title: str


class SequenceStepRef(BaseModel):
    """The séance de séquence a séance instantiates — the méthodo's own numbered step."""

    id: uuid.UUID
    number: int
    title: str


class ProgramItemRef(BaseModel):
    """An item de programme, as a séance names it."""

    id: uuid.UUID
    level: Level
    title: str
    subject: SubjectRef | None
    domain: DomainRef | None


class ProgramItemOut(ProgramItemRef):
    """An item de programme with everything the programme browser shows of it."""

    description: str | None
    source_file: str
    source_page: int | None
    source_order: int
    needs_review: bool


class ProgramItemPage(BaseModel):
    """One page of items de programme, and how many matched in all."""

    total: int
    limit: int
    offset: int
    items: list[ProgramItemOut]


# --------------------------------------------------------------------------------------
# The calendar
# --------------------------------------------------------------------------------------


class DayRef(BaseModel):
    """A jour de classe and where it sits in the year.

    A jour chômé keeps its row and its place in the semaine (ADR-0001): `is_off` and
    `off_reason` say why there is no class, which a missing day could not.
    """

    id: uuid.UUID
    date: datetime.date
    day_of_week: Weekday
    is_off: bool
    off_reason: str | None
    week_number: int
    number_in_period: int
    period_code: str


class WeekSummary(BaseModel):
    """A semaine as the year view lists it."""

    number: int
    number_in_period: int
    starts_on: datetime.date
    ends_on: datetime.date
    days_off: int


class PeriodRef(BaseModel):
    """A période, as a semaine or a jour names the one it belongs to."""

    id: uuid.UUID
    code: str
    label: str
    starts_on: datetime.date
    ends_on: datetime.date


class PeriodSummary(PeriodRef):
    """A période and its semaines, as the year view lists them."""

    weeks: list[WeekSummary]


class HolidayOut(BaseModel):
    """A stretch of vacances. ``ends_on`` is open for the summer."""

    label: str
    starts_on: datetime.date
    ends_on: datetime.date | None


class YearOverview(BaseModel):
    """The whole année scolaire in one response — §7 écran 1."""

    label: str
    zone: str
    starts_on: datetime.date
    ends_on: datetime.date
    today: datetime.date
    current_week_number: int | None
    periods: list[PeriodSummary]
    holidays: list[HolidayOut]


class TodayOut(BaseModel):
    """Where the teacher is in the year right now — « Aujourd'hui » is the home page (§7).

    ``school_day`` is today's jour de classe when today is one — **including a jour chômé**,
    which comes back with its motif so the page can say why there is no class rather than
    show nothing. ``next_taught_day`` is the jour de classe to open: today when today is
    taught, the next one otherwise, and null once the year is over.
    """

    date: datetime.date
    school_day: DayRef | None
    next_taught_day: DayRef | None


# --------------------------------------------------------------------------------------
# Séances
# --------------------------------------------------------------------------------------


class PlannedSessionSummary(BaseModel):
    """A séance as the semaine grid draws it."""

    id: uuid.UUID
    school_day_id: uuid.UUID
    date: datetime.date
    timetable_slot_id: uuid.UUID
    level: Level
    title: str
    status: SessionStatus
    position: int
    subject: SubjectRef | None
    domain: DomainRef | None
    sequence: SequenceRef | None


class PlannedSessionDetail(PlannedSessionSummary):
    """A séance with everything it says, for the jour view and the séance editor."""

    objectives: str | None
    content: str | None
    materials: str | None
    slot: SlotSummary
    sequence_session: SequenceStepRef | None
    program_items: list[ProgramItemRef]


class PlannedSessionPage(BaseModel):
    """One page of séances, and how many there are in all."""

    total: int
    limit: int
    offset: int
    sessions: list[PlannedSessionSummary]


class WeekCell(BaseModel):
    """One cell of the semaine grid: a créneau, and the 0, 1 or 2 séances planned in it.

    Two séances mean a commun créneau that a per-niveau méthodo splits (ADR-0010) — one
    CM1, one CM2. That is not the same thing as the times where the EDT itself has two
    créneaux side by side (mardi 11h30, jeudi 11h30, jeudi 15h00): those are two cells.
    None at all means a jour chômé, or a créneau the generation could not fill.
    """

    slot: SlotSummary
    sessions: list[PlannedSessionSummary]


class DayInWeek(BaseModel):
    """One jour of the semaine grid, with every créneau of its weekday."""

    id: uuid.UUID
    date: datetime.date
    day_of_week: Weekday
    is_off: bool
    off_reason: str | None
    cells: list[WeekCell]


class WeekDetail(BaseModel):
    """A semaine as §4.1 prints it: the jours in columns, the créneaux in rows.

    S1 has three jours rather than four — the year starts on a mardi — so a reader must
    take the jours from here rather than assume them.
    """

    number: int
    number_in_period: int
    starts_on: datetime.date
    ends_on: datetime.date
    period: PeriodRef
    previous_week_number: int | None
    next_week_number: int | None
    days: list[DayInWeek]


class DayDetail(BaseModel):
    """A jour de classe and its séances in the order they run."""

    id: uuid.UUID
    date: datetime.date
    day_of_week: Weekday
    is_off: bool
    off_reason: str | None
    week_number: int
    number_in_period: int
    period: PeriodRef
    previous_day: datetime.date | None
    next_day: datetime.date | None
    has_journal: bool
    sessions: list[PlannedSessionDetail]


# --------------------------------------------------------------------------------------
# The cahier journal
# --------------------------------------------------------------------------------------


class JournalEntryOut(BaseModel):
    """One ligne de cahier journal: a discipline and a durée, the objectifs, the bilan."""

    id: uuid.UUID
    school_day_id: uuid.UUID
    planned_session_id: uuid.UUID | None
    discipline: str
    duration_minutes: int | None
    objectives: str | None
    bilan: str | None
    notes: str | None
    position: int


class JournalDay(BaseModel):
    """A day's cahier journal.

    ``initialised`` says whether the day has one at all: a day whose cahier journal has
    never been created and one whose lignes have all been deleted are different states,
    and only the first may be filled from the séances (ADR-0021).
    """

    date: datetime.date
    week_number: int
    number_in_period: int
    period_code: str
    is_off: bool
    off_reason: str | None
    initialised: bool
    entries: list[JournalEntryOut]


# --------------------------------------------------------------------------------------
# The generation and the réglages
# --------------------------------------------------------------------------------------


class ProblemOut(BaseModel):
    """One line of the rapport de validation, with whose fault it is.

    ``erreur`` is the only kind that counts against « rapport de validation sans erreur »:
    `calendrier` is what the year does not afford and `source` what the méthodo does not
    say, and §10 has both reported rather than worked around.
    """

    kind: ProblemKind
    message: str


class GenerationReportOut(BaseModel):
    """What one run of the generation did, and everything it could not do."""

    periods: list[str]
    sessions_planned: int
    sessions_written: int
    days_written: int
    days_untouched: list[datetime.date]
    days_off: int
    program_links: int
    sequences_placed: dict[str, int]
    alternations: dict[str, int]
    problems: list[ProblemOut]
    error_count: int
    is_clean: bool
    seconds: float


class PeriodGenerationState(BaseModel):
    """Whether a période may be regenerated without asking first.

    ``is_started`` counts the jours a re-generation would refuse to touch — those in the
    past and those already held in a cahier journal (§10). §7 écran 5 asks for an explicit
    confirmation before overwriting such a période.
    """

    code: str
    label: str
    starts_on: datetime.date
    ends_on: datetime.date
    session_count: int
    protected_days: int
    is_started: bool


class GenerationStatus(BaseModel):
    """What a generation would find if it ran now."""

    reference_date: datetime.date
    session_count: int
    periods: list[PeriodGenerationState]


class SettingOut(BaseModel):
    """One réglage.

    ``requires_generation`` marks the ones the generation reads rather than the app: the
    alternances move nothing until the year is generated again (ADR-0013).
    """

    key: str
    label: str | None
    value: dict | list | str | int | float | bool | None
    requires_generation: bool
