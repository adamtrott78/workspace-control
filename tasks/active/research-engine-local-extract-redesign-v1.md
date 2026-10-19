<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Return to first principles on research-engine EXTRACT and identify, benchmark, and if justified implement a provenance-preserving mostly-local extraction architecture that makes STANDARD Codex a rare ambiguity/failure fallback rather than the default, while reusing accepted local document/VERIFY infrastructure and not repeating approaches already invalidated by durable evidence.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: df142ab7829e364087dbbb7453cdc2779e9d7206
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Install and verify exact workspace-control route merge df142ab7829e364087dbbb7453cdc2779e9d7206 on Lambda. Require installed manifest blob 844fe790e1af968bf87d37a8eb9ce7677cdea402 and workload-policy blob 71bd0bb9c63436964462b1f9b889686ac328ee1d, exact unchanged bootstrap/model/runtime/controller identities, model-eval-local-extract-wave1 live with workflow blob a5be693f750c481db21d86d239a505083aae40aa and public-payload capability, generic gpu-heavy DENY, all three services active NRestarts=0, and zero project CPU/GPU residue. Only after PASS, trigger PR #130 head 28d8379dfb650bfa63ea9e7ac9476b8be0f55b10 exactly once.

## Remaining work

- Wave 1 host activation — install exact workspace-control df142ab7829e364087dbbb7453cdc2779e9d7206 on Lambda and verify manifest blob 844fe790e1af968bf87d37a8eb9ce7677cdea402, policy blob 71bd0bb9c63436964462b1f9b889686ac328ee1d, model-eval-local-extract-wave1 live, generic gpu-heavy DENY, accepted model/runtime identity, healthy services, and zero residue.
- Wave 1 execution — issue exactly one `/lambda-ci-local-extract-wave1 28d8379dfb650bfa63ea9e7ac9476b8be0f55b10` comment on research-engine PR #130 and follow only that dedicated run.
- Wave 1 decision — inspect the nine-paper report plus final root receipt and stop with PROMISING, PARTIAL, or REJECT. No production EXTRACT/VERIFY routing change, larger-model search, generic gpu-heavy enablement, or tuning loop.

## Blockers / gates

- Host activation pending: exact workspace-control route merge df142ab7829e364087dbbb7453cdc2779e9d7206 is green/merged but its manifest/policy have not yet been installed and verified on Lambda. Do not trigger PR #130 before that exact install passes.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
