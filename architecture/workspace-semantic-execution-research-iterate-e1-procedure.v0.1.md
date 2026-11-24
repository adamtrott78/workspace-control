# Integrated Research-Iterate E1 Live Procedure v0.1

Status: **REVIEWED PROCEDURE CANDIDATE / NON-AUTHORITY**

Parent task: `workspace-semantic-execution-migration-v1`

## Purpose

Run exactly one production-like E1 mission through the accepted Operator Bridge after a separately persisted one-shot E1 authority is exact-head 3/3 green.

## Frozen implementation basis

- implementation head: `aaa64ec83165f8761e6511ff4a766cd3c88e32ec`
- candidate baseline: `8aacc7eebbbafabcb20b372aa53b88350a44e633`
- Workspace #3168 — SUCCESS
- Semantic #470 — SUCCESS
- Operator #741 — SUCCESS

## One-time local WOP command refresh

The installed Windows driver predates the `e1` action. After the exact E1 authority commit is green and frozen, refresh the owned WOP command shims from that exact authority checkout, then use `wop e1`.

The refresh changes only the current-user Workspace Control-owned command shims/driver and must preserve existing `wop d4`, lifecycle commands, and the accepted A7 frontend.

## Human service loop

For every E1 Instant action:

`Ctrl+Space -> Ctrl+V -> Enter`

No Tab, autocomplete selection, packet editing, automatic typing, automatic submission, or ChatGPT DOM/page-content scraping.

Expected manual Instant service points are:
1. root decomposition;
2. analysis;
3. Workspace Shell read-only probe;
4. final synthesis.

The deterministic exact-source leaf requires no manual service.

## Workspace Shell probe

The packet begins with literal `@Workspace Shell` followed by literal `@github`.

It may call only:
`workspace_shell_inspect(task_id="workspace-semantic-execution-migration-v1", target="workspace-shell", operation="runtime_inventory")`

`workspace_shell_exec`, `workspace_shell_run_reviewed_helper`, service mutation, repository mutation, privileged execution, and authority widening are prohibited.

The expected runtime-inventory values are validator-side evidence and are not disclosed in the worker packet. GitHub is allowed only for immutable candidate publication, not to discover those expected values.

## Supervisor S1

E1 also proves the first Supervisor slice as a durable, read-only projection. A fresh PostgresStateStore instance reconstructs mission state after decomposition and again after final completion. Conversation memory is not authoritative and the projection records zero authority mutations.

## Success

Success requires `E1_RESEARCH_ITERATE` with `result=PASS`, including root decomposition, child inheritance, deterministic exact source, Instant analysis, Workspace Shell read-only probe, fan-in, Instant synthesis, and Supervisor S1 fresh-store rehydration.

Any failure after the future E1 live-consumption marker consumes the one-shot authority. No silent retry.
