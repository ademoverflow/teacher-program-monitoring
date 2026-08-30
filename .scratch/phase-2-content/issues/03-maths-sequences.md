# 03 - Seed the 70 maths séquences

Type: task
Status: resolved

§4.3 of MASTER-PROMPT.md is authoritative (it says so); `docs/outil-pedagogique-maths-cm1.pdf`
and `-cm2.pdf` are the cross-check. 35 séquences per niveau, `method` = `maths-cm1` /
`maths-cm2`, `number` 1…35, `period_code` = the période the manual puts the séquence in.

No `sequence_sessions`: the manual says "une suite de 4 séances" but never titles them,
and inventing four titles per séquence is exactly what §10 forbids.

**Done when**: a test reads `core/seed/sequences.json` and finds 35 + 35 with contiguous
numbering and the §4.3 titles.
