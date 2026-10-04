<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/mth602-hw1-bonus-presentation.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: mth602-hw1-bonus-presentation
- Title: MTH 602 HW1 bonus competition presentation
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Create a concise 5–10 minute MTH 602 class presentation and natural talking points that faithfully explain the actual Homework 1 bonus coefficient-recovery methodology, show how the analysis narrowed to two exact candidate coefficient vectors, explain why the sparse rational candidate was chosen from the evidence available before submission, and reveal only at the end that the competing Taylor candidate was the hidden true answer even though the sparse submission still won the class competition.

## Workflow

- Repository: workspace-control
- Path: workflows/document-artifact-build.v1.json
- Checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9

## Repositories

### MTH602-AdamTrott

- Intent: mutate
- Remote branch: hw1-bonus-presentation
- Remote checkpoint: e5548148dd9dcfa10c2f419f05d12b66031e877f
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: true

## Next safe action

Present the current seven-slide draft and talking points to the user for review. The draft already implements the intended reveal structure: objective -> unstable OLS -> sparse/BIC structure -> two-candidate fork -> why sparse was chosen -> competition win/post-hoc clue -> final Taylor reveal. Do not lock or persist the binary PPTX as final until the user approves the narrative/content or requests revisions.

## Remaining work

- Have the user review the seven-slide first draft and narrative emphasis.
- Apply any requested content/layout revisions and rerender the deck.
- Persist editable build source, final PPTX, selected visual assets, and final rendered QA evidence to the isolated presentation branch after user approval.
- Refresh final task checkpoint and validation evidence, then leave actual classroom presentation/delivery to the user.

## Current draft state

- Durable storyboard: `homework/hw01/presentation/STORYBOARD.md`
- Durable talking points: `homework/hw01/presentation/TALKING_POINTS.md`
- Local draft: 7-slide PowerPoint with embedded speaker notes.
- Initial structural validation: PASS (`slides_test.py`, no overflow).
- Initial rendered QA: PASS after correcting the Slide 7 card-title wrap.

## Blockers / gates

- None; user content review is the current gate before final artifact lock.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-hw1-bonus-presentation.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
