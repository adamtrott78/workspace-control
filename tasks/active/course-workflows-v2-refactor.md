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
- Remote checkpoint: 32412c28440681bcfc6136ad36be71b3c1151f9e
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

Create four separate task-capsule v2 migration tasks on workspace-control main for MTH602, CIS560, EAS501, and PADataset resume/application integration. Each child must pin the promoted shared checkpoint 0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9 (or the exact descendant only if its capsule creation requires a newer main control-only commit), bind the appropriate reusable workflow descriptor by exact path/checkpoint/content identity, pin the exact target-project starting checkpoint, preserve project-local authority, and explicitly prohibit unrelated project migration. Generate each child Markdown immediately with its JSON in the same main commit. Do not execute the child repository migrations in this parent chat. After creation, verify all eight child files and advance the parent to completion/HANDOFF_SAFE assessment.

## Remaining work

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
