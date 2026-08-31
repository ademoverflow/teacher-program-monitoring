# Phase 4 — rapport de fin de phase

## Fait

- **24 endpoints sous `/api`**, un router par ressource, tags en français, OpenAPI complet
  sur `/docs`. Aucune réponse n'est une ligne SQLModel : `core/src/core/schemas.py` déclare
  les 24 formes rendues (ADR-0022).
- **La CI a un Postgres.** `.github/workflows/check.yml` démarre un service `postgres:17` ;
  `core/tests/conftest.py` le migre, le sème et génère l'année une fois pour toute la suite.
  Les 17 tests des Phases 2 et 3 qui se `skip`aient en CI y tournent maintenant
  (ADR-0018). **208 tests verts, zéro skip.**
- **Un test de router partage la transaction du test** : session liée à une connexion dont
  la transaction externe est annulée à la fin, en `join_transaction_mode="create_savepoint"`
  — donc un endpoint qui `commit()` ne laisse rien derrière lui. Client `httpx.AsyncClient`
  sur `ASGITransport` plutôt que `TestClient`, qui pilote l'app depuis la boucle d'un autre
  thread et ne peut pas partager une connexion asyncpg (ADR-0019).
- **`GET /api/calendar`** rend l'écran 1 du §7 en une requête : les 5 périodes avec leurs
  semaines (7/7/5/6/11), les vacances, la semaine courante, et le nombre de jours chômés par
  semaine. **`/calendar/today`** rend le jour de classe d'aujourd'hui — chômé compris, avec
  son motif — et le prochain jour travaillé à ouvrir.
- **`GET /api/weeks/{n}`** rend la grille du §4.1 : chaque jour, chaque créneau de ce jour de
  la semaine, et les 0, 1 ou 2 séances de la cellule. Les trois pièges sont testés — S1 rend
  3 jours et 38 séances, une semaine pleine 50, le lundi de Pâques garde ses 10 cellules
  vides avec son motif, et une cellule dédoublée (CM1/CM2) est distinguée des deux cellules
  côte à côte du mardi 11h30.
- **`GET /api/days/{date}`** rend le jour avec ses séances dans l'ordre, leur créneau, leur
  séquence et leurs items de programme. **CRUD des séances** sous `/api/planned-sessions` :
  un `POST` refuse en 409 ce que l'EDT interdit — créneau d'un autre jour de la semaine,
  d'un autre niveau, jour chômé, triplet déjà pris — au lieu d'échouer sur la contrainte.
- **`GET /api/program-items`** filtre par niveau/matière/domaine et cherche par
  `websearch_to_tsquery('french', …)` sur la colonne générée et son index GIN — jamais
  `ILIKE`. Sans `q`, l'ordre est `source_order` ; avec, le rang.
  **`GET /api/planned-sessions?program_item_id=`** répond au « voir les séances liées » du
  §7.
- **Le cahier journal existe.** `core/services/journal.py` initialise un jour depuis ses
  séances, une fois, et **jamais par-dessus lui-même** — **201** la fois où il remplit,
  **200** ensuite, donc l'appelant distingue un remplissage d'un no-op sans champ ajouté à
  un schéma que le `GET` partage. Une ligne prend l'intitulé du créneau
  comme discipline (la matière là où le créneau nomme une paire), le `duration_minutes` du
  créneau (ADR-0003), et le titre de la séance au-dessus de ses objectifs — les deux colonnes
  que `docs/exemple-cahier-journal-quotidien.pdf` imprime. Ajout, édition, suppression,
  réordonnancement par ids (ADR-0021).
- **`POST /api/generation`** lance la génération dans la requête — 1740 séances en 0,2 à
  0,7 s — et rend le rapport de validation en JSON, chaque ligne avec sa nature. Une période
  **déjà entamée** est refusée en 409 tant que l'appelant n'a pas confirmé, et
  `GET /api/generation` dit lesquelles le sont avant qu'on poste (ADR-0020). Un code de
  période que l'année n'a pas est un 422, pas une génération qui n'écrit rien.
- **`GET/PUT /api/settings`** exposent les deux alternances, validées contre le modèle du
  seed loader, avec `requires_generation: true` — l'écran 5 du §7 a de quoi écrire que
  changer un réglage ne change rien tant que la génération n'est pas relancée.
- **Cinq ADR** (0018…0022), `CONTEXT.md` complété (cellule, discipline, période entamée),
  `CLAUDE.md` remis à jour.

