Lis `MASTER-PROMPT.md` en entier, puis réalise la **Phase 6 — Cahier journal**.

## Où en est le dépôt

Les Phases 0 à 5 sont terminées, vérifiées et mergées dans `main`. Crée `phase-6-journal` à
partir de `main`.

Ne relitige pas les phases précédentes : `git log` et les ADR ont le détail.

**Lis d'abord `CONTEXT.md` (glossaire du domaine) et les vingt-six `docs/adr/`.** C'est la
convention du dépôt (`docs/agents/domain.md`). Les 0001 à 0004 cadrent le calendrier et
l'EDT, les 0005 à 0008 le contenu, les 0009 à 0017 la génération, les 0018 à 0022 l'API, et
les **0023 à 0026 le front que tu vas prolonger**. L'ADR-0021 en particulier dit ce qu'une
ligne de cahier journal copie d'une séance, et pourquoi ; c'est exactement l'écran que tu
dois dessiner.

Ouvre `/docs` (Swagger, `http://localhost:12109/docs`) : les 24 endpoints y sont, tagués en
français. C'est ta source de vérité pour les formes.

## Ce que la Phase 5 a construit et que MASTER-PROMPT ne sait pas

**Le front n'est plus un smoke test.** `webapp/src` porte trois écrans, un layout, un client
typé et 53 tests vitest. Tu prolonges, tu ne repars pas de zéro.

```
webapp/src/
├── main.tsx              # sept lignes : monte le routeur
├── router.tsx            # l'arbre de routes — PAS main.tsx (ADR-0026)
├── pages/                # Year · Week · CurrentWeek · Programs · ProgramItem (export default)
├── components/           # AppLayout · WeekGrid · Loading · LoadFailure · Empty ·
│                         #   LevelBadge · SubjectLine · ApiStatus (export nommé)
├── lib/
│   ├── api/              # client.ts (apiGet) + un module par ressource, zod à la main
│   ├── week-grid.ts      # assemblage pur de la grille §4.1
│   ├── dates.ts          # Intl + helpers, pas de lib de dates
│   ├── colors.ts         # la cascade de couleurs (ADR-0025)
│   ├── plural.ts         # « 1 jour » / « 2 jours »
│   ├── current-week.ts   # la semaine courante et son repli
│   └── program-search.ts # les search params de /programmes
└── test/
    ├── app.tsx           # renderApp(url) + stubApi(routes) : monte le vrai routeur
    ├── setup.ts          # le cleanup de Testing Library (vitest ne l'enregistre pas seul)
    └── fixtures/         # réponses figées d'une stack seedée (voir son README)
```

Ce qui change ce que tu vas écrire :

- **Les routes sont en français** (ADR-0026) : `/annee`, `/semaine/12`, `/programmes`. Les
  identifiants de code restent anglais. Ta vue Jour sera donc `/jour/2026-09-07`.
- **`/` redirige vers `/annee`.** §8 Phase 6 fait d'« Aujourd'hui » la page d'accueil : c'est
  **une ligne à changer** dans `router.tsx`, et aucune URL que l'enseignante a gardée ne
  bouge.
- **La sidebar a trois entrées sur cinq.** « Aujourd'hui » et « Réglages » ont été laissées
  de côté plutôt que d'être des liens vers rien. Tu ajoutes « Aujourd'hui ».
- **Il n'y a pas de route `/jour`, et les en-têtes de jour de la grille ne sont pas des
  liens.** §7 écran 2 demande « clic sur un jour → vue Jour » : c'est toi qui le branches,
  dans `components/WeekGrid.tsx`.
- **Le client ne sait que lire.** `lib/api/client.ts` n'a que `apiGet` — délibérément
  (ADR-0023) : « les verbes d'écriture appartiennent à la phase qui écrit ». C'est toi.
  Il a aussi `buildQuery`, `ApiError` (avec `status`) et `shouldRetry`, qui n'insiste pas
  sur un 4xx.
- **`make check-webapp` typecheck maintenant** (`make type-check-webapp` → `tsc --noEmit`).
  Biome ne l'a jamais fait, et `vite.config.ts` était cassé pour `tsc` : le front n'avait
  jamais été typechecké avant la Phase 5.
- **`.claude/skills/new-route`** a été corrigé : il envoyait éditer `main.tsx` et copier un
  `pages/About.tsx` qui n'existe pas.

## L'API dont tu as besoin

