# D4 Real-Instant Retry Procedure v1.9 — post-A7 backend revalidation

Status: **REVIEW CANDIDATE — NOT LIVE AUTHORITY**

The accepted Workspace Operator Bridge frontend remains frozen at `a9532ca8b86b7839822939a970e16af1d4a41864`.

## v1.8 failure

The v1.8 live attempt reached the accepted A7 frontend. Runtime evidence proved that the helper was alive in the same interactive Windows session, the bridge was enabled, the Firefox adapter connected, and physical Ctrl+Space presses generated dispatch attempts.

Every observed dispatch failed with `HttpRequestException` before an `actionId` was returned. Therefore browser creation, clipboard staging, and foregrounding were never reached.

Later read-only probes from the same Windows host showed both PowerShell `Invoke-WebRequest` and .NET `HttpClient` reaching the Tailscale hostname but receiving Jupyter `404 Not Found`, proving the temporary `/operator-bridge/v1` Serve route had been removed and the original Jupyter root restored by diagnosis time.

The historical helper diagnostic normalizes the HTTP failure to `HttpRequestException`, so the evidence does **not** prove whether route loss had already happened at the Q1 keypress or whether the claim endpoint returned a different non-success HTTP status.

The v1.8 authority is consumed and non-reusable.

## v1.9 repair

v1.9 changes only D4 outer orchestration. The accepted A7 frontend tree and `workspace-operator-dev.ps1` bytes remain unchanged.

After A7 `online` returns, before printing `D4_ACCEPTED_FRONTEND_READY=PASS`, D4 must:

1. refresh the remote SSH process and fail if it exited during A7 startup;
2. GET `/operator-bridge/v1/status`;
3. require HTTP 200 and valid Operator Bridge JSON;
4. require nonnegative `readyManualCycles` and `sentUnconfirmed`;
5. require `readyManualCycles >= 1`;
6. print `D4_BACKEND_REVALIDATED_AFTER_FRONTEND_START=PASS` before frontend-ready.

While the live remote process remains active, D4 periodically rechecks the status route. If the route disappears or returns invalid/non-200 content, D4 fails visibly with `D4_OPERATOR_BACKEND_ROUTE_LOST` rather than leaving the operator with an apparently inert Ctrl+Space loop.

## Exact source candidate

- Source: `3986cbcb547e71c99c008cc22aad463df8165954`
- Workspace Control #3125: SUCCESS
- Semantic Execution #425: SUCCESS
- Operator Bridge #698: SUCCESS
- A7 source tree: `51480cc44f62d661421e975e67af127ecd0b0417`
- A7 dev harness: `ac035d2fc898274c32cad43954ce44c15b198207`
- D4 wrapper: `87e2b22d010adcefde075089156ec4c8d3974964`

## Authority boundary

Live attempts authorized by this review alone: **0**.

Before any v1.9 live retry:

- clean the remaining v1.8 Windows runtime with the accepted `wop-down` path and verify OFFLINE;
- freeze and validate the v1.9 review state;
- create a fresh one-shot authority only after explicit operator approval;
- no silent retry and no reuse of v1.8 authority.
