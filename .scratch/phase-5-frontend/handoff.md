Lis `MASTER-PROMPT.md` en entier, puis réalise la **Phase 5 — Frontend : navigation & programmes**.

## Où en est le dépôt

Les Phases 0 à 4 sont terminées, vérifiées et mergées dans `main`. Crée `phase-5-frontend` à
partir de `main`.

Ne relitige pas les phases précédentes : `git log` et les ADR ont le détail.

**Lis d'abord `CONTEXT.md` (glossaire du domaine) et les vingt-deux `docs/adr/`.** C'est la
convention du dépôt (`docs/agents/domain.md`). Les ADR 0001 à 0004 cadrent le calendrier et
l'EDT, les 0005 à 0008 le contenu pédagogique, les 0009 à 0017 la génération, et les **0018 à
0022 l'API que tu vas consommer** — l'ADR-0022 en particulier explique la forme du rendu
d'une semaine, qui est exactement la grille que tu dois dessiner.

Ouvre `/docs` (Swagger, `http://localhost:12109/docs`) : les 24 endpoints y sont, tagués en
français, avec leurs 44 schémas de réponse. C'est ta source de vérité pour les formes.

## Ce que la Phase 4 a changé et que MASTER-PROMPT ne sait pas

**L'API est complète et ne rend jamais une ligne de table.** `core/src/core/schemas.py`
déclare chaque corps de réponse ; ni `search_vector`, ni `created_at`, ni `updated_at` n'en
sortent.

| Endpoint | Ce que ça te donne |
|---|---|
| `GET /api/calendar` | **l'écran 1 en une requête** : les 5 périodes avec leurs semaines (n°, n° dans la période, dates, `days_off`), les 5 vacances, et `current_week_number` |
| `GET /api/calendar/today` | `school_day` (aujourd'hui s'il est un jour de classe, **chômé compris, avec son motif**) et `next_taught_day` (le jour à ouvrir) |
| `GET /api/timetable` | les 44 créneaux du gabarit |
| `GET /api/subjects` | les 12 matières avec leur **couleur** et leurs 45 domaines |
| `GET /api/weeks/{n}` | **l'écran 2 en une requête** : `days[]` → `cells[]` → `sessions[]` (0, 1 ou 2) |
| `GET /api/days/{date}` | le jour, ses séances dans l'ordre, leur créneau, séquence et items de programme |
| `GET /api/program-items` | `?level=&subject=&domain=&q=&limit=&offset=` → `{total, limit, offset, items}` |
| `GET /api/program-items/{id}` | l'item avec `source_file` / `source_page` |
| `GET /api/planned-sessions?program_item_id=` | « voir les séances liées » (§7 écran 4), paginé |
| `GET/POST/PATCH/DELETE /api/planned-sessions` | le CRUD des séances — **pas ton écran**, mais l'API existe |
| `GET/POST/PATCH/DELETE/PUT /api/journal/…` | le cahier journal — **Phase 6, n'y touche pas** |
| `GET/POST /api/generation` | l'écran 5 — **Phase 6 ou 8, pas ici** |
| `GET/PUT /api/settings` | les deux alternances, avec `requires_generation: true` |

Quelques précisions qui changent le code que tu vas écrire :

- **Une cellule de la grille porte 0, 1 ou 2 séances.** Deux séances = un créneau `commun`
  dédoublé par niveau (ADR-0010), à dessiner empilées **dans une case**. Ce n'est *pas* la
  même chose que les trois horaires où l'EDT lui-même a deux créneaux (mardi 11h30, jeudi
  11h30, jeudi 15h00) : là ce sont **deux cellules côte à côte**. Le glossaire appelle ça une
  **cellule** (`WeekCell`) ; lis l'entrée avant de nommer quoi que ce soit.
