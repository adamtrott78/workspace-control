# Workspace Semantic Execution Session Broker v0.1

Status: **UX-04 SESSION-LIFECYCLE DESIGN CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Companions:
- `architecture/workspace-semantic-execution-operator-session-schema.v0.2.json`
- `architecture/workspace-semantic-execution-session-broker-policy.v0.1.json`
- `architecture/workspace-semantic-execution-session-decision-table.v0.1.json`
- `architecture/workspace-semantic-execution-operator-state-machine.v0.2.md`

## 1. Purpose

The session broker decides whether a Chat worker should be:

- REUSED;
- RESTORED from a discarded tab;
- CREATED;
- ROTATED;
- RETIRED;
- or BLOCKED/RECOVERED.

It owns **logical session policy**, not Firefox tabs.

The design goal is to maximize safe persistent-session reuse so the operator creates as few new chats as practical, while preserving durable recovery and isolation.

## 2. Core model

A logical worker session is identified by:

```text
worker_slot_id + generation
```

Example logical slots:

```text
instant-general-1
instant-general-2
critic-1
synthesizer-1
```

These names are deployment/profile examples, not closed core enums.

The actual durable record carries:
- session class;
- role;
- task/process affinity;
- executor requirement;
- continuity state;
- last acknowledged checkpoint;
- usage/context pressure;
- lifecycle intent.

Firefox `tabId` and `windowId` are not part of durable identity.

## 3. Slot classes

### GENERAL_PERSISTENT

Default production Instant worker.

May process multiple compatible reasoning quanta for one task affinity epoch.

Default policy:
- pinned to one task at a time;
- may serve sibling reasoning processes when isolation permits;
- does not cross into an unrelated task without rotation.

Initial pool target:
- 2 live general slots.

This is a UX/resource target, not a hard kernel limit.

### ROLE_ISOLATED_PERSISTENT

Used when independence/role isolation matters, but every quantum does not require a fresh conversation.

Examples:
- critic;
- synthesizer;
- specialized reviewer.

Pinned to:
- one task;
- one role;
- any narrower process isolation required by workflow.

Allocated on demand.

### FRESH_PER_QUANTUM

Used only when explicitly required.

Every reasoning quantum gets a fresh conversation/generation.

Examples:
- frozen benchmark treatment;
- contamination-sensitive workflow;
- explicit policy.

This is not the production default.

### EPHEMERAL_RECOVERY

Temporary session generation created while recovering continuity.

It exists so recovery can be explicit without pretending the old persistent chat is still trustworthy.

## 4. Affinity model

Persistent sessions are optimization caches, so they need contamination boundaries.

Default production rule:

> One persistent conversation is pinned to one task-affinity epoch.

Within that task, reuse may span sibling ReasoningProcesses if the isolation scope allows.

An unrelated task does **not** inherit an existing conversation merely because the executor/model matches.

Cross-task reassignment causes rotation/new generation.

This minimizes hidden conversational contamination while retaining the benefit of multi-quantum continuity.

## 5. Isolation scopes

### NONE

Compatible sibling reasoning processes inside the same task may share the session.

### ROLE

Only work with the same role may reuse the session.

### PROCESS

Only the same ReasoningProcess may reuse the session.

### TASK

Any compatible work within the same task may reuse the session, but nothing outside it.

### FRESH_QUANTUM

No reuse. New conversation/generation every quantum.

The workflow/ReasoningRequirement chooses isolation scope. The session broker enforces it.

## 6. Reuse eligibility

A session is reusable only if all of the following hold:

1. continuity is `TRUSTED`;
2. status is `ACTIVE`, `IDLE`, or `DISCARDED`;
3. generation is current;
4. no lifecycle intent requires rotate/retire;
5. executor requirement is compatible;
6. role/isolation requirements are satisfied;
7. task affinity matches;
8. process affinity satisfies isolation scope;
9. no explicit fresh-session policy applies;
10. browser preparation can target a safe managed binding or a safe restore path exists.

If any hard requirement fails, reuse is forbidden.

## 7. Continuity semantics

### NOT_ESTABLISHED

A newly allocated generation exists, but it has not yet produced its first valid durable worker acknowledgment.

It cannot be treated as a proven persistent worker until first acknowledgment.

### TRUSTED

The generation has a valid durable acknowledgment chain and no continuity-invalidating event has occurred.

This permits reuse.

### UNKNOWN

An event occurred that means conversation continuity cannot be trusted.

Examples:
- profile-wide login refresh;
- Firefox restart with no provable binding recovery;
- local tab identity lost;
- operator reports visible logout/refresh ambiguity.

UNKNOWN is **not reusable**.

### LOST

Continuity is known to be unavailable.

Examples:
- tab/session definitively destroyed;
- explicit sign-out/continuity loss;
- old generation replaced.

LOST is not reusable.

## 8. Establishing TRUSTED continuity

The broker does not infer continuity merely because a page is open.

A new generation becomes TRUSTED after:
- the worker receives its bootstrap/resume packet manually;
- a valid durable worker transition is observed for that exact generation;
- no continuity-invalidating event is active.

Thus the first durable acknowledgment is the continuity proof.

Subsequent valid durable acknowledgments reinforce, but do not create authority beyond, the session's existing contract.

## 9. Browser binding lifecycle

Local browser binding is:

```text
logical slot + generation
        ↕
Firefox managed tab/window binding
```

The Firefox side may classify a local binding as:
- ACTIVE;
- DISCARDED;
- MISSING;
- AMBIGUOUS.

Policy:
- ACTIVE + trusted logical session → reuse candidate;
- DISCARDED + trusted logical session → restore candidate;
- MISSING/AMBIGUOUS → do not guess from title; attempt reviewed binding recovery;
- if exact recovery cannot be proven → continuity UNKNOWN → rotate/recreate.

