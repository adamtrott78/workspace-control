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
- Remote checkpoint: 5839870b067af9c416099e096d29c614c5b8402b
- Remote verified: true

## Next safe action

WINDOWS OPERATOR-ONLY A7 BOOTSTRAP — exact-SHA transport hardening 5839870b067af9c416099e096d29c614c5b8402b passed Workspace #3082 / Semantic #382 / Operator #655. The legacy session-level wop wrapper cannot be trusted to materialize intermediate ancestor trees in the existing DevCheckout; do not use it to target ca8b5983…. Materialize the current branch head directly in DevCheckout using Git, verify HEAD equals 5839870b…, stop/clean the stale degraded runtime with the checked-out workspace-operator-dev.ps1, invoke install-wop-commands.ps1 with -NoProfile and per-process ExecutionPolicy Bypass, then require WORKSPACE_OPERATOR_COMMANDS_INSTALLED=PASS, WORKSPACE_OPERATOR_SELF_TEST=PASS and wop-status execution. Do not source $PROFILE. No live Stage-12 authority exists.

## Remaining work

- Materialize current branch head 5839870b… directly in the Windows DevCheckout and install/accept the validated shim commands.
- After A7 acceptance, freeze a fresh D4 real-account Stage-12 review/procedure, validate 3/3, and obtain explicit one-shot authority.
- After D4 passes, run E1–E3 on Research Engine research-iterate with mixed executors, forced loss, durable recovery and resource/soak evidence.

## Blockers / gates

- WINDOWS USER SHIM INSTALL: connected tools cannot write Adam's local current-user WindowsApps directory. One bounded operator bootstrap remains.
- LEGACY WOP BOOTSTRAP LIMIT: do not use the old session-level wrapper to target intermediate ancestor SHAs; materialize the current branch head directly before installing the hardened shims.
- LIVE STAGE-12 AUTHORITY: no reusable real-account Stage-12 authority exists; A7 installation does not create authority.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
