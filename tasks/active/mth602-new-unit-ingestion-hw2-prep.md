<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-new-unit-ingestion-hw2-prep.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-new-unit-ingestion-hw2-prep
- Title: MTH 602 new-unit ingestion and HW2 preparation
- Status: BLOCKED_EVIDENCE
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

Obtain a current read-only snapshot of the local instructor checkout at ~/adamArchives/Adam/classes/MTH602-Fall2026-SciML: fetch origin/main without changing the worktree, report the exact origin/main SHA and recent commits, print README lines relevant to lab/HW2/deadlines, and list candidate assignment/lab paths. Then immediately identify the lab due 2026-09-30 and bootstrap that urgent artifact before continuing HW2.

## Remaining work

- Recover the current instructor origin/main SHA, README deadlines/tasks, and assignment/lab file paths from the user's local instructor checkout without modifying its working tree.
- Prioritize the lab reported due tonight (2026-09-30): identify its exact source path, instructions, required artifacts, and deadline before beginning lower-urgency work.
- Identify and ingest the authoritative HW2 artifact at its exact upstream commit and bootstrap homework/hw02 through the existing homework/source workflow.
- Complete exact-byte transfer of previously ingested classroom originals when a suitable binary transfer surface is available.
- Validate final MTH602 branch state, synchronize task JSON/Markdown, establish HANDOFF_SAFE, and archive when complete.

## Blockers / gates

- Authoritative current instructor-repository evidence is inaccessible from this chat's GitHub connection. A current read-only snapshot from the user's local checkout ~/adamArchives/Adam/classes/MTH602-Fall2026-SciML is required to identify HW2 and the lab due 2026-09-30 without guessing.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-new-unit-ingestion-hw2-prep.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
