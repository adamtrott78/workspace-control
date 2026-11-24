# Workspace Supervisor Chat v0.1

Status: **PROPOSED / NON-AUTHORITATIVE INTERFACE**

Parent task: `workspace-semantic-execution-migration-v1`

## Role

Workspace Supervisor is the human-facing conversational control surface for a large semantic-execution mission. It is intentionally separate from both the orchestration core and the mechanical Operator Console.

- **Operator Console:** “How many manual service cycles can I perform, and is the bridge healthy?”
- **Workspace Supervisor:** “What is the whole mission doing, why, what changed, what is blocked, what decision do you need from me, and what happens next?”

The Supervisor is not another orchestrator. It reads authoritative durable state, explains it, and may submit bounded candidate proposals through existing intake paths.

## Default executor

Use ChatGPT Instant / the lowest adequate reasoning tier by default. The Supervisor must not silently consume frontier reasoning merely because a mission is important.

When a question is intrinsically difficult, the Supervisor proposes or requests a stronger-reasoning process through the normal routing/escalation path. Importance alone is not an escalation criterion.

## Authority and truth boundaries

The Supervisor owns no task truth and no execution authority.

It MUST NOT:
- grant or widen Permission;
- remove Prohibition;
- satisfy ReviewRequirement;
- directly mutate authority artifacts or task capsules merely from conversational reasoning;
- invent execution authority from user enthusiasm or model judgment;
- own scheduler queues, leases, generations, retries, or durable worker state;
- treat conversation memory as authoritative;
- inspect or scrape ChatGPT worker-page content;
- infer completion from worker-chat UI state.

Conversation context is a cache only. Fresh durable state and exact provenance are authoritative.

If required durable state is unavailable, stale, contradictory, or outside the Supervisor's read authority, it fails closed and reports the exact blocker.

## Responsibilities

### 1. Formulation

Translate a broad human request into a candidate top-level objective, constraints, success criteria, evidence needs, and unresolved decisions.

The output is a proposal only. It enters the same reviewed candidate/intake path as any other proposed work.

### 2. Situation awareness

Answer, from durable state:
- What is the mission trying to accomplish?
- What is complete?
- What is running?
- What is waiting on an external event?
- What is blocked or failed?
- What is the current critical path?
- Which workers/executors are active?
- What validations have passed or failed?
- What resource/allowance pools are being consumed?
- What changed since the last report?

### 3. Human decision interface

Surface only genuine human judgment or authority gates. Each gate should state:
- the exact question;
- why human judgment is required;
- relevant evidence and constraints;
- available choices;
- consequences that are actually known;
- owning authority path.

Mechanical worker servicing remains the Operator Bridge's job.

### 4. Reporting and synthesis

Provide concise status and issue reports from validated durable evidence. Final mission conclusions must be synthesized from validated child results and provenance, not from remembered worker-chat prose.

## Read model

Introduce a non-authoritative `SupervisorReadModelPort` backed by projections of authoritative state.

Suggested queries:
- `GetMissionSummary`
- `GetCriticalPath`
- `GetActiveWork`
- `GetWaitsAndBlockers`
- `GetPendingHumanDecisions`
- `GetRecentValidatedChanges`
- `GetResourceUsage`
- `GetProvenanceTrail`

The projection is rebuildable and grants no authority.

## Proposal path

Introduce `SupervisorProposalPort` with proposal-only commands such as:
- `SubmitCandidateObjective`
- `SubmitCandidatePlanAdjustment`
- `SubmitCandidateHumanDecision`

These commands MUST enter the existing authority/intake workflow. They never directly execute an effect or alter authority state.

## Connected-tool routing

Worker/supervisor packets may prefix an objective with exact literal connected-tool names, for example:

```text
@github

<objective>
```

or, after empirical proof of the exact spelling:

```text
@Workspace Shell

<objective>
```

The packet compiler/caller must select mentions from required capabilities. A missing required connected tool is a fail-closed capability mismatch, not a reason to ask the human to manually relay logs, JSON, SHAs, or commands when an authorized connector should be used.

## Session/recovery model

A persistent Supervisor chat is useful for conversational convenience, but no mission state may exist only in that chat.

After a lost/reset/replaced Supervisor session:
1. re-read durable mission state;
2. reconstruct the read projection;
3. resume reporting/formulation without relying on prior chat memory.

This is the same durable-state-first principle used for workers.

## Initial acceptance tests

A read-only Supervisor prototype passes when a fresh Instant chat can answer all of the following from durable state without hidden chat history:
- “What is happening right now?”
- “What changed since the last validated checkpoint?”
- “Why are we blocked?”
- “What do you need from me?”
- “What is the next critical-path action?”
- “Which claims are validated versus merely proposed?”

It must also:
- survive chat/session replacement;
- preserve exact provenance in its report;
- make zero authority mutations;
- make zero worker-page inspections;
- correctly distinguish routine worker service from human judgment;
- remain useful when the active graph contains many concurrent leaves.

## Rollout

1. **S1 Read-only Supervisor:** durable mission status, critical path, blockers, provenance.
2. **S2 Formulation:** broad human request -> candidate objective through normal intake.
3. **S3 Judgment interface:** summarize and submit explicit human decisions to their owning gate.
4. **S4 Validated reporting:** final and interim mission synthesis from validated durable results.

The first production-like exercise should run alongside the integrated `research-iterate` proving workload after corrected D4 acceptance.
