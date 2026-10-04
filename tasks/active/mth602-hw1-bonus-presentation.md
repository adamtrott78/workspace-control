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
- Remote checkpoint: 17252384314bfa2acfc4362787eb56e078c408a9
- Remote verified: true

### workspace-control

- Intent: read
- Remote branch: main
- Remote checkpoint: 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9
- Remote verified: true

## Next safe action

Create and review a 5–7 slide storyboard before building slides. Default narrative: (1) competition objective and why coefficient recovery differs from prediction, (2) degree-9 OLS looked accurate but was numerically unstable, (3) sparse search exposed simple odd-power structure and suggested sin(2t), (4) the analysis narrowed to the Taylor and sparse rational candidates, (5) show the strongest pre-submission evidence and why it favored sparse, (6) submitted sparse candidate / won competition, then reveal that the Taylor candidate was actually the hidden answer and close with the lesson about model-selection evidence versus structural prior knowledge.

## Remaining work

- Reduce the 866-line methodology record into a 5–7 slide narrative emphasizing the objective, OLS failure, sparse search, two-candidate fork, decision evidence, and final reveal.
- Choose/generate only the visuals that materially help the class understand the reasoning, preferably using existing numerical evidence rather than decorative graphics.
- Build the PowerPoint on the isolated branch and preserve editable source/build files.
- Render and visually inspect every slide; revise for legibility, pacing, and reveal timing.
- Write concise talking points and transitions for a natural 5–10 minute delivery.
- Checkpoint final artifacts and leave actual classroom presentation/delivery to the user.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/mth602-hw1-bonus-presentation.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
