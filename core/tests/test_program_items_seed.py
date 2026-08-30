"""The extracted curriculum is the one printed in docs/programme-cm1-cm2.pdf.

These tests read ``core/seed/program_items.json`` and never touch the database, so CI
— which has no Postgres — checks the counts and the spot-checks for real.
"""

from collections import Counter

import pytest
from core.models.level import Level
from core.services.seed_files import load_program_items, load_subjects

ITEMS = load_program_items()
SUBJECTS = load_subjects()

SOURCE_FILE = "docs/programme-cm1-cm2.pdf"
SOURCE_PAGES = 154
TOTAL_ITEMS = 213

# The breakdown §8 asks the phase report to state, asserted here so it cannot drift.
ITEMS_PER_SUBJECT_AND_LEVEL = {
    ("anglais", Level.CM1): 22,
    ("anglais", Level.CM2): 22,
    ("arts-plastiques", Level.COMMUN): 4,
    ("education-musicale", Level.COMMUN): 4,
    ("emc", Level.CM1): 3,
    ("emc", Level.CM2): 4,
    ("eps", Level.COMMUN): 15,
    ("evar", Level.CM1): 3,
    ("evar", Level.CM2): 3,
    ("francais", Level.CM1): 24,
    ("francais", Level.CM2): 25,
    ("francais", Level.COMMUN): 6,
    ("geographie", Level.CM1): 4,
    ("geographie", Level.CM2): 3,
    ("histoire", Level.CM1): 4,
    ("histoire", Level.CM2): 6,
    ("mathematiques", Level.CM1): 21,
    ("mathematiques", Level.CM2): 18,
    ("sciences-et-technologie", Level.CM1): 12,
    ("sciences-et-technologie", Level.CM2): 10,
}

# §8 Phase 2: « zéro contenu inventé (spot-check de 10 items contre les PDFs) ».
# Each row is (niveau, matière, titre, page, one line the PDF prints in that block).
SPOT_CHECKS = (
    (
        Level.CM1,
        "francais",
        "Lire avec fluidité",
        8,
        "Lire correctement en ciblant 110 mots par minute en moyenne",
    ),
    (
        Level.COMMUN,
        "francais",
        "Découvrir des héroïnes, des héros",
        10,
        "Inviter les élèves à réfléchir sur ce qui constitue une héroïne ou un héros",
    ),
    (
        Level.CM1,
        "mathematiques",
        "Les quatre opérations",
        32,
        "Poser et effectuer des divisions euclidiennes avec un diviseur à un chiffre",
    ),
    (
        Level.CM1,
        "mathematiques",
        "Les longueurs",
        42,
        "Déterminer le périmètre d’un polygone en utilisant une règle graduée",
    ),
    (
        Level.CM1,
        "anglais",
        "Suivre le fil d’une histoire simple (CO-CM1)",
        57,
        "Repérer les lettres de l’alphabet et les chiffres pour réaliser une tâche.",
    ),
    (
        Level.COMMUN,
        "eps",
        "Se déplacer pour lancer le plus loin possible",
        86,
        "Construire une course d’élan réduite pour lancer loin différents objets.",
    ),
    (
        Level.CM1,
        "sciences-et-technologie",
        "Différents types de mouvement",
        93,
        "Mesurer une durée, comme intervalle entre deux instants, lors du déplacement",
    ),
    (
        Level.CM1,
        "geographie",
        "Thème 3 : Se déplacer (1 période)",
        119,
        "Question : Comment se déplace-t-on dans le monde ?",
    ),
    (
        Level.CM1,
        "emc",
        "Civisme et citoyenneté",
        80,
        "apprendre la signification du terme « démocratie » et le fonctionnement du suffrage",
    ),
    (
        Level.CM1,
        "evar",
        "Se connaître, vivre et grandir avec son corps",
        137,
        "Objectif d'apprentissage : Connaître les changements de son corps.",
    ),
    (
        Level.COMMUN,
        "education-musicale",
        "Chanter et interpréter",
        147,
        "Interpréter un répertoire varié avec expressivité.",
    ),
)


def test_the_curriculum_holds_every_extracted_item() -> None:
    """The count comes out of the PDF; it is recorded here so a re-run cannot drift."""
    assert len(ITEMS) == TOTAL_ITEMS


def test_items_are_spread_over_the_matieres_as_the_source_spreads_them() -> None:
    """§8 Phase 2 asks the report for the répartition par niveau/matière."""
    assert Counter((item.subject, item.level) for item in ITEMS) == ITEMS_PER_SUBJECT_AND_LEVEL


def test_no_item_belongs_to_a_class_outside_the_cours_moyen() -> None:
    """The source is a cycle-3 programme: its Sixième blocks are not ours."""
    assert {item.level for item in ITEMS} == {Level.CM1, Level.CM2, Level.COMMUN}


def test_items_are_unique_on_their_natural_key() -> None:
    """(niveau, matière, domaine, intitulé) is what ``make seed`` upserts on."""
    keys = [(item.level, item.subject, item.domain, item.title) for item in ITEMS]

    assert len(set(keys)) == len(keys)


def test_every_item_names_a_matiere_and_a_domaine_the_seeds_know() -> None:
    """A dangling code would become a silent NULL — or a KeyError — at seed time."""
    known = {(subject.code, domain.code) for subject in SUBJECTS for domain in subject.domains}
    subjects = {subject.code for subject in SUBJECTS}

    assert {item.subject for item in ITEMS} <= subjects
    assert {(item.subject, item.domain) for item in ITEMS if item.domain} <= known


def test_every_item_is_traceable_back_to_its_page() -> None:
    """§5: « référence source (fichier + page) »."""
    assert {item.source_file for item in ITEMS} == {SOURCE_FILE}
    assert all(item.source_page and 1 <= item.source_page <= SOURCE_PAGES for item in ITEMS)


def test_every_item_carries_the_text_it_was_extracted_for() -> None:
    """An item with no description would index nothing for the full-text search."""
    assert all(item.title.strip() and (item.description or "").strip() for item in ITEMS)


@pytest.mark.parametrize(("level", "subject", "title", "page", "line"), SPOT_CHECKS)
def test_an_item_says_what_the_pdf_says(
    level: Level, subject: str, title: str, page: int, line: str
) -> None:
    """Spot-check against the source: the text is the PDF's, on the PDF's page."""
    matches = [
        item
        for item in ITEMS
        if item.level is level and item.subject == subject and item.title == title
    ]

    assert len(matches) == 1
    assert matches[0].source_page == page
    assert line in (matches[0].description or "")
