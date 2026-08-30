"""Where each programme lives in ``docs/programme-cm1-cm2.pdf``, and how it maps to our domaines.

This is the reviewable part of the extraction: the page ranges below say which
matière a page belongs to, and the heading tables say which domaine a section of a
programme becomes. Everything else (`extract_program_items.py`) is mechanical.

The document is a cycle-3 programme, so it also covers Sixième — those blocks are
dropped. The domaine codes reuse the thirteen Phase 1 seeded in ``subjects.json``
wherever a programme's own cut matches one, and add new ones where it does not.
"""

from typing import NamedTuple

SOURCE_FILE = "docs/programme-cm1-cm2.pdf"


class Section(NamedTuple):
    """A heading of the source that opens a domaine.

    ``code``/``label`` are the domaine it opens. A section is *coarse* when it is one
    of the programme's own top-level parts: a niveau marker (« Cours moyen deuxième
    année ») restarts the reading inside the last coarse section, so a finer heading
    that changed the domaine — « Acquérir l'orthographe grammaticale » — stops
    applying at the niveau boundary rather than leaking into the next niveau.
    """

    heading: str
    code: str
    label: str
    coarse: bool = True


class Programme(NamedTuple):
    """One matière's programme: the pages it occupies and the sections inside it."""

    subject: str
    first_page: int
    last_page: int
    sections: tuple[Section, ...]
    # Headings whose item is the prose under them rather than an « Objectifs
    # d'apprentissage » list: the culture littéraire entrées are written that way.
    paragraph_titles: tuple[str, ...] = ()
    # Same, but for programmes whose headings follow a shape instead of being listed:
    # every langues-vivantes heading ends in its activité langagière and its niveau,
    # « Suivre le fil d'une histoire simple (CO-CM1) ».
    heading_pattern: str | None = None


# Français — the six sections of the sommaire (p. 5). « Grammaire et orthographe
# grammaticale » is one section in the source but three domaines for us: the EDT
# teaches grammaire, conjugaison and orthographe in their own créneaux, and the
# source's own third-level headings say which is which.
FRANCAIS = Programme(
    subject="francais",
    first_page=6,
    last_page=25,
    sections=(
        Section("Lecture", "lecture", "Lecture"),
        Section(
            "Culture littéraire et artistique",
            "culture-litteraire-et-artistique",
            "Culture littéraire et artistique",
        ),
        Section("Écriture", "ecriture", "Écriture"),
        Section("Oral", "oral", "Oral"),
        Section("Vocabulaire", "vocabulaire", "Vocabulaire"),
        Section("Grammaire et orthographe grammaticale", "grammaire", "Grammaire"),
        Section("Acquérir l’orthographe grammaticale", "orthographe", "Orthographe", coarse=False),
        Section(
            "Approfondir sa maîtrise de la conjugaison", "conjugaison", "Conjugaison", coarse=False
        ),
    ),
    paragraph_titles=(
        "Découvrir des héroïnes, des héros",
        "Se confronter au merveilleux, à l’étrange",
        "Imaginer et vivre d’autres vies",
        "Comprendre et interroger la morale",
        "Savourer le goût des mots, imaginer et créer en poésie",
        "Se découvrir, s’affirmer dans le rapport aux autres",
    ),
)

MATHEMATIQUES = Programme(
    subject="mathematiques",
    first_page=28,
    last_page=53,
    sections=(
        Section("Nombres, calcul et résolution de problèmes", "nombres", "Nombres"),
        Section("Les nombres entiers", "nombres", "Nombres", coarse=False),
        Section("Les fractions", "nombres", "Nombres", coarse=False),
        Section("Les nombres décimaux", "nombres", "Nombres", coarse=False),
        Section("Le calcul mental", "calcul-mental", "Calcul mental", coarse=False),
        Section("Les quatre opérations", "calculs", "Calculs", coarse=False),
        Section(
            "La résolution de problèmes",
            "resolution-de-problemes",
            "Résolution de problèmes",
            coarse=False,
        ),
        Section("Algèbre", "algebre", "Algèbre", coarse=False),
        Section("Grandeurs et mesures", "grandeurs-et-mesures", "Grandeurs et mesures"),
        Section("Les longueurs", "grandeurs-et-mesures", "Grandeurs et mesures", coarse=False),
        Section("Les masses", "grandeurs-et-mesures", "Grandeurs et mesures", coarse=False),
        Section("Les contenances", "grandeurs-et-mesures", "Grandeurs et mesures", coarse=False),
        Section("Les aires", "grandeurs-et-mesures", "Grandeurs et mesures", coarse=False),
        Section("Les angles", "grandeurs-et-mesures", "Grandeurs et mesures", coarse=False),
        Section(
            "Le repérage dans le temps et les durées",
            "grandeurs-et-mesures",
            "Grandeurs et mesures",
            coarse=False,
        ),
        Section("Espace et géométrie", "geometrie", "Géométrie"),
        Section("La géométrie plane", "geometrie", "Géométrie", coarse=False),
        Section("Les solides", "geometrie", "Géométrie", coarse=False),
        Section("Le repérage dans l’espace", "geometrie", "Géométrie", coarse=False),
        Section("Déplacements dans l’espace", "geometrie", "Géométrie", coarse=False),
        Section(
            "Organisation et gestion de données et probabilités",
            "organisation-et-gestion-de-donnees-et-probabilites",
            "Organisation et gestion de données et probabilités",
        ),
        Section(
            "Organisation et gestion de données",
            "organisation-et-gestion-de-donnees-et-probabilites",
            "Organisation et gestion de données et probabilités",
            coarse=False,
        ),
        Section(
            "Les probabilités",
            "organisation-et-gestion-de-donnees-et-probabilites",
            "Organisation et gestion de données et probabilités",
            coarse=False,
        ),
        Section("La proportionnalité", "proportionnalite", "Proportionnalité"),
        Section(
            "Initiation à la pensée informatique",
            "initiation-a-la-pensee-informatique",
            "Initiation à la pensée informatique",
        ),
    ),
)

