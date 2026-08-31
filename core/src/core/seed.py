"""Entry point for ``make seed``: load the versioned JSON seeds, then plan the year.

The seeds and the programmation are loaded by the same command so a database rebuilt
from scratch (``make down && make up && make seed``) comes back usable. Both are
idempotent, and the generation never touches a jour de classe that is past or that
already has a cahier journal.
"""

import asyncio
import logging
import time
from datetime import date

from core.generate import render
from core.services.programmation.writer import generate
from core.services.seeding import seed


async def main() -> None:
    """Load the seeds and generate the year, on one event loop and one engine."""
    counts = await seed()
    for table, count in counts.items():
        print(f"{count:>5}  {table}")  # noqa: T201

    started = time.perf_counter()
    report = await generate(date.today())  # noqa: DTZ011
    print(render(report, time.perf_counter() - started))  # noqa: T201


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
