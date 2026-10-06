<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-execution-policy-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-execution-policy-v1
- Title: Workspace Lambda Execution Policy and Model Workload Governance v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, implement, and adversarially validate a fail-closed workload admission, trusted model/dependency cache, resource-governance, and execution-evidence layer on top of the accepted Lambda P5 CPU and gpu-small autonomous runner substrate so ChatGPT/GitHub-driven work can safely execute pinned model-scale workloads without granting candidate workflow code the ability to invent capabilities, persist mutable cross-job state, access production/scientific state, or widen host authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 5d9aea62cfeceb73052ccdf325d648f6e44f1134
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 9b025b3b1092d1c4e0c1f98678472341d26ee354
- Remote verified: true

## Next safe action

In GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens, open the existing research-engine controller token if editable (otherwise mint a replacement with the same existing repository/runner permissions) and add repository permission Actions: Read only; do not add Actions: Write. Keep repository access restricted to adamtrott78/research-engine. If the token value changes, restage it only with sudo -u ci-controller /opt/workspace-ci/controller/stage-pat; if the existing token is edited in place, no restaging is required. Then run a non-secret child-shell probe against GET /repos/adamtrott78/research-engine/actions/runs/37540379924 using /var/lib/workspace-ci/controller/github-token and require HTTP 200, followed by systemctl restart workspace-ci-controller.service workspace-ci-controller-gpu.service and a zero-restart-delta health check. Only after that credential gate passes, trigger a NEW /lambda-ci-p5 f5ba8278d7dfa22e63623ddf51896a6dec002813 on PR #106; use /lambda-ci-cancel <run_id> through the merged GitHub-hosted control workflow for stale acceptance cancellation. Do not enable model-scale classes or gpu-heavy.

## Remaining work

- Add GitHub Actions: Read to the existing narrow research-engine controller credential, verify the live controller is stable, then run fresh non-scientific admission-v2 CPU and gpu-small acceptance and validate root receipts plus residue-free cleanup.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Lambda controller fine-grained PAT lacks GitHub Actions repository permission Read. Add Actions: Read for research-engine while preserving the existing narrow repository scope and all currently required controller permissions; do not grant Actions: Write.
- After the server-side permission change, verify the stored controller token can GET the research-engine Actions run endpoint with HTTP 200 and verify workspace-ci-controller.service stops restart-looping before triggering another CPU acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
