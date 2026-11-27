# Integrated Research-Iterate E1 Live Procedure v0.2

Status: **REVIEWED PROCEDURE CANDIDATE / NON-AUTHORITY**

Parent task: `workspace-semantic-execution-migration-v1`

## Frozen implementation basis

- corrected implementation head: `65bdef0e3572c5cfed8b8e59298ce86fc15b59af`
- candidate baseline: `8aacc7eebbbafabcb20b372aa53b88350a44e633`
- Workspace #3173 — SUCCESS
- Semantic #475 — SUCCESS
- Operator #746 — SUCCESS
- accepted A7 loop remains `Ctrl+Space -> Ctrl+V -> Enter`

## Launch after one-shot authority

The currently installed WOP driver may predate the `e1` action. After the exact E1 authority commit is 3/3 green and frozen, use one command line that first pins the local DevCheckout to that exact authority SHA, refreshes only Workspace-Control-owned WOP shims, then launches E1 pinned to the same SHA:

```powershell
$W=Join-Path $env:LOCALAPPDATA 'WorkspaceControl\OperatorBridge\DevCheckout'; wop status <E1_AUTHORITY_SHA>; & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $W 'operator-bridge\tools\install-wop-commands.ps1'); wop e1 <E1_AUTHORITY_SHA>
```

The refresh preserves `wop d4`, lifecycle commands, and the accepted A7 frontend. It only rewrites the current-user Workspace-Control-owned command driver/shims.

## Expected service points

1. root decomposition — Instant;
2. deterministic exact-source leaf — no human action;
3. analysis — Instant;
4. Workspace Shell read-only probe — Instant;
5. final synthesis — Instant.

For every Instant service point: `Ctrl+Space -> Ctrl+V -> Enter`. No Tab, autocomplete selection, packet editing, automatic submission, or page-content scraping.

## Workspace Shell

The probe packet begins with literal `@Workspace Shell` then `@github`. It may call only `workspace_shell_inspect` with task `workspace-semantic-execution-migration-v1`, target `workspace-shell`, operation `runtime_inventory`. `workspace_shell_exec` and `workspace_shell_run_reviewed_helper` are prohibited.

## Success

Success requires `E1_RESEARCH_ITERATE` with `result=PASS`, including root decomposition, inherited child contracts, deterministic exact-source validation, Instant analysis, the read-only Workspace Shell probe, fan-in, final Instant synthesis, and Supervisor S1 fresh-store rehydration.

Any failure after `E1_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS` consumes the one-shot authority. No silent retry.