## Critères d'acceptation (§8 Phase 4)

| Critère | Résultat |
|---|---|
| OpenAPI (`/docs`) complet et cohérent | 24 endpoints, 44 schémas, tags français, aucune ligne de table rendue |
| Tests verts | **208** en conteneur comme en CI, **zéro skip** (contre 115 + 17 skips) |
| Scénario curl documenté | ci-dessous, exécuté depuis une base vide |
| `make check` | vert |
| `make test` | vert (208 core + 2 webapp) |
| `make seed` idempotent depuis une base vide | vérifié après `docker compose down -v` |

## Scénario curl

Depuis une base reconstruite (`docker compose down -v && make up && make seed`), avec
`API=http://localhost:12109/api`.

### Naviguer une semaine

```console
$ curl -s $API/calendar/today
{"date": "2026-08-31", "school_day": null,
 "next_taught_day": {"date": "2026-09-01", "day_of_week": 2, "is_off": false,
                     "week_number": 1, "number_in_period": 1, "period_code": "P1"}}
```

La rentrée est le mardi : le 31/08 n'est pas un jour de classe, et « Aujourd'hui » sait quoi
ouvrir à la place. Un jour chômé, lui, revient dans `school_day` avec son motif — la page
peut dire pourquoi il n'y a pas classe — et `next_taught_day` dit où aller.

```console
$ curl -s $API/weeks/2
{"semaine": 2, "periode": "P1", "precedente": 1, "suivante": 3,
 "jours": [{"date": "2026-09-07", "creneaux": 10, "seances": 12},
           {"date": "2026-09-08", "creneaux": 12, "seances": 14},
           {"date": "2026-09-10", "creneaux": 12, "seances": 13},
           {"date": "2026-09-11", "creneaux": 10, "seances": 11}]}
```

44 créneaux dans la semaine, 50 séances : les six créneaux dédoublés par niveau font la
différence. Une requête suffit à dessiner la grille.

```console
$ curl -s $API/days/2026-09-07
09:00   10'  commun  Accueil · rituel de langue · plan de travail
09:10   45'  CM1     Séquence 1 — Les groupes dans la phrase (séance 1/2)
09:10   45'  CM2     Séquence 1 — Les groupes dans la phrase (séance 1/2)
09:55   20'  commun  Calcul mental
10:45   45'  CM1     Séquence 2 — Fractions-1 (séance 1/4)
10:45   45'  CM2     Séquence 2 — Aires-1 (séance 1/4)
11:30   45'  commun  Charlie et la chocolaterie — Semaine 1
12:15   15'  commun  Dictée du jour
14:00   15'  commun  Lecture offerte / lecture personnelle
14:15   45'  commun  États et constitution de la matière à l'échelle macroscopique
15:00   45'  commun  Anglais
15:45   45'  commun  Expérimenter, produire, créer
```

### Éditer un cahier journal

```console
$ curl -s -o journal.json -w '%{http_code}\n' -X POST $API/journal/2026-09-07/initialise
201
initialised=True  P1 S2  12 lignes
  1. Accueil · rituel de langue · plan de travail   10'  Accueil · rituel de langue · plan…
  2. Étude de la langue — Grammaire (CM1)           45'  Séquence 1 — Les groupes dans la…
  3. Étude de la langue — Grammaire (CM2)           45'  Séquence 1 — Les groupes dans la…
  4. Calcul mental                                  20'  Calcul mental
  5. Mathématiques — Nombres (CM1)                  45'  Séquence 2 — Fractions-1 (séance 1/4)
  6. Mathématiques — Nombres (CM2)                  45'  Séquence 2 — Aires-1 (séance 1/4)
  7. Lecture — Œuvre suivie                         45'  Charlie et la chocolaterie — Sem…
  8. Dictée du jour                                 15'  Dictée du jour
  9. Lecture offerte / lecture personnelle          15'  Lecture offerte / lecture person…
 10. Sciences et technologie                        45'  États et constitution de la mati…
 11. Anglais                                        45'  Anglais
 12. Arts plastiques                                45'  Expérimenter, produire, créer
```

Le créneau du lundi 15h45 s'appelle « Arts plastiques / Éducation musicale » dans l'EDT ; la
ligne dit « Arts plastiques », parce que l'intitulé nomme une paire et pas ce qui est
enseigné (ADR-0002).

