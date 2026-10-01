<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-new-unit-ingestion-hw2-prep.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-new-unit-ingestion-hw2-prep
- Title: MTH 602 new-unit ingestion and HW2 preparation
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Bring MTH 602 course-content state current by visually synthesizing new classroom/whiteboard photographs and handwritten notes with the smallest relevant instructor material, persist durable session/topic knowledge without falsely promoting mastery, and bootstrap Homework 2 when authoritative assignment evidence is available.

## Workflow

- Repository: workspace-control
- Path: workflows/course-assignment-work.v1.json
- Checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9

## Repositories

### MTH602-AdamTrott

- Intent: mutate
- Remote branch: unit-ingestion-hw2
- Remote checkpoint: a05f6881dc55aef1cae11e755449df050c975708
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: true

## Next safe action

Continue HW2 Floating-point Problem 1(b) in LEARNING mode from MTH602 unit-ingestion-hw2@a05f6881dc55aef1cae11e755449df050c975708. Ask the student to restate the three phases of the observed error curve with the refined distinction: huge early relative error from enormous truncated partial sums versus the tiny target, rapid reduction as later terms cancel and truncation error shrinks, then a catastrophic-cancellation/roundoff floor near order-one relative error. Once correct, treat 1(b) as complete and move to 1(c) without revealing the stable reformulation before diagnosing whether the student can find it.

## Remaining work

- Finish Floating-point Problem 1(b) by verifying the refined three-phase interpretation of the executed convergence curve, then begin 1(c) in LEARNING mode and diagnose the stable reformulation without changing taylor_exp.
- Submit the completed Lab1 PDF/notebook through one of the instructor-approved channels; artifact production is complete but actual submission is a user action.
- Complete exact-byte transfer of the HW2 PDF/CSV/PNG source package into homework/hw02 and verify against assignment/manifest.json when a suitable binary transfer surface is available.
- Before Probability Problem 4, ingest the exact Bishop Problems 2.16 and 2.18 from the course textbook.
- Work HW2 one bounded problem at a time under the tutoring/mastery protocol, starting with Floating-point Problem 1.
- Build and visually validate the final reproducible HW2 report and separately verify actual submission.
- Complete exact-byte transfer of previously ingested classroom originals when a suitable binary transfer surface is available.
- Synchronize final task JSON/Markdown, establish HANDOFF_SAFE, and archive when the task's preparation/assignment boundary is complete.

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
