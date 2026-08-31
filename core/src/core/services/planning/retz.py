"""Which RETZ séquences are grammaire and which are conjugaison.

The EDT teaches grammaire on Monday and conjugaison on Tuesday, in two different
créneaux, so every RETZ séquence has to be one or the other. The CM1 progression says
which: it prints a colour legend, and Phase 2 copied it into ``sequences.domain_id``
(ADR-0006). The CM2 progression is a sommaire with neither colours nor objectives, so
its classification is made here and is ours, not the source's (ADR-0012).
"""

GRAMMAIRE = "grammaire"
CONJUGAISON = "conjugaison"

# Every CM2 séquence, in the order of the sommaire. A séquence that prints the same
# notion as a CM1 séquence takes the domaine the CM1 colour legend gives it — that half
# of the table is read off the source. The six marked « nôtre » are notions CM2
# introduces on its own, and nothing in the PDF classifies them.
RETZ_CM2_DOMAINS: dict[str, str] = {
    "Les groupes dans la phrase": GRAMMAIRE,  # CM1 1
    "Le groupe sujet": GRAMMAIRE,  # CM1 2
    "Le verbe (formes conjuguées, infinitif, variations)": GRAMMAIRE,  # CM1 4
    "Le présent": CONJUGAISON,  # CM1 5 et 6, « Le présent des verbes… »
    "Les constituants du groupe nominal (GN) simple": GRAMMAIRE,  # CM1 8
    "Le passé composé": CONJUGAISON,  # CM1 9 et 10, « Le passé composé avec… »
    "L'adjectif qualificatif épithète": GRAMMAIRE,  # CM1 12
    "Le complément circonstanciel": GRAMMAIRE,  # CM1 13
    "L'imparfait": CONJUGAISON,  # CM1 14
    "Le complément d'objet": GRAMMAIRE,  # CM1 15
    "Le futur": CONJUGAISON,  # CM1 17
    "Le complément du nom": GRAMMAIRE,  # CM1 20
    "Les phrases injonctives": GRAMMAIRE,  # CM1 18, « Les phrases impératives »
    "L'attribut du sujet": GRAMMAIRE,  # nôtre
    "Le passé simple": CONJUGAISON,  # CM1 21, « Le passé simple des verbes… »
    "Les pronoms de reprise": GRAMMAIRE,  # nôtre
    "Les phrases complexes": GRAMMAIRE,  # nôtre
    "Le plus-que-parfait": CONJUGAISON,  # nôtre
    "Le groupe nominal (GN) enrichi": GRAMMAIRE,  # CM1 8, « Les constituants du GN simple »
    "L'impératif (bonus)": CONJUGAISON,  # nôtre
    "La proposition subordonnée relative (bonus)": GRAMMAIRE,  # nôtre
}

# §4.4 relays the RETZ advice: « ne démarrer l'étude systématique de la conjugaison
# qu'après les notions de verbe et de sujet ». Both progressions call that séquence
# « Le verbe … », and both teach the groupe sujet before it.
VERB_SEQUENCE_PREFIX = "Le verbe"
