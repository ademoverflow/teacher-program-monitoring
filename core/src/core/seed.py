"""Entry point for ``make seed``: load the versioned JSON seeds into the database."""

import asyncio
import logging

from core.services.seeding import seed

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    counts = asyncio.run(seed())
    for table, count in counts.items():
        print(f"{count:>5}  {table}")  # noqa: T201
