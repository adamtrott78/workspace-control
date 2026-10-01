<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-new-unit-ingestion-hw2-prep.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-new-unit-ingestion-hw2-prep
- Title: MTH 602 new-unit ingestion and HW2 preparation
- Status: SUSPENDED
- Capsule schema: v2

## Goal

Bring MTH 602 course-content state current by visually synthesizing new classroom/whiteboard photographs and handwritten notes with the smallest relevant instructor material, persist durable session/topic knowledge without falsely promoting mastery, and bootstrap Homework 2 when authoritative assignment evidence is available.

## Workflow

- Repository: workspace-control
- Path: policies/OPERATOR_WORKFLOW.md
- Checkpoint: bc3966f10b8b07b9a27d8ec5275f218c209a7609

## Repositories

### MTH602-AdamTrott

- Intent: mutate
- Remote branch: unit-ingestion-hw2
- Remote checkpoint: 20dc641dcb9b505efe53daa52932521d0927ef3a
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: bc3966f10b8b07b9a27d8ec5275f218c209a7609
- Remote verified: true

## Next safe action

Do not begin HW2 Problem 1 while the course-workflows v2 migration is running. Preserve unit-ingestion-hw2 at the recorded pre-solution checkpoint until the migration executor takes ownership. After mth602-course-workflows-v2-migration completes on this same branch, deliberately refresh this capsule to the migrated checkpoint, restore hw2_bootstrap to active work, and then begin Floating-point Problem 1 using homework/hw02/CONTEXT.md, the 2026-09-21 floating-point lecture synthesis, and study/TUTORING.md.

## Remaining work

- Resume HW2 after the course-workflows v2 migration completes and this capsule is refreshed to the migrated branch checkpoint.
- Submit the completed Lab1 PDF/notebook through one of the instructor-approved channels; artifact production is complete but actual submission is a user action.
- Complete exact-byte transfer of the HW2 PDF/CSV/PNG source package into homework/hw02 and verify against assignment/manifest.json when a suitable binary transfer surface is available.
- Before Probability Problem 4, ingest the exact Bishop Problems 2.16 and 2.18 from the course textbook.
- Work HW2 one bounded problem at a time under the tutoring/mastery protocol, starting with Floating-point Problem 1.
- Build and visually validate the final reproducible HW2 report and separately verify actual submission.
- Complete exact-byte transfer of previously ingested classroom originals when a suitable binary transfer surface is available.
- Synchronize final task JSON/Markdown, establish HANDOFF_SAFE, and archive when the task's preparation/assignment boundary is complete.

## Blockers / gates

- Final cold-start completeness still requires exact binary transfer of hw2.pdf, hw2.csv, and the two instructor PNG reference assets into homework/hw02; current conversation can continue because those exact bytes are mounted and verified.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-new-unit-ingestion-hw2-prep.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
