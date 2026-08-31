# Phase 2 — Extraction des contenus pédagogiques (PDFs → seeds)

MASTER-PROMPT.md §8 Phase 2. Fills the three tables Phase 1 left empty:
`program_items`, `sequences`, `sequence_sessions`.

## Sources and how each is read

| Source | Pages | Text layer? | Method |
|---|---|---|---|
| `docs/programme-cm1-cm2.pdf` p5-89, p108-154 | 111 | yes | deterministic script over `pdftotext -layout` |
| `docs/programme-cm1-cm2.pdf` p90-107 (Sciences et technologie) | 18 | **no** (images) | vision, verbatim transcription |
| `docs/outil-pedagogique-maths-cm1/cm2.pdf` | 1+1 | yes | §4.3 lists are authoritative, PDF confirms |
| `docs/outil-pedagogique-grammaire-conjugaison.pdf` | 3 | **no** (scans) | vision, verbatim transcription |
| `docs/outil-pedagogique-litterature-annee.pdf` | 5 | yes | thème → période → œuvres (§4.5 cross-check) |
| `docs/outil-pedagogique-litterature-par-semaine.pdf` | 35 | **no** (photo scans) | vision, verbatim transcription |

## Decisions taken before coding

1. **`program_items` natural key** = `(level, subject_id, domain_id, title)`, as a
   `NULLS NOT DISTINCT` unique constraint (Postgres 17, SQLAlchemy 2.0). Alembic
   migration required — without it `make seed` duplicates every item on each run.
   `(level, subject_id, title)` was rejected: the langues-vivantes programme lists
   *Raconter* under both « Expression orale en continu » and « Expression écrite »
   for the same niveau, so the domaine is part of the identity.
2. **A `program_item` is one « Objectifs d'apprentissage » block of the PDF**:
   `title` = the heading the block hangs under, `description` = the objectives it
   lists, both verbatim. This is the unit the source itself uses across français,
   mathématiques, langues vivantes, EPS, sciences et histoire-géographie.
3. **`domains` come from the PDF's own section headings**, mapped through an explicit
   table (`scripts/curriculum_map.py`) onto the 13 domaines Phase 1 seeded plus the
   new ones each programme needs. The 13 existing codes are never renamed or dropped.
4. **Literature `method` = `litterature`, numbers 1…8** — one séquence per œuvre of
   §4.5, in période order; the weekly planning of an œuvre becomes its
   `sequence_sessions`. Per-œuvre methods were rejected because the model already has
   a place for "the séances a méthodo lays out", and a continuous numbering across
   œuvres would be ours rather than the source's.
5. **`sequences.level` = `commun`** for the literature œuvres (the créneau « Lecture —
   Œuvre suivie » is commun), `CM1`/`CM2` for maths and RETZ.
6. **`sequences.period_code`** uses `periods.code` (`P1`…`P5`).

## Expected counts (recomputed, never assumed)

- `sequences`: 35 × 2 maths + 21 × 2 RETZ + 8 littérature = **120**, plus 36
  `sequence_sessions` (the weekly plannings of the seven œuvres the source details).
- `program_items`: not known in advance — it came out to **220**, reported per niveau/matière.
- Every count is asserted by a test that reads the **seed files**, so CI (no Postgres) checks it.

## Left needing review

None. The eight tables whose columns `pdftotext` could not separate were rendered with
`pdftoppm` and read back (`scripts/curriculum_corrections.json`); the three doubts on the
littérature plannings were settled with the teacher and with the page 92 the source PDF
was missing (`docs/page-92.heic`, `docs/page-70-semaine-3-etape-6-chap-7.HEIC`).

## Out of scope

Phase 3. No `planned_sessions`, no programmation, no alternance settings.