```console
$ curl -s -X PATCH $API/journal/entries/$FIRST -H 'Content-Type: application/json' \
    -d '{"bilan":"Rentrée : présentation, appel, plan de la semaine."}'
1. Accueil · rituel de langue · plan de travail — bilan : Rentrée : présentation, appel…

$ curl -s -X POST $API/journal/2026-09-07/entries -H 'Content-Type: application/json' \
    -d '{"discipline":"Conseil de classe","duration_minutes":20,
         "objectives":"Règles de vie de la classe"}'
13. Conseil de classe (20') — séance planifiée : None

$ curl -s -X PUT $API/journal/2026-09-07/order -H 'Content-Type: application/json' \
    -d '{"entry_ids":[...]}'
  1. Accueil · rituel de langue · plan de travail
  2. Conseil de classe
  3. Étude de la langue — Grammaire (CM1)
  4. Étude de la langue — Grammaire (CM2)

$ curl -s -o /dev/null -w '%{http_code}\n' -X POST $API/journal/2026-09-07/initialise
200
```

Ré-initialiser ne réécrit rien : §10, « les cahiers journaux … ne sont jamais écrasés ».
Le **200** au lieu du **201** est comment l'API le dit — la première fois elle a rempli, la
seconde elle a trouvé le jour déjà tenu.

### Et la génération le sait

```console
$ curl -s -X POST $API/generation -d '{"periods":["P9"]}'
422 {"detail": "Périodes inconnues : P9"}

$ curl -s -o /dev/null -w '%{http_code}' -X POST $API/generation -d '{"periods":["P1"]}'
409
$ curl -s -X POST $API/generation -d '{"periods":["P1"]}'
{"detail": "Périodes déjà entamées : P1. Confirmez pour les régénérer."}

$ curl -s -X POST $API/generation -d '{"periods":["P1"],"confirm":true}'
périodes ['P1'], 326 séances écrites en 0.185s, intacts : ['2026-09-07'], erreurs : 0
```

326 au lieu de 338 : les 12 séances du lundi tenu au cahier journal ne sont pas réécrites.

### Chercher dans les programmes

```console
$ curl -s "$API/program-items?q=fractions&level=CM1"
3 items
  [CM1] Mathématiques / Nombres — Les fractions (p.31)
  [CM1] Mathématiques / Nombres — Les nombres décimaux (p.31)
  [CM1] Mathématiques / Calcul mental — Mémoriser des faits numériques (p.32)
```

`websearch_to_tsquery('french', …)` : « fractions » trouve « fraction », et les trois items
sont bien ceux qui parlent de fractions — pas ceux qui contiennent la chaîne.

## Non fait (et pourquoi)

- **`TestClient` n'est pas utilisé pour les routers**, alors que le §8 l'écrit. Il pilote
  l'app depuis la boucle d'événements d'un autre thread, et une connexion asyncpg appartient
  à la boucle qui l'a ouverte : la session que la fixture construit ne peut pas servir la
  requête. `httpx.AsyncClient` sur `ASGITransport` est la même chose au niveau HTTP
  (`TestClient` *est* un client httpx). `test_health.py` garde `TestClient` (ADR-0019).
- **Pas de migration Alembic** : la Phase 4 lit ce que la Phase 3 a écrit et écrit
  `journal_entries`, dont la table existe depuis la Phase 1. Rien n'a bougé dans le schéma.
- **`journal_revisions` n'est pas exposée.** C'est la Phase 7.
- **Aucune modification de `webapp/src`.** Le client typé est de la Phase 5.
- **Pas de pagination sur `/api/weeks` ni sur `/api/subjects`** : 36 semaines et 12 matières,
  la page entière est la bonne réponse.
- **Pas de filtre `?needs_review=`** sur les programmes : la colonne est rendue, parce qu'un
  item que le navigateur montre doit dire quand la source était difficile à lire, mais rien
  ne demande de filtrer dessus (ADR-0022).

## Ambiguïtés rencontrées

- **`discipline` est du texte libre, et le §5 ne dit pas ce qu'on y copie.** Trois lectures
  tenaient : le domaine, la matière, l'intitulé du créneau. Le domaine se disqualifie tout
  seul (« La matière, les mouvements et les signaux » pour une séance de sciences,
  « Compétences travaillées » pour les arts plastiques) ; l'exemple de cahier journal
  imprime des intitulés courts du genre « Grammaire », « Calcul Mental », « Anglais », qui
  sont exactement les intitulés de créneau de l'EDT. Tranché : l'intitulé du créneau, sauf
  pour les six créneaux qui nomment une paire (ADR-0021).
