# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

This is a **single-context** repo: one glossary and one ADR directory, both at the root.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root: the domain glossary.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.

If these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-weekly-programme-as-the-planning-unit.md
│   └── 0002-postgres-for-the-write-model.md
├── core/                 ← FastAPI backend
└── webapp/               ← React SPA
```

Note that `docs/` also holds the project's source PDFs (curriculum, timetables, pedagogical tools). ADRs live in the `docs/adr/` subdirectory and don't mix with those.

If this repo ever grows into genuinely separate bounded contexts, switch to the multi-context layout: a root `CONTEXT-MAP.md` pointing at one `CONTEXT.md` per context, with context-scoped `docs/adr/` directories alongside them. Until then, keep it single-context.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders), but worth reopening because…_