- **La recherche est déjà du plein texte Postgres.** `?q=` passe par
  `websearch_to_tsquery('french', …)` : « fractions » trouve « fraction », les guillemets et
  `-mot` marchent. N'ajoute pas de filtrage côté client par-dessus. Sans `q`, les items
  arrivent dans `source_order` (l'ordre de la source) ; avec, par rang.
- **`GET /api/calendar` porte `current_week_number`**, qui est `null` hors année scolaire —
  et « aujourd'hui » est le 31/08/2026 pour l'instant, donc `null` en pratique. Le repli est
  `next_taught_day` de `/api/calendar/today`.
- **La CI a maintenant un Postgres** (ADR-0018) et la suite core fait **208 tests, zéro
  skip**. Le job webapp n'a pas changé : `make check-webapp` puis `make test-webapp`.
- **Aucune migration en Phase 4** : le schéma n'a pas bougé depuis la Phase 3.
- Rappels toujours valables : UI et contenus en **français**, code et identifiants en
  **anglais** (§10) ; pas d'auth, pas de login, pas de rôles ; dates via
  `Intl.DateTimeFormat` et helpers maison, **pas de lib de dates** (§6).

## Ce que la webapp contient aujourd'hui (et c'est tout)

La Phase 4 n'a rien touché dans `webapp/`. Tu pars de :

- `webapp/src/main.tsx` — TanStack Router code-based, **une seule route** (`/` → `App`), le
  provider TanStack Query déjà branché.
- `webapp/src/App.tsx` — la page d'état de l'API (le smoke test de la Phase 0). Elle a
  vocation à disparaître ou à devenir « Aujourd'hui ».
- `webapp/src/lib/api.ts` — **`apiGet` et rien d'autre** : un fetch + `schema.parse` de zod,
  plus `healthSchema`. Pas de `apiPost`, pas de `ApiError` typée par endpoint.
- `webapp/src/App.test.tsx` — **le seul test du front** (2 cas).
- Tailwind v4, `lucide-react`, alias `@` → `src`, proxy Vite `/api` → `http://core:80`
  déjà configurés. **Toujours des URLs relatives `/api/...`** : pas de CORS, pas d'IP LAN.

## À trancher avant de coder

1. **Comment le client typé grandit.** `lib/api.ts` fait 40 lignes et connaît un endpoint.
   Tu vas en consommer une dizaine, contre 44 schémas OpenAPI. Écrire les schémas zod à la
   main, un fichier par ressource (`lib/api/calendar.ts`, `lib/api/weeks.ts`…), ou tout dans
   `api.ts` ? Et : générer depuis `openapi.json` plutôt que d'écrire à la main ? Le §6 dit
   « client API minimal typé (fetch + zod) », ce qui n'interdit ni ne prescrit la génération.
   **Tranche-le en premier, tout le reste en dépend.** Attention si tu génères : il faut que
   `make check` reste vert sans stack allumée.
2. **Écrire ou non les verbes d'écriture maintenant.** Les écrans 1, 2 et 4 sont en lecture
   seule. `apiPost` / `apiPatch` / `apiDelete` sont de la Phase 6. Le §8 dit « ne pas
   anticiper les phases suivantes » — mais un client qui n'a que `apiGet` est peut-être une
   demi-abstraction. Décide et écris-le.
3. **La forme de la grille EDT.** Les créneaux ne s'alignent pas sur une grille régulière :
   le vendredi 11h30-12h00 et 12h00-12h30 ne tombent pas sur les 11h30-12h15 / 12h15-12h30
   des autres jours (c'est ADR-0003, et c'est voulu). Une grille « une ligne par
   (starts_at, ends_at) » donne **12 bandes** dont deux ne concernent que le vendredi. Soit
   tu positionnes les cellules au temps (CSS grid proportionnel), soit tu assumes des lignes
   à trous. **Regarde le §4.1 et `docs/edt.pdf` avant de choisir.**
4. **La récréation et la pause méridienne n'existent pas en base.** `timetable_slots` n'a
   aucune ligne pour 10h15-10h45 ni pour 12h30-14h00 — ce sont des trous entre créneaux. Le
   §4.1 et l'exemple de cahier journal les impriment pourtant. Décide d'où elles viennent
   (constantes du front, dérivées des trous) et dis-le.
5. **D'où vient la couleur d'une cellule.** `cell.slot.subject` est **null pour les 6
   créneaux alternants** (ADR-0002) : c'est la séance qui porte la matière résolue. Et
   **139 séances n'ont aucune matière** — l'accueil du matin, qui n'en a pas (ADR-0015).
   Une cellule vide d'un jour chômé n'a donc parfois ni l'une ni l'autre. Décide de la
   cascade (`session.subject` → `slot.subject` → neutre) une fois pour toutes.
6. **Les URL des routes.** §10 : UI en français, identifiants en anglais. Une URL est-elle de
   l'UI ? `/semaine/12` ou `/weeks/12` ? Choisis et sois cohérent — c'est ce que
   l'enseignante verra dans sa barre d'adresse.
7. **Ce que tu testes en vitest.** Il y a exactement 2 tests dans le front aujourd'hui. Les
   candidats évidents : l'assemblage de la grille depuis une réponse `/api/weeks/{n}` (les
   trois pièges ci-dessous s'y jouent), les filtres du navigateur de programmes, le
   formatage des dates. Décide du niveau (composant contre pur) avant d'écrire.

## Pièges connus pour cette phase

- **La S1 n'a que trois jours** (rentrée élèves le mardi 01/09/2026) : une grille qui suppose
  quatre colonnes se casse sur la première semaine de l'année. 38 séances, pas 50.
- **Les 4 jours chômés gardent leurs cellules, vides, avec `off_reason`** (ADR-0001). Ne les
  omets pas : l'enseignante doit voir le trou du lundi de Pâques, pas le deviner.
- **`ends_at - starts_at != duration_minutes`** pour le calcul mental du vendredi (ADR-0003).
  Les bornes pour placer dans la grille, `duration_minutes` quand tu affiches une durée.
- **Une séance CM1 et une séance CM2 dans une cellule** ne se distinguent que par
  `session.level` : le §7 demande des **badges CM1/CM2** dessus.
- **`current_week_number` est `null` hors année.** L'écran « semaine courante par défaut » du
  §8 doit se replier sur `next_taught_day`, sinon la page est vide en août.
- **N'appelle pas `/api/journal/…`.** Le cahier journal est la Phase 6, y compris son
  initialisation (elle existe déjà côté API, et l'appeler écrit en base).
- **`POST /api/generation` écrit 1740 lignes.** L'écran Réglages est la Phase 6/8 ; ne le
  câble pas « pour voir ».
- **Ne déborde pas sur la Phase 6** : pas de vue Jour éditable, pas de cahier journal, pas
  d'impression. La vue Jour du §7 écran 3 n'est pas dans cette phase — un clic depuis la
  semaine peut mener à une page, mais son contenu est de la Phase 6.

## Repères de vérification (à recalculer, pas à croire sur parole)

Stack allumée (`make up && make seed`), contre `http://localhost:12109` :

- `GET /api/calendar` → **36 semaines**, réparties **7/7/5/6/11**, **5 vacances**.
- `GET /api/weeks/1` → **3 jours** (mardi, jeudi, vendredi), **38 séances**.
- `GET /api/weeks/2` → **4 jours**, **50 séances**, et 10/12/12/10 cellules par jour.
- `GET /api/weeks/25` → le lundi est chômé : **10 cellules, 0 séance**, `off_reason` rempli.
- `GET /api/weeks/2` mardi 09h10 → **une cellule, deux séances** (CM1 puis CM2) ;
  mardi 11h30 → **deux cellules**, une séance chacune. Ne confonds pas les deux.
- `GET /api/timetable` → **44 créneaux**, dont **6 alternants** à `subject: null`.
- `GET /api/subjects` → **12 matières**, **45 domaines**, toutes avec une couleur.
- `GET /api/program-items` → **220 items** ; `?q=fractions&level=CM1` → **3 items**.
- `GET /api/days/2026-09-07` → **12 séances**, la première (l'accueil) à `subject: null`.

## Skills à appeler

- **`mattpocock-skills:to-tickets`** en premier si tu juges la phase trop grosse pour une
  session. Les tickets vont dans `.scratch/<feature-slug>/` (voir
  `docs/agents/issue-tracker.md`). Les squelettes des Phases 2, 3 et 4 sont dans
  `.scratch/phase-2-content/`, `.scratch/phase-3-generation/` et `.scratch/phase-4-api/` si
  tu veux la forme attendue — la Phase 4 a aussi un `report.md` et un `spec.md` de fin de
  phase.
- **`/new-route`** et **`/new-component`** pour le scaffolding conforme, **`/check`** et
  **`/test`** pour la boucle qualité.
- **`mattpocock-skills:tdd`** pour l'assemblage de la grille : les trois pièges (S1, jour
  chômé, cellule dédoublée) s'écrivent en rouge sur une réponse figée, sans base ni réseau.
- **`mattpocock-skills:prototype`** si la forme de la grille (décision 3) ne se tranche pas
  sur le papier.
- **`mattpocock-skills:diagnosing-bugs`** dès qu'un affichage ne tombe pas juste.
- **`mattpocock-skills:domain-modeling`** si l'UI fait émerger du vocabulaire absent de
  `CONTEXT.md`, et écris un ADR pour chacune des décisions ci-dessus que tu tranches (la
  numérotation reprend à **0023**).
- **`mattpocock-skills:code-review`** en fin de phase, avant le commit final (§9). Les revues
  des Phases 3 et 4 ont trouvé des choses réelles ; ne la saute pas.

## Fini quand

Critères du §8 Phase 5 : parcours année → période → semaine fluide, semaine courante par
défaut, recherche « fractions » qui renvoie les items attendus, grille EDT fidèle au §4.1
(colonnes lun/mar/jeu/ven, lignes horaires, splits CM1/CM2, couleurs par matière). Plus les
règles communes : `make check` vert, `make test` vert, `make seed` toujours idempotent depuis
une base vide (`docker compose down -v && make up && make seed`), commits conventionnels, et
un court rapport (fait / non fait / ambiguïtés).

## Points ouverts hérités (pour info, pas à traiter maintenant)

De la Phase 4 :

- **`TestClient` n'est pas utilisé pour les routers**, contre ce que le §8 écrit : il pilote
  l'app depuis la boucle d'un autre thread et ne peut pas partager une connexion asyncpg. Le
  choix et sa raison sont dans l'ADR-0019.
- **Vider un cahier journal puis le ré-initialiser le re-remplit** : les états « jamais
  initialisé » et « vidé à la main » ne se distinguent pas sans une colonne de plus
  (ADR-0021). À revoir en Phase 6 si l'usage le demande.
- **`SessionStatus` garde son nom**, alors que `CONTEXT.md` proscrit « session » non
  qualifié : l'énumération date de la Phase 1 et le générateur la lit.

Des Phases 2 et 3 :

- **Trois semaines d'œuvres ne sont pas placées** et deux œuvres ne sont pas lues :
  « Hansel et Gretel » (le repli du §4.5) et « Zathura » (aucun planning hebdomadaire dans la
  source), plus « Jumanji » semaine 3. L'année a 33 lundis pour 36 semaines (ADR-0017).
- **Huit semaines de maths placent 2 ou 3 séances au lieu de 4** (ADR-0011).
- Le programme d'**histoire des arts** (p. 151-154) n'est pas extrait, et **« Initiation à la
  pensée informatique »** n'a aucun item (ADR-0007).
- La matière **`poesie`** existe, n'a aucun item et ne porte aucune séance (ADR-0014) — elle
  a une couleur et apparaîtra donc dans les filtres du navigateur de programmes en rendant
  zéro résultat. À toi de décider si tu la masques.
