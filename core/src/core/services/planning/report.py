"""Write the rapport de validation §8 Phase 3 asks for, in French.

The wording lives beside the generation rather than in ``core/generate.py`` so that both
entry points — ``make seed`` and ``make generate`` — read the same one, and so an entry
point stays what it is: a few lines that call a service.
"""

from core.services.planning.problems import ProblemKind
from core.services.planning.writer import GenerationReport

HEADINGS = {
    ProblemKind.ERREUR: "erreurs",
    ProblemKind.CALENDRIER: "ce que le calendrier ne permet pas",
    ProblemKind.SOURCE: "ce que la source ne dit pas",
}


def _counted(counts: dict[str, int]) -> str:
    """Write a mapping of counts on one line, in a stable order."""
    return ", ".join(f"{name} {count}" for name, count in sorted(counts.items()))


def render(report: GenerationReport, seconds: float) -> str:
    """Write the whole report for the terminal."""
    lines = [
        f"Programmation générée en {seconds:.1f}s — périodes {', '.join(report.periods)}",
        f"  {report.sessions_written} séances écrites sur {report.sessions_planned} planifiées "
        f"pour l'année, {report.days_written} jours de classe, {report.days_off} jours chômés",
        f"  {report.program_links} rattachements aux items de programme",
        "  séquences placées : " + _counted(report.sequences_placed),
        "  alternances : " + _counted(report.alternations),
    ]
    if report.days_untouched:
        lines.append(
            f"  {len(report.days_untouched)} jours laissés intacts "
            f"(passés ou déjà tenus au cahier journal)"
        )

    lines.append(
        "  rapport de validation : aucune erreur"
        if report.is_clean
        else f"  rapport de validation : {len(report.errors)} ERREURS"
    )
    for kind, heading in HEADINGS.items():
        of_kind = [problem for problem in report.problems if problem.kind is kind]
        if of_kind:
            lines.append(f"  {heading} ({len(of_kind)}) :")
            lines.extend(f"    - {problem}" for problem in of_kind)
    return "\n".join(lines)
