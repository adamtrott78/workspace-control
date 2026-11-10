# ADR — Dedicated Firefox WorkspaceWorkers Profile v0.1

Status: **ACCEPTED FOR UX DESIGN BASELINE / PERFORMANCE SUBJECT TO UX-09**

Parent: `workspace-semantic-execution-migration-v1`

## Context

The user uses Chrome for normal browsing and wants worker automation isolated, low-friction, and resource-bounded.

Worker sessions need:
- predictable browser ownership;
- dedicated extension configuration;
- deterministic worker-window discovery;
- tab discard/retire policy;
- separation from ordinary tabs and extensions.

## Decision

Use a dedicated Firefox profile, provisionally named:

`WorkspaceWorkers`

Chrome remains the user's normal/default browser.

Only the dedicated Firefox profile participates in operator-bridge browser management.

The extension MUST NOT adopt arbitrary ChatGPT tabs from normal browser profiles as worker sessions.

## Consequences

Positive:
- isolates worker lifecycle from normal browsing;
- allows aggressive worker-specific memory policies;
- reduces wrong-tab risk;
- deterministic extension/profile configuration;
- easier RAM benchmarking;
- clearer recovery after Firefox restart.

Costs:
- additional browser installation/profile lifecycle;
- separate login/session context;
- possible reauthentication events when creating/recovering workers;
- Firefox may or may not use less RAM than Chrome and must be measured.

## Rejected alternatives

### Use normal Chrome profile
Rejected because worker tabs would mix with daily browsing, increase wrong-tab risk, complicate extension scope, and interfere with the user's normal environment.

### Use normal Firefox profile
Rejected because the dedicated worker environment is itself a useful isolation and recovery boundary.

### Assume Firefox is lighter than Chrome
Rejected as an architectural assumption. UX-09 must measure actual memory/latency.

## Revisit conditions

Revisit if:
- Firefox worker workload fails the measured resource budget;
- another browser provides materially better resource behavior while satisfying the same adapter contract;
- a supported non-browser Chat executor removes the need for persistent browser sessions.

