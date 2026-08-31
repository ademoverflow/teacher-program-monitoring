"""How an alternance decides which matière one of its créneaux teaches.

Six créneaux of the timetable name a pair rather than a matière (ADR-0002); a réglage in
``app_settings`` resolves them (ADR-0013), and this is the vocabulary that réglage is
written in. It lives beside ``Level`` and ``SessionStatus`` because it is a domain
enumeration like they are — the seed validates against it and the generator reads it, so
spelling it once is what keeps the two from drifting.
"""

from enum import StrEnum


class AlternationMode(StrEnum):
    """The two ways §4.1 asks for an alternance to be resolved.

    ``hebdomadaire`` rotates through the matières semaine by semaine — « Histoire ou
    Géographie ». ``par-creneau`` fixes a matière on each créneau of the group for the
    whole year — « un créneau arts plastiques + un créneau éducation musicale par
    semaine ».
    """

    WEEKLY = "hebdomadaire"
    PER_SLOT = "par-creneau"
