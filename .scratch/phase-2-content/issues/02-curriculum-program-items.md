# 02 - Extract the official curriculum into `program_items`

Status: resolved
Blocked by: 01

`docs/programme-cm1-cm2.pdf` → `core/seed/program_items.json`.

- Pages 5-89 and 108-154 have a text layer: extract with a script committed to
  `scripts/` so the seed is reproducible and reviewable against the PDF.
- Pages 90-107 (sciences et technologie) are images: transcribe in vision, verbatim.
- Keep CM1 and CM2 (and cycle-3-wide blocks as `commun`); drop everything marked
  `Sixième` and every level below CM1.
- Every item carries `source_file` and `source_page`.
- Anything illegible or ambiguous gets `"needs_review": true` and goes in the report.

New domaines are added to `core/seed/subjects.json` from the programmes' own section
headings. The 13 existing codes keep their meaning.

**Done when**: a pure seed-file test asserts the per-niveau/matière breakdown and that
`(level, subject, domain, title)` is unique across the file.
