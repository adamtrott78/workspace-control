# Instant Worker Orchestration v0.1

Status: DESIGN NOTE / NON-AUTHORITATIVE  
Date: 2026-11-01  
Repository base: `d47a7922aa8d47d3a22b55c19ce4d6af7309a964`

## Purpose

Record the observed capability boundary of ChatGPT Instant as a Workspace Control worker, the current supported transport paths, the desktop-launcher research idea, and the next capability benchmarks.

This document does **not** create execution authority, modify task authority, grant runtime privileges, or replace existing Workspace Control policy.

## Proven capability evidence

### Benchmark 1: end-to-end Instant worker transport

PR #574: `Instant worker smoke benchmark v1`

Observed result: `FULL_LOOP_PASS`

Exact evidence:
- base main SHA: `d47a7922aa8d47d3a22b55c19ce4d6af7309a964`
- initial write commit: `8f3c8921ec11a0692c31b0ae2be9df9cc2f99eff`
- final write commit: `3c0d88a1322a387526ebf34ceaf23485f13a1c8e`
- Workspace Shell expected/observed SHA: `01a95b61410e2f427b9885a19e6a0b9c5ee60a38`
- Workspace Shell receipt: `job-cb71f3fa-a5c6-41d2-82ee-0f3bf2d463d2`
- Workspace Shell authorization: `ALLOW`
- Workspace Shell execution: unprivileged `git-read`, exit code 0
- main unchanged
- one changed benchmark artifact
- no manual state relay required

Capability demonstrated:

`GitHub read -> GitHub write -> Workspace Shell bounded execution -> durable receipt readback -> GitHub evidence update -> draft PR`

### Benchmark 2: autonomous coding and CI repair

PR #575: `Instant autonomous coding benchmark v1`

Observed result: `AUTONOMOUS_GREEN_PASS`

Exact evidence:
- base main SHA: `d47a7922aa8d47d3a22b55c19ce4d6af7309a964`
- initial failed head: `5a6d09ffe17c44b2cf2074e50074757878b14956`
- initial failed Workspace Control Validation: `41360553663`
- failure: `ModuleNotFoundError: No module named 'pytest'`
- repair: benchmark tests rewritten to use standard-library `unittest`
- final validated head: `31dbce01278952de9cf5009f9a305cf590a40741`
- successful Workspace Control Validation: `41360610899`
- durable result comment: `6565285424`
- repair iterations: 1
- exactly two benchmark files changed
- main unchanged
- no manual workflow dispatch
- no Workspace Shell use
- no manual state relay required

Capability demonstrated:

`read -> implement -> commit -> draft PR -> observe exact-head CI -> retrieve failure evidence -> diagnose -> repair -> revalidate -> durable result writeback`

## Current working model

Instant is now empirically suitable as a **bounded interactive worker candidate**, not merely as a summarization tier.

Current demonstrated functions:
- repository/task inspection;
- branch-aware GitHub retrieval;
- bounded task decomposition;
- distinction between `DECOMPOSE_AGAIN` and `ESCALATE_REASONING`;
- GitHub branch/file/PR mutation;
- Workspace Shell bounded read/exec and receipt verification;
- tool-to-tool durable state transport;
- source and test authoring;
- CI observation;
- log-driven failure diagnosis;
- autonomous repair;
- exact-head revalidation;
- durable result persistence.

The model must still be treated as non-authoritative. Model-generated plans and candidate actions do not create execution authority.

## Global Chat trigger

The ChatGPT custom-instruction trigger is:

`WORKSPACE_INSTANT_WORKER_V1`

Intended effect:
- keep ordinary chats ordinary unless explicitly triggered;
- prefer connected tools over manual relay;
- preserve provenance, exact SHA bindings, inherited invariants, and authority boundaries;
- fail closed on missing authority;
- recursively decompose tasks that are too large;
- escalate tasks that are intrinsically too difficult;
- persist durable results directly when an authorized path exists;
- avoid charts/images/interactive UI unless explicitly requested.

Custom instructions are behavioral defaults only. They do not grant tool permission or execution authority.

## Human-triggered Instant launch problem

Current friction:
- starting a fresh Instant chat is easy;
- repeatedly attaching GitHub and Workspace Shell is annoying;
- no supported programmatic `spawn Instant chat` interface is presently assumed by Workspace Control.

Desired future experience:

`next eligible action -> one local hotkey -> fresh Instant chat prepared with worker packet -> user submits -> worker executes -> durable result returns to Workspace Control`

