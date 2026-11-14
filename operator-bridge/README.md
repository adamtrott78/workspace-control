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
