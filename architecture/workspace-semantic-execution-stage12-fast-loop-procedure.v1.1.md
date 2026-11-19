# Stage-12 Fast Redesign Loop Procedure v1.1

Status: REVIEW CANDIDATE — NOT AUTHORITY

## Why v1.0 failed

The v1.0 live attempt consumed its one-shot authority and reached `STAGE12_Q1_READY`, but `Ctrl+Space` was not registered by WorkspaceOperator.

The current startup path constructs `BridgeController` with a disabled `BridgeState`. `WindowsHotkeyRegistrar.Register()` is called only when `BridgeController.SetEnabled(true)` runs. In the current runtime, the only enable call is the manual tray toggle. Neither `Program.cs` nor `run-stage12-real-instant.ps1` enables the bridge.

The operator observed `Ctrl+Space` reach the Linux terminal as `^@`. The clipboard also retained the prior Windows-ready marker. Therefore the dispatch coordinator never ran. No clipboard write, browser final-focus call, or native foreground fallback was exercised.

## Redesign principle

Do not use the full Stage-12 real-account transaction to debug Windows interaction mechanics.

Split validation into two layers:

1. **Windows-only interaction smoke** — hotkey registration, synthetic action, Firefox adapter, clipboard write, browser focus, native foreground.
2. **Full Stage-12 live calibration** — only after the Windows-only smoke is green.

## Fast dev lifecycle

Create `operator-bridge/tools/workspace-operator-dev.ps1` with:

- `start`
- `stop`
- `reset`
- `status`
- `smoke`

The dev harness should reuse the existing checkout and incremental .NET build. It should use a dedicated dev-only Firefox profile and preserve that profile between runs so repeated redesign tests do not require a fresh login.

The dev harness must not start Linux PostgreSQL, create a Tailscale route, create a Python venv, clone a fresh repository, touch the candidate branch, or consume any Stage-12 live authority.

## Explicit startup enablement

Add an explicit startup switch such as `--bridge-start-enabled`.

When present:

- register the configured global hotkey during startup;
- fail the helper process if registration fails;
- make the launcher declare readiness only after the helper survives registration.

The normal default remains bridge OFF unless an explicit startup mode requires ON.

## Local smoke action

Add a development-only local action source enabled only by an explicit smoke-mode switch.

It should provide one content-free synthetic `CREATE_AND_SERVICE` action with a known packet. The existing dispatch coordinator then exercises the production ordering:

`claim -> create/prepare browser target -> revalidate -> clipboard -> browser focus -> local prepared -> native foreground fallback`

Success is operator-visible immediately:

- clipboard contains the smoke packet;
- dedicated Firefox is OS foreground;
- diagnostics record local prepared;
- second press can return NO_ACTION.

No automatic paste or Enter is permitted.

## Stage-12 after smoke passes

Only after the local smoke loop is green should a later reviewed Stage-12 authority be created.

The Stage-12 Windows launcher must pass the explicit startup-enable switch and expose a readiness marker proving the helper survived hotkey registration before Linux is permitted to print the live-consumption marker.

## Production lifecycle direction

The production product should not require a giant PowerShell bootstrap.

Use a small per-user supervisor that remains available while the dispatch bridge can be ON or OFF. Expose only typed lifecycle controls:

- status
- online
- offline
- restart
- self-test

These can later be surfaced through a Workspace Control plugin/tool similarly to Heartbeat. The supervisor must not expose generic shell/process execution. Offline should unregister the hotkey and stop dispatch while leaving the bounded supervisor reachable, which avoids the problem of trying to remotely start a process that is completely absent.

## Authority gate

This file is review-only. It authorizes no source mutation and no live retry.

The current task's mutation scope does not include `operator-bridge/src/**` or `operator-bridge/tools/**`. Source implementation requires fresh operator approval for the exact file scope recorded in the v1.1 review artifact.