# Langues vivantes — the five activités langagières plus la médiation (sommaire p. 54).
ANGLAIS = Programme(
    subject="anglais",
    first_page=55,
    last_page=73,
    sections=(
        Section(
            "Compréhension de l’oral : écouter et comprendre",
            "comprehension-de-l-oral",
            "Compréhension de l’oral",
        ),
        Section(
            "Expression orale en continu : parler en continu",
            "expression-orale-en-continu",
            "Expression orale en continu",
        ),
        Section(
            "Expression orale en interaction : réagir et dialoguer",
            "expression-orale-en-interaction",
            "Expression orale en interaction",
        ),
        Section(
            "Compréhension de l’écrit : lire et comprendre",
            "comprehension-de-l-ecrit",
            "Compréhension de l’écrit",
        ),
        Section(
            "Expression écrite : écrire et réagir à l’écrit",
            "expression-ecrite",
            "Expression écrite",
        ),
        Section("Médiation", "mediation", "Médiation"),
    ),
    heading_pattern=r"\((?:CO|EOC|EOI|CE|EE|M)-(CM1|CM2)\)$",
)

EPS = Programme(
    subject="eps",
    first_page=85,
    last_page=89,
    sections=(
        Section(
            "Se déplacer pour agir dans l’espace et sur une durée",
            "se-deplacer-pour-agir-dans-l-espace-et-sur-une-duree",
            "Se déplacer pour agir dans l’espace et sur une durée",
        ),
        Section(
            "Construire des équilibres pour s’adapter à des environnements inhabituels",
            "construire-des-equilibres",
            "Construire des équilibres pour s’adapter à des environnements inhabituels",
        ),
        Section(
            "S'exprimer avec son corps, pour éprouver et partager des émotions",
            "s-exprimer-avec-son-corps",
            "S'exprimer avec son corps, pour éprouver et partager des émotions",
        ),
        Section(
            "Coopérer et s’opposer pour apprendre à jouer en respectant les règles et les autres",
            "cooperer-et-s-opposer",
            "Coopérer et s’opposer pour apprendre à jouer en respectant les règles et les autres",
        ),
    ),
)

PROGRAMMES = (FRANCAIS, MATHEMATIQUES, ANGLAIS, EPS)

# Level markers, matched on a whole line. Everything from Sixième up is dropped, and
# so is everything below the cours moyen: this is a CM1/CM2 database.
LEVEL_MARKERS = {
    "Cours moyen première année": "CM1",
    "➜ Cours moyen première année": "CM1",
    "Cours moyen deuxième année": "CM2",
    "➜ Cours moyen deuxième année": "CM2",
    "Cours moyen première et deuxième années": "commun",
    "Cours moyen": "commun",
    "Au cours moyen": "commun",
}

OTHER_LEVEL_MARKERS = frozenset(
    {
        "Sixième",
        "Cinquième",
        "Quatrième",
        "Troisième",
        "Seconde",
        "Première",
        "Terminale",
        "CAP",
        "COLLÈGE",
        "École élémentaire",
        "Cours préparatoire",
        "➜ Cours préparatoire",
        "Cours élémentaire première année",
        "➜ Cours élémentaire première année",
        "Cours élémentaire deuxième année",
        "➜ Cours élémentaire deuxième année",
    }
)


class TableProgramme(NamedTuple):
    """A programme printed as multi-column tables rather than prose.

    ``columns`` names the columns in the order the source prints them; they are
    recovered from the blank gutters ``pdftotext -layout`` preserves and written back
    into the description under those names. ``sections`` are the headings that open an
    item; a heading the source wrapped over two lines is written here in full and
    matched against the two lines joined.
    """

    subject: str
    first_page: int
    last_page: int
    columns: tuple[str, ...]
    sections: tuple[str, ...] = ()
    domain: str | None = None
    domain_label: str | None = None
    # A section heading becomes the domaine when the programme has no domaine of its
    # own — EMC and EVAR cut their programme into notions, and those are the domaines.
    domain_from_section: bool = False
    level: str = "commun"
    # Lines that switch the niveau, and lines that close the reading (Sixième and up).
    levels: tuple[tuple[str, str], ...] = ()
    stops: tuple[str, ...] = ()
    # Lines kept as introductory text above the table rather than as table content.
    intro_prefixes: tuple[str, ...] = ()


