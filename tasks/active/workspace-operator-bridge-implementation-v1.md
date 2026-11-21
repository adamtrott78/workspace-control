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
- Remote checkpoint: 3c606ac150bdf87dd9bfd38e7a2791aa6b2ca3da
- Remote verified: true

## Next safe action

WINDOWS OPERATOR-ONLY COMMAND INSTALL GATE. Convenience-command source 3c606ac150bdf87dd9bfd38e7a2791aa6b2ca3da is exact-head 3/3 green (#3078/#378/#651), and Adam requires it before D4. Use the existing session wop wrapper only to check out that exact SHA, then invoke operator-bridge/tools/install-wop-commands.ps1 directly in the current PowerShell so the global commands are available immediately and persist through $PROFILE.CurrentUserAllHosts. Verify WORKSPACE_OPERATOR_COMMANDS_INSTALLED=PASS, then wop-self-test must print WORKSPACE_OPERATOR_SELF_TEST=PASS and wop-status must execute. No live Stage-12 authority exists and no D4 run is authorized by this install.

## Remaining work

- Install/accept the validated current-user convenience commands on Adam's Windows machine: wop-up, wop-down, wop-reset, wop-status, wop-self-test.
- After alias acceptance, if Adam chooses D4, freeze a fresh bounded real-account Stage-12 review/procedure against the current validated front-end/command state, validate 3/3, and obtain explicit one-shot authority before execution.
- After D4 passes, participate in E1–E3 using Research Engine research-iterate: live mixed executors, forced worker/session/process loss, durable recovery, and resource/soak evidence.

## Blockers / gates

- WINDOWS USER-PROFILE INSTALL: connected repository/Linux tools cannot mutate Adam's local PowerShell profile. One explicit operator command is required to install and immediately load the validated convenience block.
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
