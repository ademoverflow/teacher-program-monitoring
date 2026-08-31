"""Entry point for ``make generate``: fill the year's séances from the database."""

import asyncio
import logging
import time
from datetime import date

from core.services.planning.report import render
from core.services.planning.writer import generate

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    started = time.perf_counter()
    outcome = asyncio.run(generate(date.today()))  # noqa: DTZ011
    print(render(outcome, time.perf_counter() - started))  # noqa: T201
