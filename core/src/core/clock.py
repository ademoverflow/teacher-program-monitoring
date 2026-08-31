"""Today, as a dependency.

Half the API is positional — the semaine courante, the next jour de classe, whether a
période is already under way — and all of it turns on which day it is. Reading the date
through a dependency rather than calling ``date.today()`` in a handler lets a test stand
anywhere in the 2026-2027 year without a query parameter that the webapp would never send.
"""

from datetime import date


def today() -> date:
    """Return the day the API is answering on."""
    return date.today()  # noqa: DTZ011 - a local, single-timezone application
