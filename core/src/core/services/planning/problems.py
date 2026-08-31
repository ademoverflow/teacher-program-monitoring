"""What the generator could not do, and whose fault it is.

§8 Phase 3 asks for a « rapport de validation sans erreur », and the year always has
something to report: S1 has no lundi, four jours are chômés, and the littérature planning
is three créneaux longer than the year. None of those is an error — they are the calendar,
and §10 says an impossibility is signalled rather than worked around. Separating them from
the things that would really be wrong is what makes « sans erreur » something the code can
check rather than a sentence to read.
"""

from dataclasses import dataclass
from enum import StrEnum


class ProblemKind(StrEnum):
    """Why a placement did not happen."""

    CALENDRIER = "calendrier"
    """The year does not afford it — a jour chômé, a semaine without its lundi."""

    SOURCE = "source"
    """The source has nothing to place — an œuvre with no planning hebdomadaire."""

    ERREUR = "erreur"
    """The generator could not do something it should have. This is the one that counts."""


@dataclass(frozen=True, slots=True)
class Problem:
    """One line of the rapport de validation."""

    kind: ProblemKind
    message: str

    def __str__(self) -> str:
        """Render the line the way the terminal and the UI print it."""
        return self.message
