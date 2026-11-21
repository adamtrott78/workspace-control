# Workspace Operator Bridge

This tree implements the staged operator bridge defined by
`tasks/active/workspace-operator-bridge-implementation-v1.json`.

## Stage 01 status

Stage 01 is a **contract/build harness only**.

It contains:
- a .NET 10 solution skeleton;
- the WinForms helper project with no operator behavior yet;
- shared protocol identity constants;
- a Firefox MV3 manifest/background skeleton with no browser operations;
- an implementation copy of the frozen Browser Adapter Protocol v1 schema;
- MSTest project scaffolding;
- repository static tests for protocol drift, authority scope, Firefox permissions, and CI credential independence.

It intentionally does **not** implement hotkeys, clipboard writes, Native Messaging,
named pipes, browser lifecycle, simulator behavior, or ChatGPT account interaction.

## Build

From the repository root on Windows with .NET 10 installed:

```powershell
dotnet restore operator-bridge/WorkspaceOperatorBridge.slnx
dotnet build operator-bridge/WorkspaceOperatorBridge.slnx --configuration Release --no-restore
dotnet test operator-bridge/WorkspaceOperatorBridge.slnx --configuration Release --no-build
python -m unittest discover -s tests -p "test_workspace_semantic_execution_operator_bridge*.py" -v
```

The dedicated GitHub Actions workflow performs the same checks on
`windows-latest` and requires no account credentials.


## Per-user convenience commands

The Windows development/operator lifecycle can be exposed as persistent
current-user commands without administrator rights or PowerShell profile
execution. The installer places owned `.cmd` shims in
`%LOCALAPPDATA%\Microsoft\WindowsApps` only when that exact directory already
exists and is already present on the user's `PATH`; it never modifies `PATH`
or execution policy.

```powershell
& .\operator-bridge\tools\install-wop-commands.ps1
```

Installed commands:

- `wop-up [sha]` — start the existing Workspace Operator dev lifecycle.
- `wop-down` — stop only the recorded runtime-owned helper/Firefox tree.
- `wop-reset [sha]` — reset into the existing local smoke lifecycle.
- `wop-status` — report current content-free runtime status.
- `wop-self-test [sha]` — read-only verification of repository SHA, .NET 10,
  Node 24, Firefox availability, and current runtime health.
- `wop <action> [sha]` — retain the general reviewed lifecycle entrypoint.

Each shim launches a fixed current-user driver with `-NoProfile` and a
per-process `-ExecutionPolicy Bypass`; the installer never changes the user's
persisted execution policy. It also removes the obsolete owned v1 profile block
if a prior installation wrote one. It does not modify machine PATH, services,
scheduled tasks, machine-wide registry, browser profiles, credentials, or
execution authority. `install-wop-commands.ps1 -Remove` removes only files with
the exact Workspace Control ownership markers.
