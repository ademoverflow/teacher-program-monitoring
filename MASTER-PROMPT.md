# PROMPT MAÎTRE — Application de gestion d'année double niveau CM1-CM2

> **Comment utiliser ce document.** C'est la référence unique du projet. Chaque mission de développement est décrite dans une **Phase numérotée** (§8). Pour lancer un agent : « Lis `MASTER-PROMPT.md` en entier, puis réalise la **Phase N**. » Les phases se font dans l'ordre ; chaque phase se termine par ses critères d'acceptation validés, `make check` vert, et un commit conventionnel. Ne pas anticiper les phases suivantes.

---

## 1. Contexte & objectif

Application web **locale** (PC de l'enseignante uniquement, **une seule utilisatrice, aucun login/auth**) pour gérer une année complète en **double niveau CM1-CM2**, année scolaire **2026-2027, zone C**.

L'application doit permettre de :

1. **Générer et consulter la programmation annuelle complète** : par période (P1→P5), par semaine, par jour, séance par séance, en respectant **scrupuleusement** l'emploi du temps (§4.1) et les outils pédagogiques choisis (§4.3 à §4.5).
2. **Naviguer** dans un calendrier fluide : vue année → période → semaine → jour.
3. **Consulter et chercher dans les programmes officiels** CM1 et CM2 (filtre par matière/niveau/domaine, recherche par mots-clés sur titres et descriptions).
4. **Tenir le cahier journal quotidien** : pour chaque jour de classe, la liste ordonnée des séances avec objectifs/compétences et bilan, modifiable à la volée.
5. **Ajuster le cahier journal via feedback IA** : l'enseignante décrit ce qui s'est réellement passé ou ce qu'elle veut changer ; l'IA (API Anthropic) propose un cahier journal modifié ; elle prévisualise le diff et applique.

**Tout est persisté en base de données PostgreSQL.** Aucune donnée métier dans le localStorage ou dans des fichiers à l'exécution.

**Définition du succès** : le 1er septembre 2026, l'enseignante ouvre l'app, voit sa semaine 1, ouvre le jour, a son cahier journal pré-rempli depuis la programmation, le corrige en fin de journée (à la main ou via feedback IA), et peut à tout moment consulter les programmes et la suite de l'année.

---

## 2. Vocabulaire métier (à utiliser partout : code, DB, UI)

| Terme | Définition |
|---|---|
| **Année scolaire** | 2026-2027, zone C. |
| **Période** | Bloc de classe entre deux vacances : P1…P5 (voir §4.2). |
| **Semaine** | Semaine de classe, numérotée globalement (S1…S36) et relative à sa période (P2-S3). |
| **Jour de classe** | Lundi, mardi, jeudi, vendredi uniquement (pas de mercredi), hors fériés/pont. |
| **Créneau** | Ligne du gabarit EDT : plage horaire × jour × discipline (ex. « lundi 9h10-9h55 · Étude de la langue · Grammaire »). |
| **Séance** | Instance planifiée d'un créneau pour un jour précis, rattachée à une séquence et/ou un item de programme, avec titre, objectifs, matériel. |
| **Séquence** | Suite de séances d'une méthodo sur une notion (ex. maths CM1 séquence 12 « Addition et soustraction de nombres décimaux », 4 séances/semaine). |
| **Niveau** | `CM1`, `CM2` ou `commun` (une séance peut concerner un seul niveau : créneaux splittés). |
| **Alternance** | Règle de rotation d'un créneau partagé : Histoire ↔ Géographie, Arts plastiques ↔ Éducation musicale (paramétrable, voir §4.1). |
| **Matière / Domaine** | Ex. Français → Grammaire ; Maths → Nombres ; classification issue des programmes officiels. |
| **Programme officiel** | Contenus/attendus institutionnels 2026-2027 par niveau/matière/domaine (source : `docs/programme-cm1-cm2.pdf`). |
| **Cahier journal** | Document du jour : lignes ordonnées `Discipline-Durée / Objectifs & compétences / Bilan` (modèle : `docs/exemple-cahier-journal-quotidien.pdf`). |
| **Révision IA** | Modification du cahier journal proposée par l'IA suite à un feedback, avec trace conservée. |

---

## 3. Sources documentaires (`docs/`)

| Fichier | Pages | Rôle | Consigne de lecture |
|---|---|---|---|
| `edt.pdf` | 2 | EDT hebdomadaire à respecter **scrupuleusement** | Déjà transcrit en §4.1 — le PDF fait foi en cas de doute |
| `programme-cm1-cm2.pdf` | 154 | Programmes officiels CM1 & CM2 (2026-2027), document visuel avec liens internes, par matière → domaine | Lire par tranches ≤ 20 pages (paramètre `pages` du Read). Extraction structurée en Phase 2 |
| `outil-pedagogique-maths-cm1.pdf` | 1 | Méthodo maths CM1 : 35 séquences/an | Déjà transcrit en §4.3 |
| `outil-pedagogique-maths-cm2.pdf` | 1 | Méthodo maths CM2 : 35 séquences/an | Déjà transcrit en §4.3 |
| `outil-pedagogique-grammaire-conjugaison.pdf` | 3 | Progressions RETZ grammaire-conjugaison CM1 (21 séq. + objectifs) et CM2 (21 séq., sommaire) | Titres en §4.4 ; objectifs détaillés CM1 à extraire en Phase 2 |
| `outil-pedagogique-litterature-annee.pdf` | 5 | Programmation littérature cycle 3 : thèmes → périodes → œuvres | Mapping en §4.5 |
| `outil-pedagogique-litterature-par-semaine.pdf` | 35 | Planning semaine par semaine, par œuvre (ex. Charlie et la chocolaterie : 7 semaines, étapes numérotées, fiches, devoirs). **Scans photo** : lire en vision, par tranches ≤ 20 pages | Extraction en Phase 2 |
| `exemple-cahier-journal-quotidien.pdf` | 1 | Modèle de cahier journal quotidien | Structure reprise en §5 (`journal_entries`) |

**Garde-fou : ne jamais inventer de contenu pédagogique.** Tout titre, objectif ou contenu de séance provient des PDFs ou des données embarquées ci-dessous. En cas de zone illisible ou d'ambiguïté : marquer `à compléter` et lister l'ambiguïté dans le rapport de fin de phase.

---

## 4. Données de référence embarquées

### 4.1 EDT hebdomadaire (transcription de `docs/edt.pdf` — immuable sauf demande explicite de l'utilisateur)

Jours de classe : **lundi, mardi, jeudi, vendredi**. Récréation 10h15-10h45. Pause méridienne 12h30-14h00.

| Horaires | Lundi | Mardi | Jeudi | Vendredi |
|---|---|---|---|---|
| 9h00-9h10 | Accueil · rituel de langue · plan de travail (commun, tous les jours) | idem | idem | idem |
| 9h10-9h55 (45') | Étude de la langue — **Grammaire** | Étude de la langue — **Conjugaison** | Étude de la langue — **Orthographe** | Étude de la langue — **Vocabulaire / Dictée bilan** |
| 9h55-10h15 | Calcul mental (20') | Calcul mental (20') | Calcul mental (20') | Calcul mental (15') |
| 10h15-10h45 | Récréation | Récréation | Récréation | Récréation |
| 10h45-11h30 (45') | Mathématiques — **Nombres** | Mathématiques — **Calculs** | Mathématiques — **Grandeurs et mesures** | Mathématiques — **Géométrie** |
| 11h30-12h15 (45') | Lecture — Œuvre suivie (commun) | **CM1** : Lecture, compréhension de textes · **CM2** : Histoire ou Géographie | **CM1** : Production d'écrits, projet d'écriture · **CM2** : Histoire ou Géographie | Lecture fluence (30') |
| 12h15-12h30 (15') | Dictée du jour | Dictée du jour | Dictée du jour | Dictée bilan / Poésie (30', enchaîné avec la fluence sur 11h30-12h30) |
| 12h30-14h00 | Pause méridienne | — | — | — |
| 14h00-14h15 | Lecture offerte / lecture personnelle (15 min quotidiennes) puis mise au travail | idem | idem | idem |
| 14h15-15h00 (45') | Sciences et technologie | **CM1** : Histoire ou Géographie · **CM2** : Lecture | Arts plastiques / Éducation musicale | EMC |
| 15h00-15h45 (45') | Anglais | Ateliers problèmes | **CM1** : Histoire ou Géographie · **CM2** : Production d'écrits | Sciences et technologie |
| 15h45-16h30 (45') | Arts plastiques / Éducation musicale | Anglais | EPS | EPS |

**Alternances à paramétrer** (choix par défaut à valider avec l'utilisatrice, modifiable dans l'app) :
- « Histoire ou Géographie » (2 créneaux/semaine/niveau) : rotation histoire/géographie, par défaut alternance hebdomadaire.
- « Arts plastiques / Éducation musicale » (2 créneaux/semaine) : par défaut un créneau arts plastiques + un créneau éducation musicale par semaine.
- **Les horaires et durées de l'EDT font foi**, y compris quand une méthodo indique d'autres durées (ex. maths §4.3).

### 4.2 Calendrier 2026-2027 — zone C (vérifié : arrêté du 22/10/2025, Légifrance JORFTEXT000052416058)

- Prérentrée enseignante : lundi 31/08/2026. **Rentrée élèves : mardi 01/09/2026.**
- **P1** : mar 01/09 → ven 16/10/2026 (7 semaines, S1…S7 ; S1 sans lundi) · Vacances de la Toussaint 17/10 → 02/11/2026
- **P2** : lun 02/11 → ven 18/12/2026 (7 semaines, S8…S14) · Vacances de Noël 19/12/2026 → 04/01/2027
- **P3** : lun 04/01 → ven 05/02/2027 (5 semaines, S15…S19) · Vacances d'hiver (C) 06/02 → 22/02/2027
- **P4** : lun 22/02 → ven 02/04/2027 (6 semaines, S20…S25) · Vacances de printemps (C) 03/04 → 19/04/2027
- **P5** : lun 19/04 → ven 02/07/2027 (11 semaines, S26…S36) · Été à partir du 03/07/2027

Jours chômés tombant sur des jours de classe :
- Lundi de Pâques : **lundi 29/03/2027** (P4-S6)
- Ascension + pont : **jeudi 06/05 et vendredi 07/05/2027** (P5-S3)
- Lundi de Pentecôte : **lundi 17/05/2027** (P5-S5)
- (11/11/2026 tombe un mercredi ; 01/05 et 08/05/2027 tombent des samedis — sans effet.)

Total : **36 semaines de classe** pour 35 séquences de maths (1/semaine) → 1 semaine de marge (dernière semaine = révisions/bilans/fin des œuvres). Le générateur (Phase 3) doit vérifier ces comptes par le calcul, pas les supposer.

### 4.3 Méthodo mathématiques (35 séquences/an, 1 notion nouvelle par semaine)

Structure hebdomadaire de la méthodo (indicative — les créneaux réels sont ceux de l'EDT) : 4 séances de séquence (lun/mar/jeu/ven, sur les créneaux « Mathématiques »), calcul mental quotidien, ateliers problèmes (créneau du mardi 15h00 dans l'EDT), Flash Maths 5' réparties dans la journée (rituel, pas un créneau propre).

**CM1 :**

| Période | Séquences |
|---|---|
| P1 | 1 Nombres jusqu'à 9999 · 2 Fractions-1 · 3 Aires-1 · 4 Fractions-2 · 5 Algèbre-1 · 6 Fractions-3 · 7 Droites perpendiculaires |
| P2 | 8 Fractions décimales-1 · 9 Fractions décimales-2 · 10 Nombres décimaux-1 · 11 Nombres jusqu'à 999 999 · 12 Addition et soustraction de nombres décimaux · 13 Multiplication : calcul posé-1 · 14 Droites parallèles |
| P3 | 15 Nombres décimaux-2 · 16 Algèbre-2 · 17 Division-1 · 18 Division-2 · 19 Proportionnalité · 20 Longueurs |
| P4 | 21 Nombres décimaux-3 · 22 Probabilités · 23 Cercle et disque · 24 Périmètres · 25 Multiplication : calcul posé-2 · 26 Triangles · 27 Aires-2 |
| P5 | 28 Quadrilatères · 29 Reproduction de figures · 30 Durées · 31 Construction de figures · 32 Axes de symétrie · 33 Masses et contenances · 34 Solides · 35 Angles |

**CM2 :**

| Période | Séquences |
|---|---|
| P1 | 1 Nombres jusqu'à 999 999 · 2 Aires-1 · 3 Fractions-1 · 4 Fractions-2 · 5 Algèbre-1 · 6 Fractions décimales · 7 Nombres décimaux-1 |
| P2 | 8 Multiplication posée de deux nombres entiers · 9 Nombres décimaux-2 · 10 Division euclidienne · 11 Droites perpendiculaires · 12 Proportionnalité · 13 Multiplication et division par 10, 100, 1 000 · 14 Multiplication posée d'un nombre décimal par un nombre entier |
| P3 | 15 Multiples et diviseurs · 16 Algèbre-2 · 17 Division décimale · 18 Probabilités-1 · 19 Nombres jusqu'à 999 999 999 · 20 Droites parallèles |
| P4 | 21 Nombres décimaux-3 · 22 Probabilités-2 · 23 Cercle et disque · 24 Aires-2 · 25 Durées · 26 Triangles · 27 Angles |
| P5 | 28 Quadrilatères · 29 Reproduction de figures · 30 Nombres décimaux-4 · 31 Aires-3 · 32 Construction de figures · 33 Algèbre-3 · 34 Axes de symétrie · 35 Solides · (+ Initiation à la pensée informatique) |

Note : les nombres de séquences par période (7/7/6/7/8) ne coïncident pas exactement avec les semaines des périodes 2026-2027 (7/7/5/6/11). Le générateur (Phase 3) déroule les 35 séquences **dans l'ordre, une par semaine de classe**, sans trou ; le rattachement à la période suit le calendrier réel, pas le découpage du manuel.

### 4.4 Méthodo grammaire-conjugaison (RETZ) — créneaux « Étude de la langue » Grammaire (lundi) et Conjugaison (mardi)

**CM1 — 21 séquences** (objectifs détaillés dans le PDF, à extraire en Phase 2) :
1 Les groupes dans la phrase · 2 Le groupe sujet · 3 La forme négative · 4 Le verbe (formes conjuguées, infinitif, variations) · 5 Le présent des verbes en ER, être et avoir · 6 Le présent des autres verbes fréquents · 7 La ponctuation dans la phrase · 8 Les constituants du groupe nominal simple · 9 Le passé composé avec avoir · 10 Le passé composé avec être · 11 Les phrases interrogatives · 12 L'adjectif qualificatif épithète · 13 Le complément circonstanciel · 14 L'imparfait · 15 Le complément d'objet · 16 La forme exclamative · 17 Le futur · 18 Les phrases impératives · 19 Les adverbes · 20 Le complément du nom *(bonus)* · 21 Le passé simple des verbes à la 3ᵉ personne *(bonus)*

**CM2 — 21 séquences** :
1 Les groupes dans la phrase · 2 Le groupe sujet · 3 Le verbe (formes conjuguées, infinitif, variations) · 4 Le présent · 5 Les constituants du groupe nominal (GN) simple · 6 Le passé composé · 7 L'adjectif qualificatif épithète · 8 Le complément circonstanciel · 9 L'imparfait · 10 Le complément d'objet · 11 Le futur · 12 Le complément du nom · 13 Les phrases injonctives · 14 L'attribut du sujet · 15 Le passé simple · 16 Les pronoms de reprise · 17 Les phrases complexes · 18 Le plus-que-parfait · 19 Le groupe nominal (GN) enrichi · 20 L'impératif *(bonus)* · 21 La proposition subordonnée relative *(bonus)*

Conseil RETZ : ne démarrer l'étude systématique de la conjugaison qu'après les notions de verbe et de sujet. Répartition sur l'année à construire en Phase 3 (≈ 1 séquence toutes les 1,5 à 2 semaines, bonus en fin d'année si le temps le permet).

### 4.5 Littérature (« The Littérature », S. Hanot) — créneau « Lecture — Œuvre suivie » (lundi 11h30) + compréhension/fluence

| Période | Thème | Œuvre(s) |
|---|---|---|
| P1 | Thème 1 — Héros et héroïnes | **Charlie et la chocolaterie** (planning 7 semaines dans le PDF) · Hansel et Gretel (repli en P5 si manque de temps) |
| P2 | Thème 2 — La morale en question | **Contes de Perrault** |
| P3 | Thème 4 — Vivre des aventures | **Émilie et le crayon magique** · **Sherlock Holmes** |
| P4 | Thème 6 — Se découvrir, s'affirmer dans le rapport aux autres | **Le Magicien d'Oz** |
| P5 | Thème 3 — Se confronter au merveilleux, à l'étrange | **Jumanji** · **Zathura** |

Le détail semaine par semaine de chaque œuvre est dans `outil-pedagogique-litterature-par-semaine.pdf` (extraction en Phase 2).

---

## 5. Modèle de données cible (SQLModel / PostgreSQL)

Directive générale : suivre le pattern de `core/src/core/models/user.py` (UUID PK `gen_random_uuid()`, `created_at`/`updated_at` server-side). Noms indicatifs — les affiner est permis, les simplifier en perdant une capacité ne l'est pas.

- **`subjects`** — matières (Français, Mathématiques, Histoire, Géographie, Sciences et technologie, EMC, EVAR, Anglais, Arts plastiques, Éducation musicale, EPS, Poésie…), avec couleur d'affichage.
- **`domains`** — domaines par matière et niveau (ex. Maths → Nombres, Calcul mental, Grandeurs et mesures… ; Français → Grammaire, Conjugaison, Orthographe, Vocabulaire, Lecture, Écriture, Oral…).
- **`program_items`** — items des programmes officiels : niveau (CM1/CM2), matière, domaine, intitulé, description/attendus, référence source (fichier + page). Colonne générée `tsvector` (config `french`) sur intitulé+description, index GIN → recherche plein-texte.
- **`sequences`** — séquences des méthodos : méthodo (maths-cm1, maths-cm2, retz-cm1, retz-cm2, litterature…), niveau, numéro, titre, objectifs, période indicative.
- **`sequence_sessions`** — gabarit des séances d'une séquence (n° de séance, titre/contenu, durée indicative, matériel) quand la méthodo le détaille (littérature par semaine, RETZ).
- **`periods`** — P1…P5 : bornes, libellé.
- **`weeks`** — semaines de classe : numéro global (1…36), numéro dans la période, période, dates lundi→vendredi.
- **`school_days`** — jours de classe : date, semaine, jour de la semaine, flag `is_off` + motif (férié/pont) pour les exceptions.
- **`timetable_slots`** — gabarit EDT (§4.1) : jour de semaine, heure début/fin, discipline (matière+domaine), niveau (`CM1`/`CM2`/`commun`), flag alternance et groupe d'alternance.
- **`planned_sessions`** — séances planifiées : jour (`school_days`), créneau (`timetable_slots`), niveau, séquence et/ou item(s) de programme liés, titre, objectifs/compétences, matériel, statut (`planifiée`/`faite`/`reportée`/`annulée`), ordre dans la journée.
- **`journal_entries`** — lignes du cahier journal d'un jour : référence facultative à la séance planifiée, discipline, durée, objectifs & compétences, **bilan**, notes, ordre. (Créées depuis les `planned_sessions` du jour, puis vivent leur vie : modifiables, réordonnables, supprimables, ajoutables.)
- **`journal_revisions`** — journal des révisions IA : jour, feedback utilisateur, proposition (snapshot avant/après JSON), statut (`proposée`/`appliquée`/`rejetée`), modèle utilisé, horodatage.
- **`app_settings`** — paramètres clé/valeur (choix des alternances, modèle IA, etc.).

Migrations Alembic obligatoires pour tout changement de schéma (`make db-migrate MSG="..."`). **Chaque nouveau modèle doit être importé dans `core/src/core/models/__init__.py`** (sinon l'autogenerate ne le voit pas).

---

## 6. Architecture technique

Respecter `CLAUDE.md` et les patterns existants du monorepo. Points spécifiques :

**Backend (`core/`)**
- Routers FastAPI par ressource dans `core/src/core/routers/` (pattern de `health.py`), enregistrés dans `main.py` avec un préfixe `/api`.
- Logique métier dans `core/src/core/services/` (génération de programmation, service Anthropic, seed loader).
- Recherche plein-texte : PostgreSQL `tsvector`/`websearch_to_tsquery` (config `french`) — pas de dépendance externe.
- IA : SDK `anthropic` (dépendance de `core`), settings `anthropic_api_key: str` + `anthropic_model: str` (défaut `"claude-sonnet-5"`). Appels avec sortie structurée (tool use / JSON schema) — jamais de parsing de texte libre.
- Pas d'auth : ne pas utiliser `get_current_user` ; ne pas ajouter de router login.

**Frontend (`webapp/`)**
- TanStack Router **code-based** dans `main.tsx` (pattern existant), TanStack Query pour tout accès API, Tailwind v4, `lucide-react` pour les icônes.
- Client API minimal typé dans `webapp/src/lib/api.ts` (fetch + zod), URLs relatives `/api/...`.
- **Proxy Vite** : `server.proxy` `{ "/api": "http://core:80" }` dans `vite.config.ts` → pas de CORS, pas d'URL absolue.
- UI en **français**, dates au format français (lundi 7 septembre 2026). Pas de lib de dates lourde : `Intl.DateTimeFormat` + helpers maison suffisent.

**Infra**
- Docker Compose existant (webapp :12108, core :12109, adminer :12107). `make up`, migrations auto au démarrage (lifespan).
- Seeds versionnés dans le repo (`core/seed/*.json`) + loader idempotent (upsert par clé naturelle) exécutable via `make seed` (nouvelle target) — la DB peut être reconstruite from scratch : `make down && make up && make seed`.

---

## 7. Écrans & UX

Interface simple, claire, dense en information mais apaisée — c'est un outil de travail quotidien. Sidebar de navigation persistante (Année · Semaine · Aujourd'hui · Programmes · Réglages). « Aujourd'hui » est la page d'accueil.

1. **Vue Année** — les 5 périodes en colonnes/cartes, semaines cliquables, vacances visibles, indicateur d'avancement (semaine courante).
2. **Vue Semaine** — la grille EDT (§4.1) remplie avec les séances planifiées de la semaine ; code couleur par matière ; badges CM1/CM2 sur les créneaux splittés ; navigation semaine précédente/suivante ; clic sur un jour → vue Jour.
3. **Vue Jour / Cahier journal** — cœur de l'app : lignes ordonnées (discipline-durée, objectifs & compétences, bilan) pré-remplies depuis la programmation ; édition inline, réordonnancement, ajout/suppression de lignes ; statut des séances ; **vue imprimable** (CSS print, format proche de l'exemple PDF) ; panneau **Feedback IA** (voir Phase 7).
4. **Navigateur de programmes** — liste filtrable (niveau, matière, domaine) + recherche plein-texte par mots-clés ; fiche item avec référence source ; lien « voir les séances liées ».
5. **Génération** (dans Réglages) — lancer/relancer la génération de la programmation (année complète ou une période), avec récapitulatif des règles appliquées et rapport de validation ; confirmation explicite avant d'écraser une période déjà entamée (les jours passés et les cahiers journaux ne sont jamais écrasés).

---

## 8. Phases de développement

Règles communes à toutes les phases :
- Lire ce document en entier avant de commencer. Ne traiter que la phase demandée.
- Terminer par : `make check` vert, tests de la phase verts (`make test-core` / `make test-webapp`), critères d'acceptation vérifiés un par un, commit(s) conventionnel(s), et un court rapport (fait / non fait / ambiguïtés rencontrées).
- En cas de blocage ou d'ambiguïté matérielle : poser la question plutôt que d'inventer.

### Phase 0 — Fondations & câblage
**Objectif** : un monorepo qui démarre proprement de zéro et où tout le pipeline (webapp → API → DB, tests, migrations) fonctionne.
- Ajouter `pytest` (+ `pytest-asyncio`) aux dépendances de `core` ; vérifier `make test-core`.
- Corriger `core/src/core/models/__init__.py` : importer `User` (et tout futur modèle) pour l'autogenerate Alembic ; générer la migration initiale `users` ; `make db-upgrade` OK.
- `settings.py` : donner des valeurs par défaut aux champs JWT/cookie (app sans login) pour que l'app boote avec un `.env` minimal ; ajouter `anthropic_api_key` (défaut vide) et `anthropic_model` (défaut `claude-sonnet-5`) ; mettre à jour `env.example`.
- Préfixe `/api` sur les routers ; proxy Vite `/api` → `http://core:80` ; supprimer la dépendance au LAN IP pour le dev local.
- Ajouter la dépendance `anthropic` à `core` (service branché en Phase 7).
- Smoke test : `make up`, webapp affiche une page qui appelle `GET /api/health` avec succès via le proxy.
**Acceptation** : `make up && make test-core && make test-webapp && make check` tout vert sur un clone frais ; `/api/health` visible depuis la webapp.

### Phase 1 — Modèle de données, migrations, seed structurel
**Objectif** : le squelette de l'année en base.
- Créer les modèles §5 (+ imports dans `models/__init__.py`), migration(s) Alembic.
- Seeds JSON versionnés + loader idempotent (`make seed`) pour : matières & domaines, gabarit EDT complet (§4.1, avec flags d'alternance), calendrier 2026-2027 zone C (périodes, 36 semaines, jours de classe avec fériés/pont §4.2).
- Tests : nombre de semaines par période (7/7/5/6/11), jours off corrects (29/03, 06-07/05, 17/05), aucun mercredi, S1 commence le mardi 01/09/2026.
**Acceptation** : `make seed` idempotent (double exécution = même état) ; tests calendrier verts ; Adminer montre les tables peuplées.

### Phase 2 — Extraction des contenus pédagogiques (PDFs → seeds)
**Objectif** : tout le contenu pédagogique en base, sourcé, cherchable.
- Extraire vers `core/seed/` (JSON) puis charger en DB :
  - `programme-cm1-cm2.pdf` (154 p., tranches ≤ 20 p.) → `program_items` par niveau/matière/domaine, avec référence de page ;
  - `outil-pedagogique-litterature-par-semaine.pdf` (35 p., scans photo) → `sequences` + `sequence_sessions` par œuvre et par semaine ;
  - objectifs détaillés RETZ CM1 (et sommaire CM2) → `sequences` ;
  - séquences maths §4.3 → `sequences` (les listes de ce document font foi).
- Ce travail se prête à une **parallélisation par sous-agents** (un par document ou par tranche) avec relecture croisée : chaque fichier seed est relu contre le PDF source avant intégration.
- Marquer `"needs_review": true` sur tout item incertain/illisible et lister ces items dans le rapport.
**Acceptation** : comptes attendus vérifiés (35 séquences maths × 2 niveaux ; 21 RETZ × 2 ; œuvres §4.5 toutes présentes) ; recherche plein-texte opérationnelle en SQL ; zéro contenu inventé (spot-check de 10 items contre les PDFs).

### Phase 3 — Génération de la programmation annuelle
**Objectif** : les ~139 jours de classe (36 semaines × 4 jours, moins le lundi de la S1 et les 4 jours fériés/pont) remplis de séances conformes à l'EDT.
- Service Python déterministe (pas d'IA) : pour chaque jour de classe et chaque créneau de l'EDT, créer la `planned_session` adéquate :
  - maths : séquences dans l'ordre, 1/semaine/niveau, réparties sur les 4 créneaux maths + ateliers problèmes ;
  - étude de la langue : progression RETZ (grammaire lundi, conjugaison mardi), orthographe/vocabulaire génériques rattachés aux programmes ;
  - littérature : œuvres par période (§4.5), séances hebdo depuis `sequence_sessions` (Charlie = 7 semaines de P1…) ;
  - histoire/géo, arts/musique : appliquer les alternances paramétrées ;
  - autres créneaux (EMC, sciences, anglais, EPS, poésie, rituels…) : séances génériques liées aux items de programme correspondants.
- Rapport de validation intégré : couverture des 35 séquences × 2, aucune séance hors créneau/jour off, chaque créneau de chaque jour couvert, alternances équilibrées.
- Génération relançable par période ; ne touche jamais aux jours passés ni aux cahiers journaux existants.
**Acceptation** : génération complète < 1 min ; rapport de validation sans erreur ; échantillon manuel (P1-S1 complet + une semaine de P3) conforme EDT + méthodos.

### Phase 4 — API backend
**Objectif** : tout le nécessaire pour le front, en CRUD propre.
- Endpoints (préfixe `/api`) : calendrier (année/périodes/semaines/jours), semaine détaillée (séances par créneau), jour détaillé, CRUD `planned_sessions`, CRUD `journal_entries` (+ initialisation du cahier journal d'un jour depuis ses séances, + réordonnancement), programmes (liste filtrée + recherche `?q=`), génération (lancement + rapport), settings.
- Schémas Pydantic de réponse dédiés (pattern `health.py`) ; tests pytest par router (TestClient + DB de test).
**Acceptation** : OpenAPI (`/docs`) complet et cohérent ; tests verts ; scénario curl documenté dans le rapport (naviguer une semaine, éditer un cahier journal).

### Phase 5 — Frontend : navigation & programmes
**Objectif** : écrans 1, 2 et 4 de §7 (Année, Semaine, Programmes) + squelette layout/sidebar.
- Routes TanStack Router code-based (pattern `main.tsx`), TanStack Query, client API typé.
- Grille EDT fidèle au §4.1 (colonnes lun/mar/jeu/ven, lignes horaires, splits CM1/CM2, couleurs par matière).
- Navigateur de programmes : filtres niveau/matière/domaine + recherche.
**Acceptation** : parcours année → période → semaine fluide ; semaine courante par défaut ; recherche « fractions » renvoie les items attendus ; `make check` + `make test-webapp` verts.

### Phase 6 — Cahier journal
**Objectif** : écran 3 de §7, le quotidien de l'enseignante.
- Vue Jour : cahier journal pré-initialisé depuis les séances du jour (à la première ouverture), édition inline (discipline, durée, objectifs, bilan, notes), réordonnancement (drag & drop ou boutons), ajout/suppression, statuts.
- Vue imprimable (CSS print) au format de l'exemple (`Période X – Semaine Y`, date, tableau 3 colonnes).
- « Aujourd'hui » comme page d'accueil (redirige vers le prochain jour de classe si férié/week-end).
**Acceptation** : cycle complet sur un jour de démo : ouvrir → éditer → bilan → imprimer ; les modifications persistent en DB ; le cahier journal reste intact après régénération de la programmation.

### Phase 7 — Feedback IA
**Objectif** : la boucle de feedback qui modifie le cahier journal à la volée.
- Service `core/src/core/services/ai_feedback.py` : entrée = jour + feedback libre de l'enseignante + contexte (cahier journal actuel, séances planifiées du jour et des jours suivants de la semaine, EDT) ; sortie **structurée** (tool use / JSON schema) = liste d'opérations sur les `journal_entries` (modifier/ajouter/supprimer/réordonner) + résumé en français + suggestions éventuelles pour les jours suivants (proposées, jamais appliquées automatiquement).
- Endpoint `POST /api/journal/{date}/feedback` → crée une `journal_revision` `proposée` ; endpoints appliquer/rejeter.
- UI : panneau feedback dans la vue Jour — saisie du feedback, affichage de la proposition en **diff** (avant/après par ligne), boutons Appliquer / Rejeter ; historique des révisions du jour.
- Gestion des erreurs : clé absente → fonctionnalité désactivée proprement avec message ; timeout/erreur API → l'édition manuelle reste toujours disponible.
**Acceptation** : scénario réel : « la séance de grammaire a débordé, je n'ai pas fait la géographie, décale-la » → proposition cohérente, diff lisible, application correcte, révision tracée en DB ; aucun appel IA sans action explicite de l'utilisatrice.

### Phase 8 — Finitions
**Objectif** : prêt pour la rentrée.
- Tests E2E des parcours clés (au minimum via tests d'intégration API + composants critiques).
- Polish UI : états vides, chargements, erreurs, responsive raisonnable, impression soignée.
- Doc utilisatrice `README-UTILISATRICE.md` en français simple : démarrer l'app (`make up`), les 5 écrans, le feedback IA, quoi faire si ça ne démarre pas.
- Revue finale de cohérence données : spot-check programmation vs PDFs, comptes de séquences, semaine type vs EDT.
**Acceptation** : `make down && make up && make seed` puis démo complète des 5 fonctionnalités du §1 sans accroc.

---

## 9. Skills à utiliser

**Skills du repo** (déjà installés, voir `.claude/skills/`) : `/migrate` (migrations Alembic), `/new-endpoint`, `/new-route`, `/new-component` (scaffolding conforme aux patterns), `/check` et `/fix-lint` (qualité), `/test`, `/logs`, `/db`, `/docker`.

**Skills mattpocock** (https://github.com/mattpocock/skills — installer une fois : `claude plugins install mattpocock-skills`, puis `/setup-matt-pocock-skills`) :

| Skill | Quand |
|---|---|
| `domain-modeling` / `grill-with-docs` | Phase 1 : verrouiller le vocabulaire métier (§2) et le modèle de données avant de coder |
| `to-tickets` | Découper une phase en tickets « tracer bullet » si elle est trop grosse pour une session |
| `implement` + `tdd` | Exécution des phases 3 à 7 (logique métier : génération, API, feedback IA) |
| `code-review` | Fin de chaque phase, avant commit final |
| `diagnosing-bugs` | Tout bug non trivial (surtout génération/calendrier) |
| `handoff` | Passage de relais entre deux sessions d'agents sur une même phase |

---

## 10. Conventions & garde-fous

- **Commits conventionnels** (`feat(scope): …`), enforced par commitlint. Une phase = une ou plusieurs PR/commits cohérents.
- **`make check` vert obligatoire** avant tout commit ; tests de la phase verts.
- **UI et contenus en français** ; code, identifiants et messages de commit en anglais.
- **Pas d'auth, une seule utilisatrice** — ne pas ajouter de login, de rôles, de multi-tenancy.
- **Persistance : DB uniquement.** Les seeds JSON sont la source de vérité versionnée du contenu extrait ; la DB se reconstruit intégralement par `make seed`.
- **L'EDT (§4.1) est immuable** sauf demande explicite de l'utilisateur. Toute impossibilité de placement se signale, ne se contourne pas.
- **Ne jamais inventer de contenu pédagogique** : tout provient des PDFs (§3) ou des données embarquées (§4). Le douteux est marqué `needs_review`.
- **Les cahiers journaux et les jours passés ne sont jamais écrasés** par une régénération.
- **Aucun appel IA implicite** : l'API Anthropic n'est appelée que sur action explicite (bouton feedback).
- En cas de contradiction entre ce document et un PDF source sur du contenu pédagogique : le PDF fait foi ; le signaler pour correction du document.
