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

## Workflow

- Repository: workspace-control
- Path: workflows/evidence-first-solution-research.v1.json
- Checkpoint: a9041372c50bf1258daea2236a3e62542a115117

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 392ce507a24fbd2d957d82d51630e00242787893
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

HANDOFF_SAFE at host-activation boundary. Do not redesign admission, retrieval, parser behavior, or Wave-1 model logic; those are already merged and validated. Continue the narrow child support task `workspace-local-extract-wave1-execution-v1`. Workspace-control PR #214 validation run 39197297919 PASS and route merge df142ab7829e364087dbbb7453cdc2779e9d7206 is already merged; current manifest/policy blobs are 844fe790e1af968bf87d37a8eb9ce7677cdea402 / 71bd0bb9c63436964462b1f9b889686ac328ee1d. Research-engine main is 366f9585145ab539dc43c3c974dcb8625489a3e3; trusted Wave-1 workflow blob is a5be693f750c481db21d86d239a505083aae40aa; exact inert trigger is OPEN PR #131 head 522430a6e9bfdd2977dd8517c5af9db4d1bdbf06 and must remain immutable/unmerged until the one authorized run. Next operation is exact Lambda host install/verification of the merged route, not policy design and not benchmark trigger. Only after installed identity/control-plane/residue PASS may the executor issue exactly one `/lambda-ci-local-extract-wave1 522430a6e9bfdd2977dd8517c5af9db4d1bdbf06` comment, follow only that run, read report plus final root receipt, and stop Wave 1 at PROMISING/PARTIAL/REJECT. Generic gpu-heavy remains DENY; no production routing change, larger-model search, or repeated tuning loop.

## Remaining work

- Wave 1 host activation — continue child support task workspace-local-extract-wave1-execution-v1. Install and verify exact workspace-control route merge df142ab7829e364087dbbb7453cdc2779e9d7206 on Lambda; require installed manifest blob 844fe790e1af968bf87d37a8eb9ce7677cdea402, workload-policy blob 71bd0bb9c63436964462b1f9b889686ac328ee1d, model-eval-local-extract-wave1 live, exact workflow blob a5be693f750c481db21d86d239a505083aae40aa, GITHUB_CONTROL_PLANE_PLUS_PUBLIC_PAYLOAD, model_eval_dual_gpu_v1, promoted qwen3.5-4b, exact expanded runtime, generic gpu-heavy still DENY, healthy services, and zero project residue.
- Wave 1 execution — only after host activation PASS, keep dedicated inert PR #131 open and immutable at exact head 522430a6e9bfdd2977dd8517c5af9db4d1bdbf06; issue exactly one `/lambda-ci-local-extract-wave1 522430a6e9bfdd2977dd8517c5af9db4d1bdbf06` comment and follow only that dedicated workflow. Do not rerun blindly after any partial or ambiguous execution.
- Wave 1 decision — read the report artifact and final root-owned provisioner receipt, evaluate all 9 papers / 71 historical evidence objects under the fixed configuration, and stop this wave with PROMISING, PARTIAL, or REJECT. Require non-scientific state, exact model/runtime/two-GPU identity, cleanup/postverify PASS, and no residue/quarantine.
- After the Wave-1 decision only, decide whether measured residuals justify Phase 4 component/model escalation, teacher adaptation, VERIFY-boundary analysis, or eventual production integration.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
