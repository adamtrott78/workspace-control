# Document-artifact build and QA procedure

## Purpose

Provide reusable mechanics for project-owned homework reports, cheat sheets,
resumes, technical memos, and similar artifacts.

workspace-control does not own the artifact's facts, semantic content, formatting
requirements, or submission rules.

## Required inputs

Recover the domain/content owner, source/generation owner, deterministic build and
render commands when applicable, expected final artifact, structural checks,
visual-QA criteria, delivery rules, and any explicitly authoritative human gate.

## Lifecycle

1. **Load domain contract.** Layout pressure must not silently rewrite facts or
   locked content.
2. **Prepare source.** Update project-owned source under its mutation authority.
3. **Build deterministically.** Process exit is execution evidence, not artifact
   completion evidence.
4. **Structural/static validation.** Check project-required freshness, format,
   page/file constraints, logs, extractable text, dimensions, privacy, and
   reproducibility.
5. **Render.** Produce the representation needed to inspect the final artifact.
6. **Visual QA.** Inspect clipping, overlap, legibility, density, figure
   placement, and other project criteria. Automated visual inspection is
   sufficient unless the owning workflow explicitly requires substantive human
   judgment.
7. **Bounded revision.** Change the layer that is actually wrong: content plan,
   production spec, or source/build implementation. Rebuild/revalidate only as
   needed.
8. **Delivery gate.** External upload/submission/send is a separate consequence
   gate when required; an internal artifact may need none.

A compiler/generator exit alone is never final validation evidence.
