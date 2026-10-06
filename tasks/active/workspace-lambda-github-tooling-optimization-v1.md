<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-github-tooling-optimization-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-github-tooling-optimization-v1
- Title: Workspace Lambda GitHub Tooling Optimization v1
- Status: VALIDATING
- Capsule schema: v2

## Goal

Generalize and optimize the reusable workspace-control tooling that connects ChatGPT/GitHub workflows to project-isolated Lambda self-hosted execution, reducing human-terminal mediation and repeated project-specific glue while preserving the accepted security, provenance, exact-SHA, cleanup, and rollback boundaries proven by the current research-engine pilot.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-lambda-github-tooling-optimization-v1
- Remote checkpoint: 1beb7d79ba12cf336c1d14645714f801e388a1f2
- Remote verified: true

## Next safe action

Consume the next PR #89 validation result immediately. If it fails, diagnose only the failing child-branch path and repair the demonstrated defect; if it passes, checkpoint the chat-orchestration protocol as validated. Do not mutate the parent P5 task, controller/provisioner implementation, research-engine Lambda workflows, or live Lambda state from this child.

## Remaining work

- Validate PR #89 through the repository's full integration path and repair only demonstrated child-branch defects.
- After the parent P5 path is accepted and stable, exercise the ChatGPT -> PR comment -> GitHub run -> compact receipt -> continuation loop without routine SSH or PAT relay.
- Adopt the comment-ID run-name correlation convention only through the owning project workflow after P5 stabilization; do not modify research-engine workflow from this child while P5 is active.
- Measure human terminal steps, trigger-to-bound-run tool calls, terminal-to-diagnosis tool calls, ambiguous correlation rate, successful-run log downloads, and post-terminal idle time.
- Revisit generic execution-profile/launcher implementation only as a later explicitly authorized runtime-layer optimization after parent P5 acceptance.

## Blockers / gates

- The parent P5 controller/provisioner implementation is active in a separate owning conversation; this child must remain read-only with respect to that task and live Lambda runtime.
- Strong one-to-one issue-comment run correlation requires a later project-owned metadata-only workflow adaptation; current compatibility correlation remains fail-closed and provisional until then.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-github-tooling-optimization-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