UX-12 will decide the concrete local binding proof mechanism.

## 10. Context-pressure policy

Because v0 does not inspect ChatGPT conversation contents, context pressure uses only data we control/observe durably:

- number of reasoning quanta;
- estimated tokens in packets we sent;
- estimated tokens in durable worker outputs;
- validator-repair history.

It MUST NOT scrape the ChatGPT DOM or depend on hidden token counters.

Context pressure is executor-profile calibrated.

Initial calibration seeds:

- observe carefully after ~12 reasoning quanta;
- hard fallback rotation by ~24 quanta if no better calibrated signal exists;
- soft rotation after 2 consecutive validator-repair cycles attributable to session confusion/context degradation.

These are **not frozen production thresholds**. GPT-6 calibration and UX-11 usability evidence may move them.

The goal is not “rotate frequently.” The goal is:

> reuse persistent chats until evidence says continued reuse is less reliable than a durable-state restart.

## 11. Hard rotation conditions

Rotate/recreate when:

- continuity is UNKNOWN or LOST;
- model/surface/toolset becomes incompatible;
- workflow requires a fresh chat;
- role/process isolation would be violated;
- authentication refresh invalidates the profile continuity domain;
- binding is lost and cannot be safely restored;
- user explicitly requests rotation.

Hard rotation is correctness-driven.

## 12. Soft rotation conditions

Rotate at a safe boundary when:

- context-pressure threshold is reached;
- validator repair streak suggests degraded continuity;
- affinity change risks contamination;
- resource policy favors replacement.

Soft rotation is optimization-driven and should not interrupt an already valid worker quantum.

## 13. Discard versus retire

### DISCARD

Use when:
- session is TRUSTED;
- currently idle;
- likely reusable;
- RAM should be reclaimed.

Discard unloads the Firefox tab but preserves the logical session/generation.

Next service uses `RESTORE_AND_SERVICE`.

### RETIRE

Use when:
- generation is replaced;
- task affinity epoch is over;
- session cannot serve planned work;
- user/policy explicitly retires it.

Retired generation is never reused.

## 14. Authentication refresh invalidating all tabs

This is the profile-wide recovery policy.

When UX-07 eventually emits an authoritative local recovery signal such as:

`AUTH_REFRESH_ALL_TABS_REPORTED`

the session broker treats the entire `WorkspaceWorkers` authentication domain as suspect.

Policy:

```text
1. Freeze reuse of every affected session generation.
2. Mark affected continuity = UNKNOWN.
3. Re-read durable state for each outstanding OperatorAction.
4. If an expected durable ack already exists:
      accept/complete that action normally.
5. If no ack exists:
      do not resend into the old generation.
      supersede the unresolved old-generation action.
6. Advance affected logical session generations.
7. Build replacement sessions from each last acknowledged durable checkpoint.
8. Generate new CREATE_AND_SERVICE/RESTORE actions as appropriate.
9. Old refreshed tabs are untrusted remnants and may be retired later.
```

Important consequence:

A late old-generation worker result can be preserved as evidence, but generation fencing prevents it from advancing current state.

This is what makes “login refreshed every tab” survivable without manually reconstructing which workers were doing what.

## 15. Outstanding action interaction

A session with an action in `AWAITING_DURABLE_ACK` is not automatically reusable for another packet unless the workflow explicitly models multi-message concurrency for that session.

Default v0 policy:
- one outstanding worker packet per logical chat session at a time.

This keeps acknowledgment mapping simple and prevents the human from stacking prompts into a still-running chat.

Independent sessions can still be serviced in parallel.

## 16. Allocation algorithm

Given a ready reasoning packet:

```text
1. Resolve executor requirement + task/role/process isolation.
2. Find TRUSTED compatible ACTIVE/IDLE session.
      → SERVICE_EXISTING
3. Else find TRUSTED compatible DISCARDED session.
      → RESTORE_AND_SERVICE
4. Else find available logical slot / allocate a new generation.
      → CREATE_AND_SERVICE
5. Else identify a safe rotate/retire candidate.
      → queue atomic maintenance action(s), requery, then CREATE_AND_SERVICE
6. If continuity/binding/auth state is ambiguous:
      → OPEN_RECOVERY / fail closed.
```

The user never chooses among these branches.

## 17. Active-pool strategy

Initial design target:

- 2 `GENERAL_PERSISTENT` live slots;
- role-isolated slots only while needed;
- unused trusted slots may be DISCARDED;
- old/incompatible generations are RETIRED.

Why two general slots:
- lets one worker remain SENT/UNCONFIRMED while another independent worker is serviced;
- bounds RAM;
- reduces new-chat frequency.

UX-09 must measure memory before this is frozen.

## 18. Login/restart philosophy

Persistent conversation continuity is valuable but never irreplaceable.

The system should prefer:
- preserving trusted sessions when evidence supports them;
- recovering browser bindings when exact proof exists;
- otherwise rotating rather than guessing.

The operator should never be asked to inspect all worker tabs and decide which conversations survived.

That is a session-broker decision based on durable generations and explicit recovery signals.

## 19. UX-04 acceptance assessment

UX-04 now defines:

- persistent session classes;
- default two-general-slot pool target;
- role/task/process affinity;
- reuse compatibility;
- continuity establishment/invalidation;
- one-outstanding-packet-per-session default;
- context pressure and rotation;
- discard vs retire;
- browser-binding recovery policy;
- profile-wide authentication-refresh invalidation;
- old-generation fencing;
- deterministic REUSE / RESTORE / CREATE / ROTATE / RETIRE / RECOVERY decisions.

The exact user-facing recovery choreography remains UX-07.

