Lis `MASTER-PROMPT.md` en entier, puis réalise la **Phase 3 — Génération de la programmation annuelle**.

## Où en est le dépôt

Les Phases 0, 1 et 2 sont terminées, vérifiées et mergées dans `main`. Crée `phase-3-generation` à partir de `main`.

Ne relitige pas les phases précédentes : `git log` et les ADR ont le détail.

**Lis d'abord `CONTEXT.md` (glossaire du domaine) et les huit `docs/adr/`.** C'est la convention du dépôt (`docs/agents/domain.md`) et ça t'évitera de réinventer du vocabulaire ou de « corriger » des choix délibérés. Les ADR 0001 à 0004 cadrent le calendrier et l'EDT, les 0005 à 0008 le contenu pédagogique.

## Ce que la Phase 2 a changé et que MASTER-PROMPT ne sait pas

- **`program_items` est rempli : 220 items**, sur les 12 matières. Répartition : francais 55, anglais 44, mathematiques 39, sciences-et-technologie 22, eps 15, histoire 10, education-musicale 8, arts-plastiques 7, emc 7, geographie 7, evar 6, **poesie 0**. Recherche plein-texte opérationnelle (`search_vector` généré, `websearch_to_tsquery('french', …)`).
- **`sequences` est rempli : 120 séquences** — `maths-cm1` 35, `maths-cm2` 35, `retz-cm1` 21, `retz-cm2` 21, `litterature` 8 — et **36 `sequence_sessions`**, qui sont toutes des semaines d'œuvres de littérature.
- **`domains` : 45** (les 13 de la Phase 1, jamais renommés, plus 32 tirés des programmes). **Histoire et géographie n'ont aucun domaine** : leur programme est découpé en thèmes, et chaque thème est un `program_item` dont l'intitulé porte sa période (« Thème 1 : La vie quotidienne au Moyen Âge (XIe - XIIIe siècles) (première et deuxième période) »). C'est ta source pour les placer.
- **`program_items` a une clé naturelle** `(level, subject_id, domain_id, title)`, en `NULLS NOT DISTINCT` (ADR-0005).
- **`sequences.domain_id` existe** (ajouté en Phase 2) et n'est rempli **que pour `retz-cm1`** : 14 grammaire, 7 conjugaison, d'après le code couleur imprimé par le PDF RETZ. ADR-0006 dit explicitement que pour tout le reste la méthodo ne nomme pas de domaine et que c'est à toi de décider — et de tracer ta décision comme la tienne.
- **`period_code`** est rempli pour `maths-cm1`, `maths-cm2` (la période du manuel) et `litterature` (P1…P5, §4.5). **RETZ n'en a pas** : la répartition sur l'année est ton travail (§4.4).
- **Aucune séquence de maths n'a de `sequence_sessions`.** La méthodo annonce « une suite de 4 séances » sans jamais les titrer ; les inventer est ce que §10 interdit. Une séquence maths n'a qu'un numéro, un titre et une période.
- **L'extraction du programme est un script versionné** (`scripts/extract_program_items.py`, `curriculum_map.py`, `curriculum_corrections.json`) et le seed est régénérable (ADR-0007). Tu n'as pas à y toucher, mais si un item te paraît faux, c'est là qu'on le corrige, pas dans le JSON.
- **Conventions de test** : les tests qui lisent les fichiers seed tournent en CI (qui n'a pas de Postgres) — c'est ce qui rend les comptes vérifiables. Ceux qui ont besoin de la base se `skip` via le fixture de `core/tests/test_seeding.py`. Privilégie la même séparation : la logique de placement doit être testable sans base.
- **`make seed` reste idempotent**, vérifié par empreinte depuis une base vide.
- Rappels toujours valables : tout nouveau modèle importé dans `core/src/core/models/__init__.py` ; migrations via `make db-migrate MSG="..."` stack allumée, jamais `alembic` en direct depuis l'hôte ; énumérations en texte contraint par CHECK (ADR-0004).

## À trancher avant de coder

1. **`planned_sessions` n'a AUCUNE contrainte d'unicité en dehors de sa clé primaire** — exactement le piège que la Phase 2 a rencontré sur `program_items`. Une génération relançable a besoin d'une clé naturelle (`(school_day_id, timetable_slot_id, level)` est le candidat évident) **avec migration Alembic**. Sans ça, relancer la génération duplique toute l'année.
2. **Un créneau `commun` qui porte du contenu par niveau : une séance, ou deux ?** Les 4 créneaux de maths, les ateliers problèmes et les 4 créneaux d'étude de la langue sont `commun` dans l'EDT, mais les méthodos sont par niveau (`maths-cm1` / `maths-cm2`, `retz-cm1` / `retz-cm2`). `planned_sessions.level` peut valoir `CM1` ou `CM2` même quand le créneau est `commun`. **Ce choix change le compte attendu** — tranche-le avant d'écrire le générateur, il est structurant.
3. **Comment remplir les 4 créneaux de maths depuis une séquence sans séances ?** L'EDT donne un domaine à chaque jour (lundi Nombres, mardi Calculs, jeudi Grandeurs et mesures, vendredi Géométrie) et la séquence de la semaine n'en couvre qu'un (« Fractions-1 », « Droites perpendiculaires »). Rattacher la séquence aux 4 créneaux, ou seulement à celui dont le domaine correspond ? Que mettre dans les autres ? Décide et écris-le, sans inventer de contenu.
4. **RETZ CM2 n'a pas de domaine.** À toi de dire quelles séquences vont sur le créneau grammaire (lundi) et lesquelles sur conjugaison (mardi), et de le tracer comme une décision de Phase 3, pas comme une lecture de la source.
5. **Les alternances ne sont pas paramétrées** : `app_settings` est vide. Deux groupes, six créneaux à `subject_id` NULL (ADR-0002) : `histoire-geographie` (CM1 mardi 14h15 et jeudi 15h00, CM2 mardi 11h30 et jeudi 11h30) et `arts-plastiques-education-musicale` (commun, lundi 15h45 et jeudi 14h15). Le §4.1 donne les défauts à valider ; ils doivent vivre dans `app_settings` et rester modifiables.
6. **Poésie.** Le créneau vendredi 12h00-12h30 « Dictée bilan / Poésie » est rattaché à `francais`/`orthographe` et ne porte pas de flag d'alternance (le §4.1 n'en liste que deux). La matière `poesie` existe et n'a **aucun** item de programme — elle n'a pas de programme propre, c'est une entrée de « Culture littéraire et artistique » en français. Point laissé ouvert par la Phase 1, à trancher ici.