Tout est déjà écrit et testé (208 tests core). Rien à ajouter côté `core/` a priori.

| Endpoint | Ce que ça te donne |
|---|---|
| `GET /api/calendar/today` | **la page d'accueil** : `school_day` (aujourd'hui s'il est jour de classe, **chômé compris**) et `next_taught_day` (le jour à ouvrir) |
| `GET /api/days/{date}` | **l'écran 3 côté programmation** : le jour, ses séances dans l'ordre avec `slot`, `sequence`, `sequence_session`, `program_items`, `objectives`, `content`, `materials`, `status`, plus `previous_day` / `next_day` et `has_journal` |
| `GET /api/journal/{date}` | le cahier journal : `initialised`, `entries[]`, et le contexte d'impression (`week_number`, `number_in_period`, `period_code`, `is_off`, `off_reason`) |
| `POST /api/journal/{date}/initialise` | remplit le jour depuis ses séances — **201** si ça remplit, **200** si c'était déjà rempli (ADR-0021) |
| `POST /api/journal/{date}/entries` | ajoute une ligne à la fin — `discipline` (obligatoire, ≥1 car.), `duration_minutes`, `objectives`, `bilan`, `notes`, `planned_session_id`, `position` |
| `PATCH /api/journal/entries/{id}` | change une ligne — tous les champs sont optionnels |
| `DELETE /api/journal/entries/{id}` | supprime une ligne → **204** |
| `PUT /api/journal/{date}/order` | réordonne — `{entry_ids: [...]}` doit nommer **toutes** les lignes du jour, chacune une fois, sinon **400** |
| `PATCH /api/planned-sessions/{id}` | le **statut** d'une séance (`planifiée`/`faite`/`reportée`/`annulée`), son titre, ses objectifs, son matériel |
| `GET/POST /api/generation` | l'écran 5 — **hors périmètre, voir la décision 7** |

## À trancher avant de coder

1. **Comment le client apprend à écrire.** L'ADR-0023 a laissé la question ouverte exprès :
   « la forme que veulent les verbes d'écriture — un corps d'erreur que l'UI peut montrer,
   une mise à jour optimiste — est une connaissance qu'a la Phase 6 ». Tu as maintenant
   cette connaissance. `apiPost` / `apiPatch` / `apiDelete` / `apiPut` génériques, ou une
   mutation nommée par action dans `lib/api/journal.ts` ? Et l'erreur : `ApiError` ne porte
   que le statut, or FastAPI renvoie `{"detail": "..."}` en français — un 400 sur
   `PUT /order` et un 409 sur une séance ont un message que l'enseignante devrait voir.
   **Tranche-le en premier.**
2. **Quand le cahier journal s'initialise.** L'ADR-0021 dit « appelle-le à chaque ouverture
   de la vue jour ». C'est une **écriture** à chaque ouverture, et TanStack Query n'aime pas
   qu'un `useQuery` écrive. Mutation au montage ? Bouton « Initialiser depuis la
   programmation » ? Le 201/200 existe précisément pour que tu puisses distinguer les deux
   sans drapeau — sers-t'en, et dis dans quel sens tu as tranché.
3. **L'édition inline.** Auto-save au blur, à la frappe débouncée, ou bouton ? Optimiste ou
   pas ? Le bilan est un champ long qu'on remplit en fin de journée, la discipline un champ
   court : ils ne veulent peut-être pas la même chose.
4. **Le réordonnancement.** §8 dit « drag & drop **ou boutons** ». Le drag & drop veut une
   dépendance (`@dnd-kit`…) que le dépôt n'a pas ; les boutons haut/bas n'en veulent aucune.
   Note que `PUT /{date}/order` attend la **liste complète** des ids : la vue doit connaître
   tout l'ordre, pas juste le déplacement.
5. **La vue imprimable.** Route séparée (`/jour/$date/impression`) ou `@media print` sur la
   vue Jour ? Le modèle est `docs/exemple-cahier-journal-quotidien.pdf` : un en-tête
   « Période X – Semaine Y », la date en toutes lettres, « CM1-CM2 – Cycle 3 », puis un
   tableau à trois colonnes *Discipline - Durée / Objectif(s) et compétence(s) / Bilan* —
   avec la récréation et la pause méridienne imprimées **en travers du tableau**, comme dans
   la grille de la Phase 5 (`lib/week-grid.ts` sait déjà les trouver).
