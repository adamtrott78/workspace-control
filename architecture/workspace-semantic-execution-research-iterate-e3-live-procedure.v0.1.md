# Workspace Semantic Execution — E3-LIVE Procedure v0.1

Status: **FROZEN / ZERO LIVE AUTHORITY**

This procedure is repository-safe to review and validate. It does **not** authorize a live ChatGPT mission.

## Bound sources

- Accepted E2 topology: `benchmarks/workspace-semantic-execution/live_research_iterate_e2.py`, blob `d6acd6a4266641813deecb900b877b7250b02530`.
- Read-only resource observer: `benchmarks/workspace-semantic-execution/resource_observer_v1.py`, blob `458a869252f108bea52952e12852961bc3158d1f`.
- E3 live instrumentation wrapper: `benchmarks/workspace-semantic-execution/live_research_iterate_e3.py`, blob `51e471886a4911c9f00d824316c600bf8f8fae19`.
- Validated C2 source: `e14e71d1981a4aedbe9af75a54087683fe4718e1`.
- Worker-result candidate baseline: `6115b48dfdf4a4954b3b1626598f897e4e71eeec`.

The exact commit containing this procedure and its paired review becomes the `review_head` only after required exact-head validations succeed.

## Pre-authority verification

1. Recover PR #590 and verify the branch descends from the validated C2 source.
2. Verify this procedure, the paired E3-LIVE review, the wrapper blob, E2 topology blob, observer blob, and candidate baseline exactly.
3. Verify all required validations for the exact review head are SUCCESS.
4. Verify `worker-result-candidates-v1` is still exactly at the frozen candidate baseline unless a newer authority-owned append-only handoff explicitly supersedes it.
5. Verify there is no unconsumed E3-LIVE authority.
6. Verify no Workspace Shell helper/trust/privilege change is required by this mission.

## STOP_AT_AUTHORITY_GATE

**NO LIVE AUTHORITY EXISTS.**

After the review head is validated, stop here. A fresh, explicit operator approval from Adam is required for exactly one E3-LIVE attempt. Model reasoning, review completion, CI success, prior D4/E1/E2 approvals, or prior “always approved” statements do not create this authority.

## Post-approval steps — only after fresh explicit approval

1. Create exactly one one-shot E3-LIVE authority artifact bound to:
   - exact validated `review_head`;
   - exact E3 wrapper blob;
   - exact E2 topology blob;
   - exact observer blob;
   - exact candidate baseline;
   - exact permitted live mission and cleanup/rollback paths.
2. Validate the authority artifact on its exact head before execution. Do not reuse any D4/E1/E2 authority.
3. Execute the already-accepted Windows Operator frontend and reviewed Linux private route without changing the A7 manual-input semantics.
4. Launch the E3 wrapper with required exact `source_head`, `review_head`, `authority_head`, and `candidate_baseline` bindings. The wrapper samples read-only resource/task state while the unchanged E2 topology runs.
5. Human service remains manual: Ctrl+Space may focus/stage; Ctrl+V and Enter remain human actions. The system must never auto-type, auto-paste, auto-press Enter, or scrape ChatGPT page content.
6. The mission must exercise root decomposition, deterministic exact-source read, generation-0 analysis, deliberate loss/fence, PostgreSQL rehydration, generation-1 replacement, read-only Workspace Shell probe, fan-in, and synthesis.
7. Capture the emitted `E3_LIVE_RESOURCE_REPORT`, candidate append-only commits, phase timing, durable-state projection, sampling gaps, and exact source/review/authority/candidate bindings.
8. Tear down the private route/server and return Windows Operator to OFFLINE on success or failure.
9. Verify no ready/manual, sent-unconfirmed, awaiting-ack, unreaped managed process, or unresolved task/session/action state remains.
10. Persist an E3-LIVE closeout only from exact tool evidence. There is no automatic retry; a failed/consumed authority is non-reusable.

## Safety invariants

No GPU/NVIDIA telemetry. No PADataset access or mutation. No paid API fallback. No browser DOM/page-content/output scraping. No automatic input. No public/Funnel exposure. No candidate-history rewrite. No stale-generation acceptance. No Workspace Shell authority widening. No execution authority inferred from model reasoning.
