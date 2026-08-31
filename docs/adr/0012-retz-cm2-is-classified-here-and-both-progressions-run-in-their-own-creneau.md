# RETZ CM2 is classified here, and each progression runs in its own créneau

The EDT teaches grammaire on Monday and conjugaison on Tuesday, in two separate
créneaux, so every RETZ séquence has to be one or the other. The CM1 progression says
which — it prints a colour legend, and Phase 2 copied it into `sequences.domain_id`
(ADR-0006). The CM2 progression is a sommaire with no legend, so the classification is
made in `core/services/planning/retz.py` and is a Phase 3 decision.

Fifteen of the twenty-one CM2 séquences print a notion the CM1 progression also prints,
and take the domaine CM1's colours give it — that half is read off the source, and the
table names the CM1 séquence beside each one. Six notions CM2 introduces on its own are
ours: L'attribut du sujet, Les pronoms de reprise, Les phrases complexes, Le
plus-que-parfait, L'impératif and La proposition subordonnée relative. The result is
14 grammaire and 7 conjugaison, the same shape as CM1.

The two progressions then run independently, each spread evenly over the year's
occurrences of its own créneau: 14 séquences over 33 lundis, 7 over the mardis that are
left once conjugaison opens. §4.4 relays a RETZ advice — « ne démarrer l'étude
systématique de la conjugaison qu'après les notions de verbe et de sujet » — and the
generator honours it by keeping conjugaison shut until the grammaire séquence « Le
verbe… » has finished; the mardi créneaux before that work the programme de conjugaison
instead of a séquence.

The obvious alternative was to run the twenty-one séquences as one list across both
créneaux, two séances a week, which is the only reading that matches §4.4's « ≈ 1
séquence toutes les 1,5 à 2 semaines ». It would have put conjugaison séquences in the
lundi grammaire cell. §4.1 settles it: « les horaires et durées de l'EDT font foi, y
compris quand une méthodo indique d'autres durées ». The EDT gives grammaire one créneau
a week and conjugaison one, and the pacing follows from that — a conjugaison séquence
runs about four weeks rather than two.
