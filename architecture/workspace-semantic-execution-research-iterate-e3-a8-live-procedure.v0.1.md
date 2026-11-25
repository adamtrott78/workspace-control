# E3-A8 Live Retry Procedure v0.1

Status: **FROZEN EXECUTABLE REVIEW / ZERO LIVE AUTHORITY**

This procedure prepares a successor retry of the consumed E3-LIVE attempt. It does not authorize execution.

## Frozen dependencies

- Consumed predecessor authority: `1f6d3639ade8469ca2a7caeab4a9fbdc1fba881d` — non-reusable.
- Failed-run candidate head / retry baseline: `fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f`.
- Validated A8 frontend review: `6fb315884804214f96ca0f7264a48eed40741a60`.
- Validated A8 frontend source: `b97a4c7b9309d413ced7eea14fe87b5864ad0c5b`.
- Validated E3-A8 operator transport: `55edb7a6e618f5a49ddf17ec5c9426f70fa08f2d`.
- Accepted E2 topology blob: `d6acd6a4266641813deecb900b877b7250b02530`.
- Resource observer blob: `458a869252f108bea52952e12852961bc3158d1f`.

## Human service sequence

The frontend remains manual and content-blind. At each service point use only:

**Ctrl+Space -> Ctrl+V -> Enter**

1. root decomposition
2. analysis generation 0
3. analysis generation 1 replacement
4. Workspace Shell read-only probe
5. final synthesis

No automatic paste, typing, Enter, Send, mouse input, DOM inspection, or ChatGPT page-content scraping is permitted.

## Pending-action repair invariant

An HTTP 204 claim means only that there is no *new* claimable action. The A8 client synchronously refreshes content-free workload counters before returning NoAction. If `SentUnconfirmed > 0`, the frontend must not say "Nothing needs service" and must not minimize the worker; it may only refocus the trusted prepared worker and warn that durable acknowledgement remains pending.

## Future authority contract

A future authority must be a new one-shot artifact at:

`architecture/workspace-semantic-execution-research-iterate-e3-a8-live-authority.v0.1.json`

It must bind the exact validated review head, A8 frontend review/source, operator transport, wrapper/E2/observer blobs, and candidate baseline above. The Linux transaction validates that artifact before emitting:

`E3_A8_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`

After that marker, success or failure consumes the future authority. No silent retry.

## Current stop

**Live attempts authorized by this review alone: 0.**

After this review's exact head is 3/3 green, stop and require fresh explicit operator approval for exactly one E3-A8 live retry.
