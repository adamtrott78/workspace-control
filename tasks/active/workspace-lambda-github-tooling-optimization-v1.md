<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-github-tooling-optimization-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-github-tooling-optimization-v1
- Title: Workspace Lambda GitHub Tooling Optimization v1
- Status: IN_PROGRESS
- Capsule schema: v2
- Current stage: control_loop_measurement

## Goal

Minimize the model-visible ChatGPT/GitHub orchestration delay and interaction between a naturally required Lambda workflow becoming terminal and ChatGPT validating its compact exact-SHA evidence and beginning the next substantive owning-task action, while treating the execution-policy/P5 runtime as externally authoritative.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-lambda-github-tooling-optimization-v1
- Remote checkpoint: 189c2cd35e48db2ba1838ad404fb2c55f0e723b6
- Remote verified: true

## Next safe action

On the next naturally required successful CPU or gpu-small owning-task run, consume its CONTROL_LOOP_OBSERVATION_V1 exactly as produced. Evaluate only model-visible GitHub connector reads, exact workload+PR+request-SHA job correlation, compact receipt retrieval/verification, actual human relay, and terminal-to-next-action delay. Do not request an extra run/probe/log/SSH/artifact for optimization measurement and do not mutate execution-policy/P5/runtime responsibilities.

## Remaining work

- Keep validated draft PR #143 unmerged while accumulating ordinary-run control-loop observations; revise only if evidence demonstrates a protocol/tooling defect or measurable orchestration inefficiency.
- Consume future CONTROL_LOOP_OBSERVATION_V1 records from naturally required successful CPU/gpu-small owning-task runs without requesting extra measurement work.
- Measure and reduce assistant-visible success-path reads: eliminate full logs, avoid redundant job/status reads, and count actual artifact discovery/download invocations on the current connector surface.
- Measure terminal_evidence_first_available_at -> receipt_validated_at -> next_substantive_action_started_at when those timestamps are naturally observed; preserve null otherwise.
- Validate zero routine human relay on ordinary successful runs while separately classifying any owning-task-required acceptance/recovery evidence.
- Treat comment-ID run metadata as optional future ergonomics only if real duplicate-identical-trigger ambiguity occurs.
- Keep generic launcher/runtime refactoring deferred outside the current observer-only orchestration scope unless the user explicitly reauthorizes it.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-github-tooling-optimization-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
