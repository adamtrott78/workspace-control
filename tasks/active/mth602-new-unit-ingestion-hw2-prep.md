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
- Remote checkpoint: 62b7a03c7139cb3987b72ad66bdc532e8a61b82a
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: bc3966f10b8b07b9a27d8ec5275f218c209a7609
- Remote verified: true

## Next safe action

Start a fresh ingestion chat from this capsule. From MTH602 README.md at unit-ingestion-hw2@62b7a03c7139cb3987b72ad66bdc532e8a61b82a, load the existing classnotes visual-ingestion route and smallest relevant course/source/study owners. Then ask the user to upload the new classroom/whiteboard and handwritten-note images, preferably grouped by session/date/order. Inspect them directly before deciding whether any OCR is useful. Do not mutate course knowledge until the actual image evidence has been visually reviewed.

## Remaining work

- Upload the new classroom/whiteboard photographs and handwritten notes in the ingestion chat, grouped by session/date/order when known.
- Visually synthesize the new unit with the repository's direct-visual model and smallest relevant instructor sources.
- Persist session syntheses and justified cumulative topic/dependency/notation updates without inferring mastery.
- Resolve HW2 authoritative availability and either bootstrap it or checkpoint an HW2-ready state.
- Validate/push the task branch, synchronize task JSON/Markdown, establish HANDOFF_SAFE, and archive when complete.

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
