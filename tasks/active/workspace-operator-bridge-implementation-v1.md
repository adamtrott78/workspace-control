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
- Remote checkpoint: ca8b59837391405fd693b4a4e95b1e14a1441e96
- Remote verified: true

## Next safe action

WINDOWS OPERATOR-ONLY COMMAND SHIM INSTALL GATE. Profile-based alias persistence is superseded by validated replacement ca8b59837391405fd693b4a4e95b1e14a1441e96 (#3080/#380/#653). Use existing session wop only to check out this exact SHA and stop the stale degraded smoke runtime, then invoke operator-bridge/tools/install-wop-commands.ps1 directly with -NoProfile/-ExecutionPolicy Bypass. Do NOT source $PROFILE. Installer removes only the obsolete owned profile block and installs owned .cmd shims in the already-present current-user WindowsApps PATH directory without changing PATH or persistent execution policy. Require WORKSPACE_OPERATOR_COMMANDS_INSTALLED=PASS, then wop-self-test must PASS from an offline runtime and wop-status must execute. No live Stage-12 authority exists.

## Remaining work

- Install and accept validated shim commands ca8b5983… on Adam's Windows machine.
- After A7 acceptance, freeze a fresh D4 real-account Stage-12 review/procedure, validate 3/3, and obtain explicit one-shot authority.
- After D4 passes, run E1–E3 on Research Engine research-iterate with mixed executors, forced loss, durable recovery and resource/soak evidence.

## Blockers / gates

- WINDOWS USER SHIM INSTALL: connected tools cannot write Adam's local current-user WindowsApps directory. One bounded operator command is required.
- LIVE STAGE-12 AUTHORITY: no reusable real-account Stage-12 authority exists; alias installation does not create authority.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
