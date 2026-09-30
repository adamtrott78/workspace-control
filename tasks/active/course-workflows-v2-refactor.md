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
- Remote checkpoint: d757a0c5d59e915fa3f78b4c19d936748f7c318d
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

Promote the validated workspace-control architecture explicitly. Review `course-workflows-v2-refactor@d757a0c5d59e915fa3f78b4c19d936748f7c318d` against the current `main`, preserving concurrent main-only task/control changes. Use a reviewed pull-request/merge integration when clean; do not force-update main. Verify the resulting main commit contains the registry bootstrap, shared review/design/validation records, policy/template/evaluation updates, seven procedures, and eight descriptors while retaining unrelated main work. Immediately checkpoint the promoted main identity in this capsule+Markdown, then create the four required child migration capsules (MTH602, CIS560, EAS501, resume/application integration) on main. Do not execute child repository migrations in this parent chat unless the parent capsule explicitly transitions ownership.

## Remaining work

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