- **« Période déjà entamée » n'est pas défini par le §7.** Deux lectures : « la période
  contient aujourd'hui » ou « la période contient des jours que la génération refuserait de
  toucher ». La seconde est retenue : la première se tairait sur une régénération complète
  d'une période passée, et poserait la question pour une période à laquelle personne n'a
  encore touché (ADR-0020).
- **Une ré-initialisation après avoir tout supprimé re-remplit le jour.** L'état « jamais
  initialisé » et l'état « vidé à la main » ne se distinguent pas sans une colonne de plus.
  Le cas est celui où re-remplir est probablement ce qu'on veut ; noté dans ADR-0021.
- **`needs_review` sort dans `ProgramItemOut`.** C'est la seule colonne « de seed » qui
  traverse. Le §8 Phase 2 en fait une affirmation sur l'extraction, et le navigateur de
  programmes a le droit de la voir et de filtrer dessus.

## Revue de fin de phase

`mattpocock-skills:code-review` sur les deux axes. Ce qui en est sorti et ce qui a été fait :

| Trouvé | Fait |
|---|---|
| `SessionSummary`, `create_session` — « session » non qualifié, que `CONTEXT.md` proscrit, et qui collisionne avec l'`AsyncSession` du même paramètre | Renommé partout : `PlannedSessionSummary`, `PlannedSessionDetail`, `services/planned_sessions.py`, `routers/planned_sessions.py`, URL `/api/planned-sessions` |
| `ProgramItemPage` et `LinkedSessions` déclarés dans les routers alors que l'ADR-0022 dit « tout dans `schemas.py` » | Déplacés, avec `PAGE_SIZE`/`MAX_PAGE_SIZE` qui étaient dupliqués |
| `services/schedule.py` à 634 lignes, changeant pour six raisons | Coupé en `reference.py` (les petites tables), `schedule.py` (l'année, la semaine, le jour) et `curriculum.py` (la recherche) |
| « ce n'est pas un jour de classe » écrit quatre fois, trois recherches de jour différentes, « position = fin de la journée » deux fois | `services/school_day.py` : `not_a_school_day`, `find_school_day`, `next_position` |
| Cinq `_rendered` sans rapport, `async def run(...)` | Renommés : `_setting`, `_read_back`, `_entry`, `_report`, `launch_generation` |
| `linked_sessions()` appelée une fois pour emballer un appel | Inlinée |
| Le router du cahier journal cherchait le jour une seconde fois pour composer la réponse | Le service rend directement un `JournalDay` |
| `ProblemOut.kind: str` aplatissait l'énumération existante | Typé `ProblemKind` |
| **`POST /generation {"periods":["P9"]}` répondait 200 avec un rapport vide** | 422, « Périodes inconnues : P9 », et un test |
| **`initialise` ne disait pas s'il avait rempli** | 201 quand il remplit, 200 sinon |
| **`/calendar/today` perdait le motif d'un jour chômé**, et `next_school_day` renvoyait aujourd'hui sur un jour travaillé | `school_day` rend le jour chômé avec son motif, `next_taught_day` dit où aller |
| Le test de recherche vérifiait la botte de foin, pas chaque item | Chaque item rendu doit contenir le mot |
| `?needs_review=` n'était demandé nulle part | Retiré |

Deux remarques de la revue ont été gardées telles quelles, et pourquoi :

- **`SessionStatus` reste `SessionStatus`.** C'est la même objection de vocabulaire, mais
  l'énumération date de la Phase 1 et est lue par le générateur ; la renommer déborde de la
  phase.
- **`DayDetail.previous_day` / `next_day` / `has_journal`** ne sont pas dans le ticket 05.
  Ils sont dans l'écran 3 du §7 — la vue Jour se parcourt jour par jour et doit savoir s'il
  faut proposer d'initialiser. Exposer ce que les Phases 5 et 6 vont dessiner est le travail
  de la Phase 4.

## Points ouverts hérités (inchangés)

Les trois semaines d'œuvres non placées, les huit semaines de maths à 2 ou 3 séances,
l'histoire des arts non extraite et la matière `poesie` sans item restent ce que la Phase 3
en a dit (ADR-0011, ADR-0014, ADR-0017, ADR-0007). Le rapport de validation les rend
maintenant en JSON, chacune avec sa nature : 11 `calendrier`, 1 `source`, **0 `erreur`**.
