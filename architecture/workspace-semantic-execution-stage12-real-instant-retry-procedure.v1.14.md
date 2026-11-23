# D4 Real-Instant Retry Procedure v1.14 — Q1 durable-intake observability + A6 plugin invariant

Status: **FROZEN VALIDATED REVIEW — NOT LIVE AUTHORITY**

## Consumed v1.13 result

v1.13 passed all pre-consumption gates, reached the live consumption point, and produced a valid Q1 candidate at:

- commit: `daa18627982a1d406eb88d44145113f0e99561e0`
- path: `worker-results/stage12/d85e6ca0d9484b4a98e8694e787d3505/q1.json`

After publication, the private Operator Bridge status remained:

`{"readyManualCycles":0,"sentUnconfirmed":1}`

for approximately ten minutes. That means Q1 remained in `AWAITING_DURABLE_ACK`; Q2 was never planned.

## Previously proven UX/plugin invariant

Do **not** redesign the operator UX.

A6 already proved literal raw `@github` in a Personalized Temporary Chat works with:

- `autocomplete_selection_used=false`
- no Tab
- no click
- no autocomplete selection

The accepted operator loop remains:

`Ctrl+Space -> Ctrl+V -> Enter`

A7 remains the accepted frontend/convenience-command packaging checkpoint.

## v1.14 repair

1. Preserve the immutable candidate history and advance the reviewed candidate baseline to `daa18627982a1d406eb88d44145113f0e99561e0`.
2. Resolve candidate branch head with `git ls-remote` before each fetch.
3. Fetch the branch and require fetched head == independently observed remote head.
4. Emit `STAGE12_Q1_CANDIDATE_OBSERVED=<sha>` when the Q1 commit is observed.
5. Emit `STAGE12_Q1_DURABLE_INGEST=PASS` only after WorkerResultIntakeService successfully transitions durable state.
6. Prefix Stage12 packet objectives with literal raw `@github`, requiring no human packet editing and no Tab/click/autocomplete selection.
7. Retain semantic backend repair, stale-route normalization, A7 frontend bytes, security boundaries, and append-only candidate semantics.

This review grants zero live authority.


## Exact-head validation

Frozen repair head: `70f8c21185dad6dc0be8c84a21fe8fd841a557b6`

- Workspace Control #3153 — SUCCESS
- Semantic Execution #455 — SUCCESS
- Operator Bridge #726 — SUCCESS

## Current operational gate

The v1.13 attempt is consumed and is still the source of the live/stuck runtime that reported:

`{"readyManualCycles":0,"sentUnconfirmed":1}`

Do not silently reuse v1.13. Stop/clean that runtime first. After cleanup evidence, stage exactly one fresh v1.14 authority; Adam already explicitly requested a repaired rerun in the handoff-preparation turn, but the authority artifact itself must still be newly created and exact-head validated.
