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
- Remote branch: course-workflows-v2-refactor
- Remote checkpoint: 8a6202b020d0733437960415f77833f2001da962
- Remote verified: True

### MTH602-AdamTrott

- Intent: read
- Remote branch: main
- Remote checkpoint: 62b7a03c7139cb3987b72ad66bdc532e8a61b82a
- Remote verified: True

### CIS560-AdamTrott

- Intent: read
- Remote branch: tutor-framework
- Remote checkpoint: 1af3ce7022d079b89f0fbca32f313a6853db1c60
- Remote verified: True

### EAS501-AdamTrott

- Intent: read
- Remote branch: eas501-tutor-bootstrap
- Remote checkpoint: aa6195377b856862124643d0fc501969467fad3b
- Remote verified: True

### PADataset

- Intent: read
- Remote branch: resume-framework
- Remote checkpoint: 078461795be3c1d3e5c3845c81607166fac9fad3
- Remote verified: True

## Next safe action

Start from workspace-control README.md and this capsule. Continue on the isolated `course-workflows-v2-refactor` branch at 8a6202b020d0733437960415f77833f2001da962. Review the current shared tutoring/operator/adapter/evaluation contracts against only the smallest pinned legacy evidence needed from MTH602, CIS560, EAS501, and PADataset; identify the smallest reusable shared changes required by this task's acceptance criteria without mutating project repositories. Record the review as durable branch changes/evidence only where justified. After any material capsule update, regenerate its Markdown immediately; if the review validates a bounded design direction, advance to `workflow_descriptor_design` rather than stopping at the review boundary.

## Remaining work

- Review current shared tutoring/adapter/evaluation/operator contracts against demonstrated legacy repo evidence and identify the smallest reusable changes.
- Define composite reusable course workflow descriptors/procedures for course bootstrap/migration, content ingestion, assessment preparation, study session, assignment work, cheat-sheet build, communications ingestion, and document-artifact build without changing task-capsule v2 composition semantics.
- Implement shared contract/template/procedure updates on the isolated architecture branch while preserving project-local truth and explicit workflow-version migration rules.
- Validate cold-start routing, assessment relevance behavior, multimodal ingestion, LaTeX artifact QA, continuation behavior, and executor handoff.
- Promote the validated shared architecture to workspace-control main through an explicit reviewed integration step and record the exact promoted checkpoint.
- Create separate durable migration capsules for MTH602, CIS560, EAS501, and resume/application integration pinned to the promoted shared checkpoint and exact project checkpoints.
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
