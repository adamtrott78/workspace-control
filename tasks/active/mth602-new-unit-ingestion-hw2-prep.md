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
- Remote checkpoint: 6b1cefa7c6d36e0c33e7aaaa926bd07f07b46e1a
- Remote verified: True

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: bc3966f10b8b07b9a27d8ec5275f218c209a7609
- Remote verified: True

## Next safe action

Bridge the exact current instructor lab and HW2 artifacts from local origin/main@5c037ac5e16249f6d6fa107f50f73ceac848f60d into a user-uploadable bundle without changing the instructor checkout. Read and execute the lab first because it is due 2026-09-30; then ingest/bootstrap HW2 from Homeworks/hw2/ for its 2026-10-05 deadline.

## Remaining work

- Bridge exact authoritative lab and HW2 source bytes from instructor origin/main@5c037ac5e16249f6d6fa107f50f73ceac848f60d without modifying the instructor checkout.
- Prioritize and complete Lab1-ProbabilyCoin.ipynb, due 2026-09-30, preserving its exact instructions and required deliverable.
- Ensure the final project-topic action item due 2026-09-30 is not missed.
- Ingest HW2 exact source package from Homeworks/hw2/ and bootstrap homework/hw02; HW2 is due 2026-10-05.
- Complete exact-byte transfer of previously ingested classroom originals when a suitable binary transfer surface is available.
- Validate final MTH602 branch state, synchronize task JSON/Markdown, establish HANDOFF_SAFE, and archive when complete.

## Blockers / gates

- The current GitHub connector still cannot directly read sfield17/MTH602-Fall2026-SciML. Exact lab/HW2 contents must be bridged from the user's local instructor checkout at origin/main@5c037ac5e16249f6d6fa107f50f73ceac848f60d before their requirements can be interpreted or student work created.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-new-unit-ingestion-hw2-prep.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
