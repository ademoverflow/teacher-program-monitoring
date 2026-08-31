"""Entry point for ``make generate``: fill the year's séances from the database."""

import asyncio
import logging
import time
from datetime import date

from core.services.programmation.writer import GenerationReport, generate


def _counted(counts: dict[str, int]) -> str:
    """Write a mapping of counts on one line, in a stable order."""
    return ", ".join(f"{name} {count}" for name, count in sorted(counts.items()))


def render(report: GenerationReport, seconds: float) -> str:
    """Write the validation report §8 Phase 3 asks for, in French, for the terminal."""
    lines = [
        f"Programmation générée en {seconds:.1f}s — périodes {', '.join(report.periods)}",
        f"  {report.sessions_written} séances écrites sur {report.sessions_planned} planifiées, "
        f"{report.days_written} jours de classe, {report.days_off} jours chômés",
        f"  {report.program_links} rattachements aux items de programme",
        "  séquences placées : " + _counted(report.sequences_placed),
        "  alternances : " + _counted(report.alternations),
    ]
    if report.days_untouched:
        lines.append(
            f"  {len(report.days_untouched)} jours laissés intacts "
            f"(passés ou déjà tenus au cahier journal)"
        )
    if report.problems:
        lines.append(f"  {len(report.problems)} points signalés :")
        lines.extend(f"    - {problem}" for problem in report.problems)
    else:
        lines.append("  aucun point à signaler")
    return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    started = time.perf_counter()
    outcome = asyncio.run(generate(date.today()))  # noqa: DTZ011
    print(render(outcome, time.perf_counter() - started))  # noqa: T201
