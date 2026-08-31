# Phase 3 — rapport de fin de phase

## Fait

- **`planned_sessions` a une clé naturelle** `(school_day_id, timetable_slot_id, level)`,
  migration Alembic, montée et redescendue (ADR-0009).
- **Les deux alternances vivent dans `app_settings`**, avec les défauts du §4.1, et un
  `make seed` ne les écrase jamais — un test le vérifie en changeant la valeur à la main
  (ADR-0013).
- **Un planificateur déterministe et sans base** (`core/services/planning/`) : il lit des
  dataclasses gelées et rend des brouillons de séance plus un rapport. Deux constructeurs
  le remplissent — les seeds versionnés et la base — et un test en base prouve qu'ils
  donnent le même plan. C'est ce qui rend les règles de placement vérifiables en CI.
- **1740 séances**, une par couple (jour de classe, créneau, niveau) : les 1532 couples de
  la grille plus les 208 créneaux dédoublés par niveau (ADR-0010). Aucune séance sur un
  jour chômé, aucun créneau d'un jour travaillé laissé vide.
- **4040 rattachements** aux items de programme, jamais d'une autre matière que celle de
  la séance.
- **35 × 2 séquences de maths** placées dans l'ordre, une par semaine, quatre séances par
  semaine sur les créneaux « Mathématiques » (ADR-0011).
- **21 × 2 séquences RETZ** placées : grammaire le lundi, conjugaison le mardi, la
  conjugaison n'ouvrant qu'après la séquence « Le verbe » (ADR-0012).
- **33 des 36 semaines d'œuvres** placées sur le créneau « Lecture — Œuvre suivie »
  (ADR-0017).
- **Histoire et géographie alternent semaine par semaine**, chaque niveau, et leurs thèmes
  se placent d'après les périodes que leurs intitulés nomment (ADR-0016). Arts plastiques
  le lundi, éducation musicale le jeudi.
- **Le reste des créneaux parcourt le programme de sa matière** au fil de l'année ; un
  rituel (≤ 20 minutes) garde le sien en entier (ADR-0015).
- **Poésie** partage le créneau du vendredi 12h00 avec la dictée bilan (ADR-0014).
- **Régénération relançable**, par année ou par période, idempotente sur la clé naturelle,
  qui ne touche jamais un jour passé ni un jour déjà tenu au cahier journal.
- **Neuf ADR** (0009…0017), `CONTEXT.md` complété (programmation, rituel, progression,
  marge, repli, rapport de validation), `CLAUDE.md` remis à jour.

## Critères d'acceptation (§8 Phase 3)

| Critère | Résultat |
|---|---|
| Génération complète < 1 min | **0,5 s** depuis une base vide |
| Rapport de validation sans erreur | **aucune erreur** — 11 lignes « calendrier », 1 ligne « source » |
| Échantillon manuel P1-S1 + une semaine de P3 | relu en base contre le §4.1, conforme |
| `make check` | vert |
| `make test` | 132 tests verts en conteneur ; 113 + 17 skips sur le chemin CI |
| `make seed` idempotent depuis une base vide | vérifié après `docker compose down -v` |

## Deux colonnes ajoutées, qu'aucun ticket ne demandait

- `program_items.source_order` : une progression parcourt le programme dans l'ordre de la
  source, et une clé primaire en `gen_random_uuid()` ne peut pas porter cet ordre. Sans
  elle, l'année générée changeait à chaque reconstruction.
- `planned_sessions.content` : le planning hebdomadaire d'une œuvre est une page
  d'activités, pas un objectif.

## Non fait (et pourquoi)

- **Le créneau « Ateliers problèmes » ne porte pas la séquence de la semaine.** Le §8
  résume la règle par « réparties sur les 4 créneaux maths + ateliers problèmes » ; le
  §4.3, qui est la méthodo, les liste séparément. Le créneau porte donc « La résolution de
  problèmes » du programme (ADR-0011).
- **« Zathura » n'est pas placée** : la source ne lui donne aucun planning hebdomadaire.
- **« Hansel et Gretel » n'est pas lue** : c'est le repli que le §4.5 garde en réserve, et
  l'année manque de créneaux.
- **Aucun router, aucun endpoint** : c'est la Phase 4.

## Ambiguïtés rencontrées

1. **L'EDT nomme un domaine à chaque créneau de maths ; la méthodo n'en nomme aucun.** Une
   séquence « Droites perpendiculaires » tombe donc dans la cellule « Mathématiques —
   Nombres » certaines semaines. La tension est celle des deux sources ; l'EDT est
   immuable, le domaine reste la position dans la grille (ADR-0011).
2. **Le §4.4 annonce « ≈ 1 séquence toutes les 1,5 à 2 semaines »**, ce qui suppose deux
   séances hebdomadaires par progression. L'EDT n'en donne qu'une par domaine, et le §4.1
   dit que l'EDT fait foi : une séquence de conjugaison dure donc environ quatre semaines
   (ADR-0012).
3. **Le §4.5 mentionne « compréhension/fluence » à côté du créneau œuvre suivie** sans
   donner de contenu hebdomadaire pour ces créneaux. Ils parcourent le programme de
   lecture.
4. **Le rythme d'une progression est le nôtre.** La source donne un ordre, jamais une
   durée ; le générateur découpe les créneaux de l'année en parts égales.
5. **Six notions RETZ CM2 n'existent pas au CM1** et ne sont donc classées en grammaire ou
   en conjugaison par personne d'autre que nous (ADR-0012).
6. **Le sens de la rotation histoire/géographie et le jour d'arts plastiques** ne sont dits
   nulle part ; ce sont des réglages, modifiables (ADR-0013).

## Pour la Phase 4

- `generate_year(session, reference_date=…, periods=…)` et `GenerationReport` sont prêts à
  être exposés ; `report.is_clean` est le critère « sans erreur » et `report.errors` la
  liste à montrer en rouge.
- L'écran Réglages du §7 doit écrire `app_settings` puis relancer la génération : changer
  une alternance ne change rien tant que l'année n'est pas régénérée.
- Le gel des jours passés est déjà dans le code, pas seulement dans les tests : la Phase 6
  n'a rien à ajouter pour que les cahiers journaux survivent à une régénération.
