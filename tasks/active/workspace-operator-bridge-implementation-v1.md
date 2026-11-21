<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-operator-bridge-implementation-v1
- Title: Workspace Operator Bridge Implementation v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Implement the UX-13-frozen human-operated Chat Instant bridge as a staged, test-first Windows/Firefox system: .NET 10 helper, typed Native Messaging/named-pipe BrowserPort, least-privilege Firefox MV3 adapter, deterministic fake-worker simulator, recovery/fault closure, packaging/rollback, empirical performance/usability evidence, optional WebView2 comparison, and gated real-account calibration without changing the frozen manual Ctrl+V + Enter or authority/security boundaries.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-semantic-execution-migration-v1
- Remote checkpoint: aa44c9a844eb5927565e1911e96155dfb0f68207
- Remote verified: true

## Next safe action

WINDOWS-ONLY STALE-BOOTSTRAP RECOVERY SMOKE — repair aa44c9a844eb5927565e1911e96155dfb0f68207 passed Workspace #3065 / Semantic #365 / Operator #638. The previous smoke already proved verified-dead workdir residue can be deferred and fresh runtime startup succeeds, but the persistent Firefox profile restored the exact legacy simulator URL http://127.0.0.1:8765/fake-worker.html plus one blank tab. aa44c9a… narrowly repairs only that exact legacy bootstrap residue to https://chatgpt.com/?temporary-chat=true and removes the one stale blank tab in the exact two-tab residue shape; arbitrary localhost/unmanaged tabs remain untouched. NEXT ACTION: run wop smoke on the current bookkeeping tip with no manual Firefox cleanup. Require no Troubleshoot Mode prompt, Temporary Chat startup, retained auth or at most one login, no stray blank/duplicate worker tab, one Ctrl+Space on that same Temporary Chat, clipboard exactly WORKSPACE_OPERATOR_SMOKE_PACKET_V1, and managed Firefox foreground. Do not create or infer live Stage-12 authority from this local smoke.

## Remaining work

- live transport gate: after Workspace Shell semantic authority exists, prove exact-host Tailscale fake-worker transport before real-account use.
- impl_12: bounded real-account calibration with no DOM/content automation, no added browser permissions and no security workaround.
- impl_09: authoritative target-machine UX-09 performance/resource benchmark after real-account calibration.
- impl_13: explicit PROMOTE_V0/HOLD/REVISE production-readiness review.

## Blockers / gates

- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. It remains mandatory before impl_13 production readiness can pass.
- Real-account Stage-12 retry remains paused. Repair aa44c9a… is 3/3 validated, but the operator must rerun the Windows-only fast smoke and prove the persistent Firefox profile now lands on Personalized Temporary Chat with no stale fake-worker/blank duplicate, then prove Ctrl+Space clipboard replacement and native foreground. No new live retry authority exists.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