# Histoire and géographie share a programme and a page range; the matière switches on
# its own heading. An item is a thème — the unit the source itself plans in, période
# by période.
HISTOIRE_GEOGRAPHIE = TableProgramme(
    subject="histoire",
    first_page=111,
    last_page=122,
    columns=("Objectifs d’apprentissage", "Attendus (connaissances et compétences)", "Repères"),
)

TABLES = (
    # EMC prints one table per notion of the niveau's programme.
    TableProgramme(
        subject="emc",
        first_page=80,
        last_page=83,
        columns=(
            "Notions abordées",
            "Contenus d’enseignement",
            "Démarches et situations d’apprentissage possibles",
        ),
        sections=(
            "Civisme et citoyenneté",
            "L’égalité dans la dignité",
            "Comment faire société",
            "Citoyenneté et nationalité",
            "Libertés et droits fondamentaux",
            "Respecter les droits de tous",
            "À l’école laïque",
        ),
        domain_from_section=True,
        levels=(("CM1 : Faire société", "CM1"), ("CM2 : Vivre en république", "CM2")),
        stops=("COLLÈGE", "Sixième : Apprendre à vivre dans une société démocratique"),
    ),
    # EVAR prints the same three axes at every niveau, each with its objectif.
    TableProgramme(
        subject="evar",
        first_page=137,
        last_page=140,
        columns=(
            "Notions et compétences",
            "Propositions de démarches et d’activités pour les séances "
            "ou temps d’enseignement spécifiques",
        ),
        sections=(
            "Se connaître, vivre et grandir avec son corps",
            "Rencontrer les autres et construire des relations, s’y épanouir",
            "Trouver sa place dans la société, y être libre et responsable",
        ),
        domain_from_section=True,
        levels=(
            ("➜ Cours moyen première année", "CM1"),
            ("➜ Cours moyen deuxième année", "CM2"),
        ),
        stops=("➜ Sixième", "➜ Cinquième", "Collège", "COLLÈGE"),
        intro_prefixes=("Objectif d'apprentissage :",),
    ),
    # The enseignements artistiques still follow the 2020 programmes: cycle-3 wide, no
    # CM1/CM2 split. Only their « Compétences travaillées » tables are read — see the
    # phase report for what is left out and why.
    TableProgramme(
        subject="arts-plastiques",
        first_page=141,
        last_page=142,
        columns=("Compétences travaillées", "Domaines du socle"),
        sections=(
            "Expérimenter, produire, créer",
            "Mettre en œuvre un projet artistique",
            "S’exprimer, analyser sa pratique, celle de ses pairs ; établir "
            "une relation avec celle des artistes, s’ouvrir à l’altérité",
            "Se repérer dans les domaines liés aux arts plastiques, être "
            "sensible aux questions de l’art",
        ),
        domain="competences-travaillees",
        domain_label="Compétences travaillées",
        stops=("Ces compétences sont développées",),
    ),
    TableProgramme(
        subject="arts-plastiques",
        first_page=143,
        last_page=146,
        columns=(
            "Questionnements",
            "Exemples de situations, d’activités et de ressources pour l’élève",
        ),
        sections=(
            "La représentation plastique et les dispositifs de présentation",
            "Les fabrications et la relation entre l’objet et l’espace",
            "La matérialité de la production plastique et la sensibilité aux constituants "
            "de l’œuvre",
        ),
        domain="questionnements",
        domain_label="Questionnements",
        stops=("Croisements entre enseignements",),
    ),
    TableProgramme(
        subject="education-musicale",
        first_page=147,
        last_page=147,
        columns=("Compétences travaillées", "Domaines du socle"),
        sections=(
            "Chanter et interpréter",
            "Écouter, comparer et commenter",
            "Explorer, imaginer et créer",
            "Échanger, partager et argumenter",
        ),
        domain="competences-travaillees",
        domain_label="Compétences travaillées",
    ),
    TableProgramme(
        subject="education-musicale",
        first_page=148,
        last_page=150,
        columns=(
            "Connaissances et compétences associées",
            "Exemples de situations, d’activités et de ressources pour l’élève",
        ),
        sections=(
            "Chanter et interpréter",
            "Écouter, comparer et commenter",
            "Explorer, imaginer et créer",
            "Échanger, partager et argumenter",
        ),
        domain="connaissances-et-competences-associees",
        domain_label="Connaissances et compétences associées",
        stops=("Repères de progressivité",),
    ),
)
