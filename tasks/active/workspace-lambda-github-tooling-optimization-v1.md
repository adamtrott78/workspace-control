<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-github-tooling-optimization-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-github-tooling-optimization-v1
- Title: Workspace Lambda GitHub Tooling Optimization v1
- Status: CHECKPOINTED
- Capsule schema: v2

## Goal

Generalize and optimize the reusable workspace-control tooling that connects ChatGPT/GitHub workflows to project-isolated Lambda self-hosted execution, reducing human-terminal mediation and repeated project-specific glue while preserving the accepted security, provenance, exact-SHA, cleanup, and rollback boundaries proven by the current research-engine pilot.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-lambda-github-tooling-optimization-v1
- Remote checkpoint: 1053885a71f84fa68a9475b7b17e17ebd7b0258b
- Remote verified: true

## Next safe action

CHECKPOINT_AND_STOP while the parent P5 implementation remains active elsewhere. Do not write Workspace Heartbeat from this child conversation and do not merge PR #91 or mutate parent/P5/research-engine runtime paths. Once P5 has a durable accepted/stable checkpoint, rehydrate current workspace-control main and the authoritative parent task, refresh PR #91 against that state, then run the first end-to-end ChatGPT-triggered Lambda validation through the accepted GitHub comment interface.

## Remaining work

- Keep validated draft PR #91 unmerged while the parent P5 implementation is actively changing main; after P5 stabilizes, rehydrate current main and refresh/revalidate the isolated protocol branch before promotion.
- After parent P5 acceptance, exercise the ChatGPT -> exact-SHA PR comment -> correlated GitHub run -> compact receipt -> immediate continuation loop with zero routine SSH/PAT relay.
- Adopt the comment-ID run-name correlation convention only through the owning project workflow after P5 stabilization and validate exact correlation under concurrent run conditions.
- Measure human terminal steps, trigger-to-bound-run tool calls, terminal-to-diagnosis tool calls, ambiguous correlation rate, successful-run log downloads, and post-terminal idle time.
- Revisit generic execution-profile/launcher implementation only as a later explicitly authorized runtime-layer optimization after parent P5 acceptance.

## Blockers / gates

- The parent P5 controller/provisioner implementation is active in a separate owning conversation; this child must remain read-only with respect to that task and live Lambda runtime until P5 has a durable accepted/stable checkpoint.
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