## Pièges connus pour cette phase

- **L'EDT est immuable** (§10) : toute impossibilité de placement se signale dans le rapport, ne se contourne pas.
- **Les jours passés et les cahiers journaux ne sont jamais écrasés** par une régénération (§8). Aucune `journal_entry` n'existe encore, mais la règle doit être dans le code dès maintenant, pas ajoutée en Phase 6.
- **4 jours chômés** : lundi 29/03/2027, jeudi 06/05, vendredi 07/05, lundi 17/05. La ligne `school_days` existe avec `is_off` vrai (ADR-0001) — aucune séance dessus, mais la semaine doit rester lisible.
- **La S1 n'a pas de lundi** (rentrée élèves mardi 01/09/2026) : 35 lundis pour 36 semaines.
- **`ends_at - starts_at != duration_minutes`** pour le calcul mental du vendredi (ADR-0003) : utiliser `duration_minutes` quand on parle de temps d'enseignement, les bornes quand on parle de position dans la grille.
- **Génération < 1 min** : insertions en masse, pas un aller-retour par séance. Il y en a plus de 1500.
- **La CI n'a pas de Postgres** : la logique de placement doit être testable sans base.

## Repères de vérification (à recalculer, pas à croire sur parole)

- **143 `school_days`**, dont **139 non chômés**.
- **44 créneaux** : lundi 10, mardi 12, jeudi 12, vendredi 10.
- Jours travaillés par jour de semaine : **33 lundis, 36 mardis, 35 jeudis, 35 vendredis**.
- Soit **1532 couples (jour de classe, créneau)** à couvrir si une séance = un créneau. Si la décision 2 donne deux séances aux créneaux communs à contenu par niveau, le total monte — recalcule-le, ne le suppose pas.
- **35 séquences de maths × 2 niveaux** toutes placées, dans l'ordre, une par semaine de classe, sans trou (§4.3 : le rattachement à la période suit le calendrier réel, pas le découpage du manuel).
- **8 œuvres de littérature** placées sur le créneau lundi 11h30, Charlie sur 7 semaines de P1 depuis ses `sequence_sessions`.
- Semaines par période : **7/7/5/6/11**.
- Alternances équilibrées sur l'année, et chaque créneau de chaque jour non chômé couvert.

## Skills à appeler

- **`mattpocock-skills:to-tickets`** en premier si tu juges la phase trop grosse pour une session. Les tickets vont dans `.scratch/<feature-slug>/` (voir `docs/agents/issue-tracker.md`). Le squelette de la Phase 2 est dans `.scratch/phase-2-content/` si tu veux voir la forme attendue.
- **`mattpocock-skills:tdd`** pour les comptes ci-dessus et pour les règles de placement : elles s'écrivent en rouge d'abord, sur des données en mémoire, donc sans base, donc vérifiables en CI.
- **`/migrate`** pour la clé naturelle de `planned_sessions`, **`/check`** et **`/test`** pour la boucle qualité.
- **`mattpocock-skills:diagnosing-bugs`** dès qu'un placement ne tombe pas juste — le calendrier et l'EDT sont exactement le terrain où deviner coûte cher.
- **`mattpocock-skills:domain-modeling`** si la génération fait émerger du vocabulaire absent de `CONTEXT.md` (rituel, atelier, alternance résolue…) — mets-le à jour au fil de l'eau, et écris un ADR pour chacune des six décisions ci-dessus que tu tranches.
- **`mattpocock-skills:code-review`** en fin de phase, avant le commit final (§9).

## Fini quand

Critères du §8 Phase 3 : génération complète en moins d'une minute, rapport de validation sans erreur, échantillon manuel (P1-S1 complet + une semaine de P3) conforme à l'EDT et aux méthodos. Plus les règles communes : `make check` vert, `make test` vert, `make seed` toujours idempotent depuis une base vide (`docker compose down -v && make up && make seed`), commits conventionnels, et un court rapport (fait / non fait / ambiguïtés).

Ne déborde pas sur la Phase 4 : aucun router, aucun endpoint. La Phase 3 remplit la base, elle ne l'expose pas.

## Points ouverts hérités de la Phase 2 (pour info, pas à traiter maintenant)

- Le programme d'**histoire des arts** (p. 151-154 du PDF) n'est pas extrait : enseignement transversal du cycle 3, sans créneau à l'EDT et sans matière au §5 (ADR-0007).
- **« Initiation à la pensée informatique »** n'a aucun item : la source lui donne de la prose et aucun objectif, en disant que son contenu est « abordé dans les autres domaines de ce programme ».
- La CI ne couvre pas le critère d'idempotence du seed (pas de Postgres) ; il est couvert par `make test-core` dans le conteneur.
- Deux pages photographiées (`docs/page-92.heic`, `docs/page-70-semaine-3-etape-6-chap-7.HEIC`) complètent le PDF de littérature, à qui il manquait une page. Elles sont versionnées, pas à retoucher.