The user should not need to copy JSON, SHAs, logs, commands, or receipts between systems.

## Desktop launcher research direction

A future local `instant-worker-launcher` may:
1. query Workspace Control for the next eligible candidate action;
2. render a compact worker packet;
3. place the packet into the system clipboard;
4. open/focus ChatGPT Desktop;
5. prepare a new chat at the Instant setting where supported;
6. minimize human interaction to the explicit submission action.

The launcher should **not** be treated as an unofficial unattended ChatGPT API.

Do not build the architecture around machine-scale UI farming, output scraping, account-limit circumvention, or assumptions that consumer Chat can be programmatically spawned without an official interface.

The supported architectural fallback remains:
- Instant for human-triggered interactive workers;
- local/free-hosted inference for machine-triggered workers;
- frontier models for hard escalation.

## Long-term orchestration model

```
Goal / ontology task graph
        |
        v
deterministic eligibility + authority evaluation
        |
        v
executor routing
  |        |         |          |
  v        v         v          v
deterministic  Instant  local/free  frontier
                  |
                  v
          GitHub / Workspace Shell
                  |
                  v
          validators / GitRunner
                  |
                  v
           durable evidence
                  |
                  v
          next graph transition
```

Instant can propose, decompose, implement, validate, and persist evidence. Authority-owned policy remains responsible for ALLOW/DENY decisions.

## Remaining unproven capabilities

The current evidence does **not** yet prove:
- multi-leaf queue execution in one Instant session;
- dependency-aware scheduling across multiple leaves;
- preservation of inherited invariants across a deeper recursive task tree;
- clean handling of mixed outcomes where some leaves are executable and one requires escalation;
- bounded retry policy across multiple failures;
- direct end-to-end useful GitRunner task execution under existing task authority;
- reliable selection between Instant, local, free-hosted, and frontier executors based on empirical success data;
- supported programmatic creation of fresh Instant Chat sessions.

## Recommended next benchmark

### INSTANT_MULTI_LEAF_QUEUE_V1

Purpose:
prove whether one Instant conversation can behave as a bounded worker process over several eligible actions without user relay.

Recommended structure:
- 4 to 6 candidate actions;
- dependency DAG, not a flat list;
- at least two independent executable leaves;
- one leaf that requires decomposition;
- one leaf that should explicitly return `ESCALATE_REASONING`;
- objective validators for executable leaves;
- bounded maximum attempts per leaf;
- exact durable state after every transition;
- no production authority;
- no merge;
- no manual workflow dispatch;
- no manual user relay.

Required behaviors:
1. inspect durable queue;
2. choose only an eligible action;
3. preserve inherited invariants;
4. perform the action;
5. validate exact resulting state;
6. persist completion/failure evidence;
7. select the next newly eligible action;
8. decompose oversized work rather than forcing execution;
9. escalate intrinsically difficult work rather than repeatedly retrying;
10. stop only when queue is complete, blocked by real authority, or escalation is required.

Primary measurement:
whether Instant behaves like a stateful worker over a bounded queue rather than as a single-shot coding assistant.

## Benchmark sequence after multi-leaf queue

If `INSTANT_MULTI_LEAF_QUEUE_V1` passes:

1. `INSTANT_DEPENDENCY_DAG_V1`
   - larger dependency graph;
   - verify correct ordering and safe parallelism judgment.

2. `INSTANT_GITRUNNER_LEAF_V1`
   - one genuinely useful low-risk GitRunner-mediated leaf;
   - existing authority only;
   - no new authority inferred by the model.

3. `INSTANT_ESCALATION_CALIBRATION_V1`
   - controlled mix of easy, oversized, and intrinsically difficult tasks;
   - score false escalation and unsafe under-escalation.

4. `INSTANT_CONTEXT_LIMIT_V1`
   - progressively increase repository/task context;
   - determine where invariant retention or implementation quality degrades.

5. `INSTANT_LAUNCHER_RESEARCH_V1`
   - evaluate supported desktop launch/deep-link/automation surfaces;
   - target one-click human-triggered worker creation;
   - do not assume unattended consumer-UI automation is acceptable or stable.

## Design conclusion

The two completed benchmarks justify treating Instant as a serious candidate worker tier.

The immediate next question is no longer whether Instant can use tools or write code. The next question is:

**Can one Instant session safely process a dependency-aware queue of heterogeneous bounded actions while preserving authority, provenance, and escalation discipline?**
