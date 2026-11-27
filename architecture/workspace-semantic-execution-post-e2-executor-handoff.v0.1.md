# Post-E2 Executor Handoff — Workspace Semantic Execution Migration v1

**Task:** `workspace-semantic-execution-migration-v1`  
**Repository:** `adamtrott78/workspace-control`  
**Branch:** `workspace-semantic-execution-migration-v1`  
**PR:** #590  
**Durable E2 closeout head:** `090155abc1c943e629d2a9fa1e74c6cf2c8927f4`  
**Worker-result candidate head after E2:** `6115b48dfdf4a4954b3b1626598f897e4e71eeec`

This handoff is metadata on top of the accepted E2 closeout. A new executor must recover the current branch head and verify it descends from the E2 closeout head above before acting.

## Read first

- `procedures/task_capsule.md`
- `tasks/active/workspace-semantic-execution-migration-v1.json`
- `tasks/active/workspace-semantic-execution-migration-v1.md`
- `architecture/workspace-semantic-execution-research-iterate-e1-closeout.v0.4.json`
- `architecture/workspace-semantic-execution-research-iterate-e2-live-closeout.v0.2.json`
- `architecture/workspace-semantic-execution-research-iterate-e3.v0.1.json`

Trust those artifacts plus exact Git/runtime evidence over chat prose.

## Accepted milestones — DO NOT REDO

- D4 real-account Stage-12 calibration: PASS.
- E1 integrated Research-Iterate mixed workflow: PASS.
- E2-C1 deterministic recovery canary: PASS.
- E2-C2 PostgreSQL restart/recovery canary: PASS.
- E2 live fault-injection mission: PASS.

E2 proved real serviced worker/session/process loss, stale-result fencing, PostgreSQL rehydration, generation-1 replacement, Workspace Shell read-only probing, fan-in, synthesis and complete cleanup with no manual durable-state reconstruction.

## Exact E2 live evidence

Authority: `2970c9ab635a338826b66847d8deb51ad8769e3a` — consumed PASS.

Candidate chain from E1 baseline `fdb801d895068c78b2e2e11e6984173812884deb`:

1. root decomposition `a64deffc54a7f39b38169068549673c3434fdb9b`
2. stale generation-0 analysis `8d3648e16929d5397dd16f34bdf0cb1837f10fa9`
3. accepted generation-1 analysis `4f96d5c3a99414b1ff825c2668915b42fe1e50df`
4. Workspace Shell probe `f5a42fffde6d654b02631e576cd6378ac8939eb7`
5. synthesis `6115b48dfdf4a4954b3b1626598f897e4e71eeec`

The stale generation-0 result was observed and rejected without durable mutation. Process and session generation both advanced 0 -> 1. Runtime state was rebuilt from PostgreSQL. Final mission state was COMPLETED with four COMPLETED processes and zero unresolved work.

## Immediate next work: E3

Do **not** start with a live model run.

1. **E3-C1 — resource observer/accounting canary.**
   - Build a read-only, versioned JSON observer/report.
   - Capture CPU time, RSS/peak RSS (PSS when safely available), threads, FDs, managed children, phase durations, durable process/session/action counts and sampling gaps.
   - Prove observer-on vs observer-off does not change semantic state.
   - No GPU/NVIDIA/PADataset access.

2. **E3-C2 — bounded no-model soak.**
   - Repeated deterministic/fake-worker integrated cycles; zero model calls and zero human service.
   - Include at least one generation-recovery cycle.
   - Measure resource envelope and detect unexplained growth/leaks.
   - Require clean terminal task/action/session state and cleanup.

3. **E3-LIVE — only after C1/C2 PASS.**
   - Freeze exact review/procedure.
   - Stop at a fresh explicit operator approval gate.
   - Prefer instrumenting the accepted E2 topology so the live resource run exercises the hardest validated path.
   - Bind all measurements to exact source, authority and candidate heads.

## After E3

Proceed in order where gates allow:

- E4 calibrated economics comparison vs all-strong/frontier control.
- E5 authoritative target-machine UX-09 performance benchmark.
- E6 provenance/authority/rollback audit.
- E7 November acceptance-matrix reconciliation.
- E8 explicit `PROMOTE_V0`, `HOLD`, or `REVISE` verdict.

## Boundaries

- No automatic typing/paste/Enter/Send.
- No ChatGPT DOM/page-content/output scraping.
- No credential automation.
- No Funnel/public exposure.
- No paid-API fallback.
- No PADataset/GPU mutation.
- No Workspace Shell authority widening.
- No candidate-history rewrite.
- No stale-generation acceptance.
- Do not infer execution authority from model reasoning.
- Validate exact heads before promotion.

## New-chat bootstrap

Use connected GitHub, Heartbeat and Workspace Shell directly. Recover durable state before action; do not ask Adam to relay repository/runtime state those tools can read. Continue autonomously through repository-safe E3-C1/C2 work. Stop at the genuine fresh authority gate before E3-LIVE.
