<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/course-workflows-v2-refactor.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: course-workflows-v2-refactor
- Title: Shared course workflows and tutor architecture v2 refactor
- Status: CHECKPOINTED
- Capsule schema: v2

## Goal

Evolve the repository-backed course tutoring/application architecture to the task-capsule-driven workspace-control v2 model: remove dependence on conversational builder/tutor hierarchy, define reusable course and document-artifact workflow descriptors/procedures, improve assessment alignment and multimodal ingestion, preserve project-local authority and mastery semantics, and create independently executable migration capsules for MTH602, CIS560, EAS501, and the resume/application workflow.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 06058acf5a074db5a849f7f42f721971e5dda965
- Remote verified: true

### MTH602-AdamTrott

- Intent: read
- Remote branch: main
- Remote checkpoint: 62b7a03c7139cb3987b72ad66bdc532e8a61b82a
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: resume-framework
- Remote checkpoint: 078461795be3c1d3e5c3845c81607166fac9fad3
- Remote verified: true

## Next safe action

Start from workspace-control README.md at the recorded baseline. Inspect the smallest available evidence needed to establish stable workspace paths and canonical-branch identity for CIS560-AdamTrott and EAS501-AdamTrott; then add only those stable identities to repos.json. Do not encode tutor-framework/eas501-tutor-bootstrap HEADs as registry state. After that material mutation, update this JSON capsule and immediately regenerate its Markdown before any further architecture work; then add CIS560/EAS501 as formal read-only repository recovery entries and proceed to shared_contract_review.

## Remaining work

- Register CIS560-AdamTrott and EAS501-AdamTrott with stable identity in repos.json after verifying their workspace paths/canonical branch evidence; then add them as formal read-only recovery entries in this capsule.
- Review current shared tutoring/adapter/evaluation/operator contracts against demonstrated legacy repo evidence and identify the smallest reusable changes.
- Define composite reusable course workflow descriptors/procedures for course bootstrap/migration, content ingestion, assessment preparation, study session, assignment work, cheat-sheet build, communications ingestion, and document-artifact build without changing task-capsule v2 composition semantics.
- Implement shared contract/template/procedure updates while preserving project-local truth and explicit workflow-version migration rules.
- Validate cold-start routing, assessment relevance behavior, multimodal ingestion, LaTeX artifact QA, continuation behavior, and executor handoff.
- Create separate durable migration capsules for MTH602, CIS560, EAS501, and resume/application integration from exact project checkpoints.
- Complete HANDOFF_SAFE assessment and archive this task.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/course-workflows-v2-refactor.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
