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
- Remote checkpoint: 54ac65cbcd4211554710b8f8f4231c6c9554e3cc
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

Workspace Shell live activation is accepted. Validate this new authority-state commit, sync the umbrella task, then derive the exact reviewed private route for benchmarks/workspace-semantic-execution/live_fake_worker_transport_v1.py from durable repository evidence. Do not invent a route or widen authority. If the reviewed route exists and is account/browser/model/GPU-free, execute the fake-worker transport and require an exact action/status/result roundtrip before proceeding toward Stage 12.

## Remaining work

- Validate this live-acceptance authority-state commit.
- Sync the umbrella workspace-semantic-execution-migration-v1 task to the accepted live Workspace Shell runtime and evaluator-isolation checkpoint; validate Workspace/Semantic/Operator exact head.
- Derive the exact reviewed private route/profile/task authority for benchmarks/workspace-semantic-execution/live_fake_worker_transport_v1.py from durable source/docs.
- Run the fake-worker transport only if the reviewed route and authority are explicitly present and it remains account-free, browser-free, model-free, and GPU-free; require exact action/status/result roundtrip.
- Continue toward Stage 12 / real account calibration only after the fake-worker transport acceptance.

## Blockers / gates

- Workspace Shell multirepo live activation is accepted and independently verified at runtime 54ac65cbcd4211554710b8f8f4231c6c9554e3cc with evaluator isolation PASS.
- The next gate is no longer Workspace Shell activation. Before any fake-worker execution, derive the exact reviewed private route for benchmarks/workspace-semantic-execution/live_fake_worker_transport_v1.py from durable repository authority; do not invent a route.
- Claim-bearing Reasoning Economy execution remains separately gated on reviewed live executor authority, evaluator isolation, and calibrated allowance telemetry.
- GitRunner/controller modernization remains deferred and authority-separated.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.


## Candidate evidence mountpoint repair — Track B unblock

PADataset candidate validation exposed a deterministic launcher defect: clean exact-SHA candidate materializations do not contain the ignored/untracked `local_artifacts/evidence/` directory, while the launcher required that directory to pre-exist before binding the verified read-only evidence root.

Validated runtime: `f3f999ff0200e2450d83e93887b2450f1ee83e2f`.

The fix creates only the empty bind target inside disposable per-job writable scratch and fails closed on symlink/non-directory path components. It does not mutate the candidate store, PADataset execution source, historical evidence source, task authority, profiles, network policy, credentials, or privileged-helper policy.

Focused candidate validation: `job-a31b81ba-8ce9-4f29-903d-a6bcdfb3aa0c` — **4 passed**.

The installed-plugin diff from live runtime `54ac65cbcd4211554710b8f8f4231c6c9554e3cc` is limited to the 31-line `job_launcher.py` repair.

Activation remains a root/operator gate using the existing transactional upgrader and the frozen PADataset/semantic tuple. No merge authority is implied by draft PR #642.
