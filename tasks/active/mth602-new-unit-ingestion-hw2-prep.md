<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-new-unit-ingestion-hw2-prep.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-new-unit-ingestion-hw2-prep
- Title: MTH 602 new-unit ingestion and HW2 preparation
- Status: CHECKPOINTED
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
- Remote checkpoint: dd664c785585e55c2dfe974f98050268fd343b97
- Remote verified: True

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: bc3966f10b8b07b9a27d8ec5275f218c209a7609
- Remote verified: True

## Next safe action

Accept the next lecture ZIP from the user. Treat it as the next provisional session label, inspect the actual images directly, recover date/order/overlap from image evidence and mathematical continuity, distinguish any notebook images as student-derived supplemental evidence, and do not use OCR/Mathpix unless direct vision proves insufficient. Persist the next session only after visual review. Do not begin HW2 bootstrap until the user has finished supplying the new-unit lecture batches or authoritative assignment evidence makes an earlier bootstrap independently safe.

## Remaining work

- Upload the remaining lecture ZIP batches; for each batch, visually establish date/order/overlap and synthesize the session without default OCR.
- When a batch contains notebook images, preserve them as student-derived supplemental evidence rather than direct professor-board evidence.
- Complete exact-byte transfer of classroom originals into each session source tree and verify them against the recorded SHA-256 manifests when a suitable binary transfer surface is available.
- Resolve exact current instructor-slide provenance/page slices where accessible and update only claims that stronger source evidence supports.
- After all new-unit sessions are represented, finish cumulative topic/dependency/notation promotion without inferring mastery.
- Resolve HW2 authoritative availability and either bootstrap its exact contract or checkpoint an HW2-ready state.
- Validate the final task branch, synchronize task JSON/Markdown, establish HANDOFF_SAFE, and archive when complete.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-new-unit-ingestion-hw2-prep.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
