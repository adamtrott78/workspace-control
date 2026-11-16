<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-multirepo-research-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-multirepo-research-v1
- Title: Workspace Shell multi-repo PADataset research access v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Extend the live Workspace Shell v1 lineage with first-class PADataset access and a permanent candidate-evidence path that can validate exact candidate SHAs without promoting them to durable task authority, while preserving credential isolation, private-repository support, rollback, and exact-SHA authoritative execution.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-candidate-evidence-current-v1
- Remote checkpoint: af3baf3bdc29bff6ae7114059fdfe4709dc13100
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

DO NOT RETRY ROOT ACTIVATION YET. Recover the exact stderr for failed transient unit workspace-shell-job-c02602c3-80a8-42.service (receipt job-c02602c3-80a8-4233-affe-943194db9cc0, failure time 2026-11-16T14:46:59Z) with a read-only local journal query. Connected Workspace Shell cannot access arbitrary transient job journals by design. Once the stderr is known, patch only the demonstrated hostile-worker evaluator-denial runtime defect, add exact regression coverage, validate the new runtime, update JSON+Markdown atomically, and only then refreeze/retry activation. Preserve PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f and semantic capsule/execution 8019248f6952743d61e90d5abac754356952c18b / 7c20097c5f177f23c16a765b95ce94d7161f0d29.

## Remaining work

- Read the journal for exact transient unit workspace-shell-job-c02602c3-80a8-42.service around 2026-11-16T14:46:59Z to recover the 144-byte stderr from the failed evaluator-denial process.
- Patch only the defect demonstrated by that stderr, add a regression that exercises the exact failure mode, validate the new runtime candidate, then refreeze the activation tuple.
- Only after a fresh activation produces LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS, LOCAL_EVALUATOR_ISOLATION=PASS, EVALUATOR_ISOLATION_ACCEPTANCE=PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS may the integrated semantic program continue to the fake-worker private-route harness.

## Blockers / gates

- LATEST LIVE ACTIVATION FAILED CLOSED AND ROLLED BACK after evaluator-denial authorization succeeded. The exact receipt job-c02602c3-80a8-4233-affe-943194db9cc0 shows exit_code=1, stdout_bytes_seen=0, stderr_bytes_seen=144, stderr_sha256=8f8a93cfc164206a98ab72ca9c2767ca6c343583261d4e6c838fa00258456113 for evaluator-denial-probe at semantic SHA 7c20097c5f177f23c16a765b95ce94d7161f0d29.
- Target/profile admission and frontend resolver parity are now proven fixed: LOCAL_EVALUATOR_WORKER_DENIAL_MCP=PASS and the receipt authorization_decision is ALLOW. The remaining defect is inside actual hostile-worker execution of the fixed denial probe or its exact filesystem observation.
- Direct live rollback-state validation-bounded execution succeeds with /usr/bin/python3 in the hostile-worker sandbox, so generic Python/bubblewrap startup is not the current root cause.
- Connected Workspace Shell cannot read the failed transient unit journal because transient job units are outside its fixed inspect allowlist, and the semantic task disappeared from live authority after rollback. Recover the exact transient-unit stderr locally before changing runtime code or retrying activation.
- Existing helper, issuer, generic shell/interpreter, network, evaluator-path, PADataset, and GPU authority boundaries remain unchanged.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
