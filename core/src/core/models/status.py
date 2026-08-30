"""Statuses carried by a séance and by a révision IA.

The values are the domain's own words (MASTER-PROMPT.md §5) and are what is stored.
"""

from enum import StrEnum


class SessionStatus(StrEnum):
    """Where a séance stands on the day it was planned for."""

    PLANIFIEE = "planifiée"
    FAITE = "faite"
    REPORTEE = "reportée"
    ANNULEE = "annulée"


class RevisionStatus(StrEnum):
    """A révision IA is proposed, then applied or rejected — never applied on its own."""

    PROPOSEE = "proposée"
    APPLIQUEE = "appliquée"
    REJETEE = "rejetée"