6. **Où vit le statut d'une séance.** `status` est sur `planned_sessions`, pas sur la ligne
   de cahier journal — et une ligne peut n'avoir aucune séance derrière elle
   (`planned_session_id` est nullable, l'enseignante ajoute des lignes). §8 demande « statuts
   des séances » dans la vue Jour. Deux listes côte à côte (la programmation à gauche, le
   cahier journal à droite) ? Un seul tableau où le statut est une colonne quand la ligne
   vient d'une séance ? **Le glossaire dit que ce sont deux choses** — une `discipline` est
   du texte libre, une `matière` est une ligne de `subjects`. Ne les refonds pas.
7. **L'écran 5 (Génération / Réglages) n'est assigné à aucune phase.** §8 donne les écrans
   1-2-4 à la Phase 5, l'écran 3 à la Phase 6, le feedback IA à la Phase 7 ; l'écran 5 du §7
   n'apparaît nulle part. Soit tu l'ajoutes ici (la sidebar serait complète), soit tu le
   laisses à la Phase 8 et tu le dis dans le rapport. **Ne le câble pas à moitié.**

## Pièges connus pour cette phase

- **`POST /{date}/initialise` écrit en base.** C'est le premier endpoint du projet que le
  front appelle en écriture. En dev, un appel « pour voir » remplit vraiment le jour.
- **Un jour chômé a un cahier journal légal et vide.** `GET /api/journal/2027-03-29` répond
  `is_off: true`, `off_reason: "Lundi de Pâques"`, `initialised: false`, zéro ligne, et
  l'initialiser répond **200** sans rien créer — il n'y a aucune séance à copier. La vue doit
  dire pourquoi, pas afficher un tableau vide.
- **Un mercredi, un week-end, des vacances → 404** sur `/api/journal/{date}` comme sur
  `/api/days/{date}`. « Aujourd'hui » doit se replier sur `next_taught_day`, pas planter.
- **Aujourd'hui, c'est le 31/08/2026** : `school_day` est `null`, `next_taught_day` est le
  mardi 01/09. La page d'accueil est donc **toujours** dans le cas du repli pour l'instant.
- **`PUT /order` est tout-ou-rien** : la liste doit nommer chaque ligne du jour exactement
  une fois, sinon 400. Un réordonnancement optimiste qui envoie un sous-ensemble échoue.
- **Vider un cahier journal puis le ré-initialiser le re-remplit** (ADR-0021) : « jamais
  initialisé » et « vidé à la main » ne se distinguent pas. Si l'usage montre que c'est
  gênant, c'est une colonne de plus et une migration — décide, ne subis pas.
- **La durée d'une ligne vient de `duration_minutes`, pas de `ends_at - starts_at`**
  (ADR-0003) : le calcul mental du vendredi est 15' dans une bande de 20'.
- **Les dates et les heures sont toutes deux des `string` dans le front.**
  `formatTime(day.date)` compile et est faux. Si tu introduis des types marqués, fais-le en
  premier ou pas du tout.
- **Pas d'IA en Phase 6.** Le panneau Feedback IA (§7 écran 3, dernière ligne) est la
  Phase 7. `POST /api/journal/{date}/feedback` n'existe pas encore.
- **N'appelle pas `POST /api/generation`** : il écrit 1740 lignes. `GET` est sans risque et
  te dit quelles périodes sont entamées.
- Rappels toujours valables : UI et contenus en **français**, code et identifiants en
  **anglais** (§10) ; pas d'auth ; dates via `Intl` et `lib/dates.ts`, **pas de lib de
  dates** (§6) ; URLs relatives `/api/...`.

## Repères de vérification (à recalculer, pas à croire sur parole)

Stack allumée (`make up && make seed`), contre `http://localhost:12109` :

- En base au départ : **0 `journal_entries`**, **143 `school_days`** dont **139 non chômés**,
  **1740 `planned_sessions`**.
- `GET /api/days/2026-09-07` → **12 séances**, `has_journal: false`, `previous_day`
  2026-09-04, `next_day` 2026-09-08 ; la première séance (l'accueil) a `subject: null`.
- Séances par jour d'une semaine pleine : **lundi 12 · mardi 14 · jeudi 13 · vendredi 11**.
- `GET /api/journal/2026-09-07` → `initialised: false`, 0 ligne, `week_number: 2`,
  `number_in_period: 2`, `period_code: "P1"`.
- `POST /api/journal/2026-09-07/initialise` → **201** et **12 lignes** ; le rappeler → **200**
  et toujours 12.
- `GET /api/journal/2027-03-29` → `is_off: true`, « Lundi de Pâques » ; l'initialiser → **200**
  et **0 ligne**.
- `GET /api/journal/2026-09-02` (un mercredi) → **404**.
- `GET /api/calendar/today` → `school_day: null`, `next_taught_day` = 2026-09-01.
- `PUT /api/journal/2026-09-07/order` avec 11 ids sur 12 → **400**.

## Skills à appeler

- **`mattpocock-skills:to-tickets`** en premier si tu juges la phase trop grosse pour une
  session. Les tickets vont dans `.scratch/phase-6-journal/` (voir
  `docs/agents/issue-tracker.md`). Les Phases 2 à 5 ont chacune leur `spec.md`, leurs
  `issues/` et leur `report.md` si tu veux la forme attendue.
- **`/new-route`** (à jour : il pointe sur `router.tsx`) et **`/new-component`**, **`/check`**
  et **`/test`**.
- **`mattpocock-skills:tdd`** pour les règles d'édition : l'initialisation 201/200, l'ordre
  tout-ou-rien et le jour chômé s'écrivent en rouge sur une réponse figée. `test/app.tsx`
  monte déjà le vrai routeur sur une URL choisie avec un `fetch` bouchonné — **`stubApi` ne
  répond aujourd'hui qu'aux `GET`**, tu devras lui apprendre les autres verbes.
- **`mattpocock-skills:prototype`** si la forme de la vue Jour (décision 6) ne se tranche pas
  sur le papier.
- **`mattpocock-skills:diagnosing-bugs`** dès qu'un affichage ne tombe pas juste.
- **`mattpocock-skills:domain-modeling`** si l'UI fait émerger du vocabulaire absent de
  `CONTEXT.md`, et écris un ADR pour chacune des décisions ci-dessus que tu tranches (la
  numérotation reprend à **0027**).
- **`mattpocock-skills:code-review`** en fin de phase, avant le commit final (§9). La revue
  de la Phase 5 a trouvé deux vrais bugs que les tests ne voyaient pas ; ne la saute pas.

## Fini quand

Critères du §8 Phase 6 : cycle complet sur un jour de démo — **ouvrir → éditer → bilan →
imprimer** ; les modifications persistent en DB ; le cahier journal reste intact après une
régénération de la programmation. Plus les règles communes : `make check` vert, `make test`
vert, `make seed` toujours idempotent depuis une base vide
(`docker compose down -v && make up && make seed`), commits conventionnels, et un court
rapport (fait / non fait / ambiguïtés).

Vérifie la promesse de non-écrasement pour de vrai : initialise un jour, édite une ligne,
relance `make generate`, et relis le cahier journal.

## Points ouverts hérités (pour info, pas à traiter maintenant)

De la Phase 5 :

- **Les URL sont en français** (ADR-0026) : c'était un coup de dé argumenté, pas une
  évidence. Si tu le retournes, retourne-le partout et écris-le.
- **Les dates et les heures sont des `string`** — voir les pièges.
- **La matière `poesie` reste dans le filtre des programmes** et rend zéro résultat
  (ADR-0014). Affiché exprès.
- **Une cellule alternante sans séance n'a aucune couleur** : le créneau nomme une paire et
  aucune séance ne l'a résolue. N'arrive pas dans l'année générée — mais si tu ajoutes la
  suppression d'une séance, ça arrivera.
- **Sur la fiche d'un item de programme, les séances liées ne sont pas des liens** :
  `PlannedSessionSummary` porte la date et pas la semaine, et il n'y avait nulle part où
  aller. Maintenant qu'il y a une vue Jour, c'est un `<Link to="/jour/$date">`.

De la Phase 4 :

- **`TestClient` n'est pas utilisé pour les routers** (ADR-0019).
- **`SessionStatus` garde son nom**, alors que `CONTEXT.md` proscrit « session » non
  qualifié : l'énumération date de la Phase 1 et le générateur la lit.

Des Phases 2 et 3 :

- **Trois semaines d'œuvres ne sont pas placées** et deux œuvres ne sont pas lues (ADR-0017).
- **Huit semaines de maths placent 2 ou 3 séances au lieu de 4** (ADR-0011).
- Le programme d'**histoire des arts** n'est pas extrait, et **« Initiation à la pensée
  informatique »** n'a aucun item (ADR-0007).
